# -- encoding: utf-8 -*-
"""
Multimodal Embedding Mapper - Generates embeddings from images or videos using multimodal embedding API.

Description:
    This operator reads image/video binary data and generates vector embeddings using
    a multimodal embedding model (e.g., DashScope multimodal-embedding-v1).
    The embedding is stored in sample['embedding'] for downstream processing.

Create: 2026/03/02
"""
import base64
import time
from typing import Dict, Any, List, Optional
import httpx

from loguru import logger
from datamate.core.base_op import Mapper


class MultimodalEmbeddingMapper(Mapper):
    """
    多模态向量嵌入算子
    
    将图片或视频转换为向量嵌入，支持多模态嵌入模型（如阿里云百炼 multimodal-embedding-v1）。
    自动检测文件类型并选择对应的嵌入方法。
    嵌入向量存储在 sample['embedding'] 中，元数据存储在 sample['text'] 中。
    """
    
    # 支持的图片扩展名
    IMAGE_EXTENSIONS = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
    }
    
    # 支持的视频扩展名
    VIDEO_EXTENSIONS = {
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mkv': 'video/x-matroska',
        'wmv': 'video/x-ms-wmv',
        'flv': 'video/x-flv',
        'webm': 'video/webm',
        'm4v': 'video/x-m4v',
        '3gp': 'video/3gpp',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # API 配置 - 参数名称与 metadata.yml 保持一致
        self._api_url = kwargs.get("apiUrl", "").rstrip("/")
        self._api_key = kwargs.get("apiKey", "")
        self._model_name = kwargs.get("modelName", "multimodal-embedding-v1")
        self._text_prompt = kwargs.get("textPrompt", "")
        
        # 检测是否为阿里云百炼 API
        self._is_dashscope = "dashscope.aliyuncs.com" in self._api_url
        self._api_endpoint = self._detect_api_endpoint()
        
        logger.info(f"MultimodalEmbeddingMapper initialized - model: {self._model_name}, endpoint: {self._api_endpoint}")
    
    def _detect_api_endpoint(self) -> str:
        """检测 API 提供商并设置对应的端点"""
        if self._is_dashscope:
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        return f"{self._api_url}/embeddings"
    
    def _get_file_category(self, file_type: str) -> tuple[Optional[str], str]:
        """
        根据文件扩展名获取文件类别和 MIME 类型
        :return: (category, mime_type) - category 为 'image', 'video' 或 None
        """
        ext = file_type.lower().lstrip('.')
        
        if ext in self.IMAGE_EXTENSIONS:
            return 'image', self.IMAGE_EXTENSIONS[ext]
        
        if ext in self.VIDEO_EXTENSIONS:
            return 'video', self.VIDEO_EXTENSIONS[ext]
        
        return None, 'application/octet-stream'
    
    def _bytes_to_data_url(self, data: bytes, file_type: str) -> tuple[str, Optional[str]]:
        """
        将二进制数据转换为 base64 data URL
        :return: (data_url, category)
        """
        category, mime_type = self._get_file_category(file_type)
        base64_data = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}", category
    
    def _build_request_body(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建请求体"""
        if self._is_dashscope:
            # 阿里云百炼 HTTP API 格式: input.contents
            return {
                "model": self._model_name,
                "input": {"contents": contents},
                "parameters": {},
            }
        # 通用格式: input 数组
        return {
            "model": self._model_name,
            "input": contents,
        }
    
    def _embed(self, contents: List[Dict[str, Any]]) -> List[float]:
        """调用嵌入 API 获取向量"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload = self._build_request_body(contents)
        
        # 视频处理可能需要更长时间
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                self._api_endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # 尝试阿里云百炼格式: output.embeddings[0].embedding
            if "output" in data:
                embeddings = data["output"].get("embeddings", [])
                if embeddings:
                    return embeddings[0]["embedding"]
            
            # 通用格式: data[0].embedding
            if "data" in data and data["data"]:
                return data["data"][0]["embedding"]
            
            raise ValueError(f"Invalid response format: {data}")
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        
        :param sample: 输入的数据样本，包含 data (二进制数据), fileType, fileName 等
        :return: 处理后的数据样本，包含 embedding (向量), text (元数据描述)
        """
        start = time.time()
        self.read_file_first(sample)
        
        file_name = sample.get(self.filename_key, "")
        file_type = sample.get(self.filetype_key, "")
        file_bytes = sample.get(self.data_key)
        
        if not file_bytes:
            logger.warning(f"MultimodalEmbeddingMapper: No binary data found for {file_name}")
            return sample
        
        try:
            # 转换为 base64 data URL 并获取文件类别
            data_url, category = self._bytes_to_data_url(file_bytes, file_type)
            
            if category is None:
                logger.warning(f"MultimodalEmbeddingMapper: Unsupported file type '{file_type}' for {file_name}")
                sample['embedding_error'] = f"Unsupported file type: {file_type}"
                return sample
            
            # 构建嵌入请求内容
            content = {category: data_url}
            if self._text_prompt:
                content["text"] = self._text_prompt
            
            # 获取嵌入向量
            embedding = self._embed([content])
            
            # 存储结果
            sample['embedding'] = embedding
            sample['text'] = f"[{'图片' if category == 'image' else '视频'}文件: {file_name}]"
            sample['embedding_dimension'] = len(embedding)
            sample[f'is_{category}'] = True
            
            logger.info(f"MultimodalEmbeddingMapper: {file_name} ({category}) - generated embedding with dimension {len(embedding)}, cost {time.time() - start:.3f}s")
            
        except Exception as e:
            logger.error(f"MultimodalEmbeddingMapper failed for {file_name}: {e}")
            sample['embedding_error'] = str(e)
        
        return sample
