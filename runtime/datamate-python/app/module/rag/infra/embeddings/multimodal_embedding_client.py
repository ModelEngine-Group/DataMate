"""
多模态嵌入模型客户端

支持不支持 OpenAI 兼容模式的多模态 embedding 模型（如 qwen3-vl-embedding）。
参考 Java 版本 MultimodalEmbeddingClient 实现。
"""

import base64
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import numpy as np
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


def _normalize_vector(vector: List[float]) -> List[float]:
    """L2 归一化向量

    确保向量长度为 1，使 COSINE similarity 在相同向量时返回 1.0

    Args:
        vector: 原始向量

    Returns:
        归一化后的向量
    """
    arr = np.array(vector, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return arr.tolist()
    return (arr / norm).tolist()


class MultimodalEmbeddingClient(Embeddings):
    """多模态嵌入模型客户端，支持文本、图片和视频的嵌入。

    用于处理不支持 OpenAI 兼容模式的多模态 embedding 模型（如 qwen3-vl-embedding）。
    参考 Java 版本 MultimodalEmbeddingClient 实现。
    """

    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: str,
        **kwargs: Any,
    ):
        """初始化客户端

        Args:
            model_name: 模型名称（如 qwen3-vl-embedding）
            base_url: API 基础 URL
            api_key: API 密钥
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.is_dashscope = "dashscope.aliyuncs.com" in base_url
        self.api_endpoint = self._detect_api_endpoint()
        logger.info(
            f"MultimodalEmbeddingClient initialized - model: {model_name}, endpoint: {self.api_endpoint}"
        )

    def _detect_api_endpoint(self) -> str:
        """检测 API 端点"""
        if self.is_dashscope:
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        return f"{self.base_url}/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        return [self.embed_text(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            嵌入向量
        """
        return self.embed_text(text)

    def embed_text(self, text: str) -> List[float]:
        """嵌入文本

        Args:
            text: 文本内容

        Returns:
            嵌入向量
        """
        content = {"text": text}
        return self._embed([content])

    def embed_image(self, image_url: str, text: Optional[str] = None) -> List[float]:
        """嵌入图片

        Args:
            image_url: 图片 URL 或本地路径
            text: 可选的文本描述

        Returns:
            嵌入向量
        """
        logger.info(
            f"embed_image called - image_url length: {len(image_url) if image_url else 0}, text: '{text}'"
        )

        content: Dict[str, Any] = {}
        converted_url = self._convert_to_data_url(image_url, "image")
        content["image"] = converted_url

        logger.info(f"Image converted, final data URL length: {len(converted_url)}")

        if text:
            content["text"] = text
            logger.info(f"Added text to embedding request: '{text}'")

        result = self._embed([content])
        logger.info(f"Embedding result dimension: {len(result)}")
        return result

    def embed_video(self, video_url: str, text: Optional[str] = None) -> List[float]:
        """嵌入视频

        Args:
            video_url: 视频 URL 或本地路径
            text: 可选的文本描述

        Returns:
            嵌入向量
        """
        logger.info(
            f"embed_video called - video_url length: {len(video_url) if video_url else 0}, text: '{text}'"
        )

        content: Dict[str, Any] = {}
        converted_url = self._convert_to_data_url(video_url, "video")
        content["video"] = converted_url

        logger.info(f"Video converted, final data URL length: {len(converted_url)}")

        if text:
            content["text"] = text
            logger.info(f"Added text to embedding request: '{text}'")

        result = self._embed([content])
        logger.info(f"Video embedding result dimension: {len(result)}")
        return result

    def _convert_to_data_url(self, file_input: str, file_type: str) -> str:
        """将文件路径或URL转换为Data URL格式

        Args:
            file_input: 文件路径或URL
            file_type: 文件类型 (image/video)

        Returns:
            Data URL 或原始 URL
        """
        if not file_input:
            raise ValueError(f"{file_type} input cannot be null or empty")

        # 如果已经是 data URL 或 http URL，直接返回
        if (
            file_input.startswith("data:")
            or file_input.startswith("http://")
            or file_input.startswith("https://")
        ):
            logger.debug(f"Using {file_type} URL directly, length: {len(file_input)}")
            return file_input

        # 本地文件路径
        file_path = Path(file_input)
        if not file_path.exists():
            raise RuntimeError(f"File not found: {file_input}")

        try:
            mime_type = self._detect_mime_type(file_path, file_type)
            file_bytes = file_path.read_bytes()
            base64_str = base64.b64encode(file_bytes).decode("utf-8")
            data_url = f"data:{mime_type};base64,{base64_str}"
            logger.debug(
                f"Converted local file to data URL, file size: {len(file_bytes)} bytes"
            )
            return data_url
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {file_input}") from e

    def _detect_mime_type(self, file_path: Path, file_type: str) -> str:
        """根据文件扩展名检测 MIME 类型

        Args:
            file_path: 文件路径
            file_type: 文件类型 (image/video)

        Returns:
            MIME 类型字符串
        """
        file_name = file_path.name.lower()

        if file_type == "video":
            video_types = {
                ".mp4": "video/mp4",
                ".avi": "video/x-msvideo",
                ".mov": "video/quicktime",
                ".mkv": "video/x-matroska",
                ".wmv": "video/x-ms-wmv",
                ".flv": "video/x-flv",
                ".webm": "video/webm",
                ".m4v": "video/x-m4v",
                ".3gp": "video/3gpp",
            }
            for ext, mime in video_types.items():
                if file_name.endswith(ext):
                    return mime
            return "video/mp4"
        else:
            # Image types
            image_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
                ".tiff": "image/tiff",
                ".tif": "image/tiff",
            }
            for ext, mime in image_types.items():
                if file_name.endswith(ext):
                    return mime
            return "image/jpeg"

    def _embed(self, contents: List[Dict[str, Any]]) -> List[float]:
        """调用嵌入 API

        Args:
            contents: 内容列表，每个元素是包含 text/image/video 的字典

        Returns:
            嵌入向量
        """
        request_body = self._build_request_body(contents)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            logger.debug(
                f"Sending embedding request to: {self.api_endpoint}, contents size: {len(contents)}"
            )

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.api_endpoint,
                    headers=headers,
                    json=request_body,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Embedding API call failed with status: {response.status_code}, body: {response.text}"
                    )
                    raise RuntimeError(
                        f"Embedding API call failed: {response.status_code}"
                    )

                response_json = response.json()
                logger.debug("Received embedding response, checking format...")

                # 尝试阿里云百炼格式: output.embeddings[0].embedding
                if "output" in response_json:
                    embeddings_array = response_json["output"].get("embeddings", [])
                    if embeddings_array and len(embeddings_array) > 0:
                        embedding = embeddings_array[0].get("embedding", [])
                        normalized = _normalize_vector(embedding)
                        logger.info(
                            f"Successfully extracted embedding from DashScope format, dimension: {len(embedding)}, normalized"
                        )
                        return normalized

                # 尝试通用格式: data[0].embedding
                if "data" in response_json:
                    data_array = response_json["data"]
                    if isinstance(data_array, list) and len(data_array) > 0:
                        embedding = data_array[0].get("embedding", [])
                        normalized = _normalize_vector(embedding)
                        logger.info(
                            f"Successfully extracted embedding from generic format, dimension: {len(embedding)}, normalized"
                        )
                        return normalized

                logger.error(f"Invalid response format: {response_json}")
                raise RuntimeError("Invalid response format: missing embedding data")

        except Exception as e:
            logger.error(f"Embedding API call failed: {str(e)}")
            raise RuntimeError(f"Embedding API call failed: {str(e)}") from e

    def _build_request_body(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建请求体

        Args:
            contents: 内容列表

        Returns:
            请求体字典
        """
        request_body: Dict[str, Any] = {"model": self.model_name}

        if self.is_dashscope:
            request_body["input"] = {"contents": contents}
            request_body["parameters"] = {}
        else:
            request_body["input"] = contents

        return request_body

    def check_health(self) -> bool:
        """健康检查

        Returns:
            是否健康
        """
        try:
            self.embed_text("health check")
            logger.info(
                f"Multimodal embedding model health check passed: {self.model_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Multimodal embedding model health check failed: {str(e)}")
            return False
