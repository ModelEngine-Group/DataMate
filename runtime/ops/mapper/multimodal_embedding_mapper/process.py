# -- encoding: utf-8 --
"""
Multimodal Embedding Mapper - Generates embeddings from images or videos using multimodal embedding API
and stores them in Milvus vector database.

Description:
    This operator reads image/video binary data and generates vector embeddings using
    a multimodal embedding model (e.g., DashScope multimodal-embedding-v1).
    The embedding is automatically stored in Milvus collection (named by dataset_id).

Create: 2026/03/02
"""
import base64
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import httpx

from loguru import logger
from datamate.core.base_op import Mapper

# Milvus imports
from pymilvus import (
    MilvusClient,
    DataType,
    AnnSearchRequest,
)


class MultimodalEmbeddingMapper(Mapper):
    """
    多模态向量嵌入算子
    
    将图片或视频转换为向量嵌入，支持多模态嵌入模型（如阿里云百炼 multimodal-embedding-v1）。
    自动检测文件类型并选择对应的嵌入方法。
    嵌入向量自动存储到 Milvus 向量数据库中。
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
    
    # 已创建的 collection 缓存（避免重复检查）
    _created_collections = set()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 嵌入 API 配置
        self._api_url = kwargs.get("apiUrl", "").rstrip("/")
        self._api_key = kwargs.get("apiKey", "")
        self._model_name = kwargs.get("modelName", "multimodal-embedding-v1")
        self._text_prompt = kwargs.get("textPrompt", "")
        
        # Milvus 配置
        self._milvus_uri = kwargs.get("milvusUri", "http://milvus:19530")
        
        # 检测是否为阿里云百炼 API
        self._is_dashscope = "dashscope.aliyuncs.com" in self._api_url
        self._api_endpoint = self._detect_api_endpoint()
        
        # Milvus 客户端（延迟初始化）
        self._milvus_client = None
        
        logger.info(f"MultimodalEmbeddingMapper initialized - model: {self._model_name}, milvus: {self._milvus_uri}")
    
    def _detect_api_endpoint(self) -> str:
        """检测 API 提供商并设置对应的端点"""
        if self._is_dashscope:
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        return f"{self._api_url}/embeddings"
    
    def _get_milvus_client(self) -> MilvusClient:
        """获取 Milvus 客户端（单例模式）"""
        if self._milvus_client is None:
            self._milvus_client = MilvusClient(uri=self._milvus_uri)
            logger.info(f"Milvus client connected: {self._milvus_uri}")
        return self._milvus_client
    
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
            return {
                "model": self._model_name,
                "input": {"contents": contents},
                "parameters": {},
            }
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
        
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                self._api_endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            if "output" in data:
                embeddings = data["output"].get("embeddings", [])
                if embeddings:
                    return embeddings[0]["embedding"]
            
            if "data" in data and data["data"]:
                return data["data"][0]["embedding"]
            
            raise ValueError(f"Invalid response format: {data}")
    
    def _has_collection(self, collection_name: str) -> bool:
        """检查 collection 是否存在"""
        client = self._get_milvus_client()
        return client.has_collection(collection_name)
    
    def _create_collection(self, collection_name: str, dimension: int):
        """
        创建 Milvus collection
        
        参考 Java 版本 MilvusService.createCollection 实现
        包含字段: id, text, metadata, vector, sparse (BM25)
        """
        client = self._get_milvus_client()
        
        # 创建 schema
        schema = MilvusClient.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        
        # 添加字段
        schema.add_field(
            field_name="id",
            datatype=DataType.VARCHAR,
            max_length=36,
            is_primary=True,
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="metadata",
            datatype=DataType.JSON,
        )
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=dimension,
        )
        schema.add_field(
            field_name="sparse",
            datatype=DataType.SPARSE_FLOAT_VECTOR,
        )
        
        # 创建索引参数
        index_params = client.prepare_index_params()
        
        # 向量索引 (COSINE)
        index_params.add_index(
            field_name="vector",
            index_type="FLAT",
            metric_type="COSINE",
        )
        
        # 稀疏向量索引 (BM25)
        index_params.add_index(
            field_name="sparse",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params={"inverted_index_algo": "DAAT_MAXSCORE", "bm25_k1": 1.2, "bm25_b": 0.75},
        )
        
        # 创建 collection
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )
        
        logger.info(f"Created Milvus collection: {collection_name} with dimension {dimension}")
    
    def _ensure_collection_exists(self, collection_name: str, dimension: int):
        """确保 collection 存在，不存在则创建"""
        # 使用类级别缓存避免重复检查
        if collection_name in self._created_collections:
            return
        
        if not self._has_collection(collection_name):
            self._create_collection(collection_name, dimension)
        
        self._created_collections.add(collection_name)
    
    def _insert_to_milvus(
        self,
        collection_name: str,
        doc_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ):
        """
        将向量插入 Milvus
        
        参考 Java 版本 MilvusService.addAll 实现
        """
        client = self._get_milvus_client()
        
        # 构建插入数据
        data = [{
            "id": doc_id,
            "text": text,
            "metadata": metadata,
            "vector": embedding,
            # sparse 字段由 Milvus 自动生成 (BM25 Function)
        }]
        
        client.insert(
            collection_name=collection_name,
            data=data,
        )
        
        logger.info(f"Inserted vector to Milvus collection '{collection_name}': id={doc_id}")
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        
        :param sample: 输入的数据样本
            - data: 二进制数据
            - fileType: 文件类型
            - fileName: 文件名
            - fileId: 文件ID (可选)
            - dataset_id: 数据集ID，用于 Milvus collection 名称
            - ext_params: 扩展参数字典
        :return: 处理后的数据样本（新生成的变量存入 ext_params）
        """
        start = time.time()
        self.read_file_first(sample)
        
        file_name = sample.get(self.filename_key, "")
        file_type = sample.get(self.filetype_key, "")
        file_bytes = sample.get(self.data_key)
        file_id = sample.get("fileId", str(uuid.uuid4()))
        
        # dataset_id 从 sample 顶层获取（输入参数，保持原有使用方式）
        dataset_id = sample.get("dataset_id") or sample.get("datasetId")
        
        # 获取 ext_params（如果不存在则创建空字典）
        ext_params = sample.get("ext_params", {}) or {}
        
        if not file_bytes:
            logger.warning(f"MultimodalEmbeddingMapper: No binary data found for {file_name}")
            return sample
        
        try:
            # 转换为 base64 data URL 并获取文件类别
            data_url, category = self._bytes_to_data_url(file_bytes, file_type)
            
            if category is None:
                logger.warning(f"MultimodalEmbeddingMapper: Unsupported file type '{file_type}' for {file_name}")
                ext_params["embedding_error"] = f"Unsupported file type: {file_type}"
                sample["ext_params"] = ext_params
                return sample
            
            # 构建嵌入请求内容
            content = {category: data_url}
            if self._text_prompt:
                content["text"] = self._text_prompt
            
            # 获取嵌入向量
            embedding = self._embed([content])
            dimension = len(embedding)
            
            # 构建元数据
            text = f"[{'图片' if category == 'image' else '视频'}文件: {file_name}]"
            metadata = {
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                f"is_{category}": True,
            }
            
            # 将新生成的变量存入 ext_params（遵循算子开发规范）
            ext_params["embedding"] = embedding
            sample["text"] = text
            ext_params["embedding_dimension"] = dimension
            ext_params[f"is_{category}"] = True
            
            # 入库到 Milvus
            if dataset_id:
                collection_name = str(dataset_id)
                
                # 确保 collection 存在
                self._ensure_collection_exists(collection_name, dimension)
                
                # 插入向量
                doc_id = str(uuid.uuid4())
                self._insert_to_milvus(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    text=text,
                    embedding=embedding,
                    metadata=metadata,
                )
                
                ext_params["milvus_inserted"] = True
                ext_params["milvus_doc_id"] = doc_id
                ext_params["milvus_collection"] = collection_name
            else:
                logger.warning(f"MultimodalEmbeddingMapper: No dataset_id in sample, skipping Milvus insertion for {file_name}")
                ext_params["milvus_inserted"] = False
            
            logger.info(f"MultimodalEmbeddingMapper: {file_name} ({category}) - embedding dim={dimension}, milvus={ext_params.get('milvus_inserted')}, cost {time.time() - start:.3f}s")
            
        except Exception as e:
            logger.error(f"MultimodalEmbeddingMapper failed for {file_name}: {e}")
            ext_params["embedding_error"] = str(e)
            ext_params["milvus_inserted"] = False
        
        # 更新 sample 的 ext_params
        sample["ext_params"] = ext_params
        
        return sample
