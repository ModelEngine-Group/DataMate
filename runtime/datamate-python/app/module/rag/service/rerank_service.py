"""
重排序服务

支持多种重排序模型提供商：
- Cohere Rerank API
- Jina Rerank API
- BGE Rerank (HuggingFace)
- 自定义 OpenAI-compatible APIs
"""
import httpx
from typing import List, Dict, Optional, Any
from app.core.logging import get_logger
from app.core.exception import BusinessError, ErrorCodes
from app.module.system.service.models_service import ModelsService

from app.db.models.models import Models

from pydantic import BaseModel

logger = get_logger(__name__)


class RerankResult(BaseModel):
    """重排序结果"""
    index: int
    relevance_score: float
    document: Optional[str] = None


class RerankResponse(BaseModel):
    """重排序响应"""
    results: List[RerankResult]


class RerankService:
    """重排序服务
    
    根据模型配置调用对应的重排序 API
    """
    
    def __init__(self, models_service: ModelsService):
        self.models_service = models_service
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        model_id: str,
        top_k: int = 5,
    ) -> RerankResponse:
        """执行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            model_id: 重排序模型ID
            top_k: 返回前K个结果
            
        Returns:
            RerankResponse: 重排序结果
            
        Raises:
            BusinessError: 如果模型不存在或不支持重排序
        """
        model_config = await self.models_service.get_model_detail(model_id)
        
        if not model_config:
            raise BusinessError(ErrorCodes.SYSTEM_MODEL_NOT_FOUND)
        
        if model_config.type != "RERANK":
            raise BusinessError(
                ErrorCodes.BAD_REQUEST,
                context=f"Model {model_id} is not a rerank model"
            )
        
        provider = model_config.provider.lower()
        
        try:
            if provider == "cohere":
                return await self._rerank_cohere(
                    query, documents, model_config, top_k
                )
            elif provider == "jina":
                return await self._rerank_jina(
                    query, documents, model_config, top_k
                )
            elif provider in ["bge", "huggingface"]:
                return await self._rerank_bge(
                    query, documents, model_config, top_k
                )
            else:
                return await self._rerank_custom(
                    query, documents, model_config, top_k
                )
        except Exception as e:
            logger.error(f"Rerank failed: {str(e)}")
            raise BusinessError(
                ErrorCodes.OPERATION_FAILED,
                context=f"Rerank operation failed: {str(e)}"
            )
    
    async def _rerank_cohere(
        self,
        query: str,
        documents: List[str],
        model_config: Models,
        top_k: int,
    ) -> RerankResponse:
        """Cohere Rerank API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_config.base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {model_config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_config.model_name,
                    "query": query,
                    "documents": documents,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = [
                RerankResult(
                    index=r["index"],
                    relevance_score=r["relevance_score"],
                    document=documents[r["index"]] if r["index"] < len(documents) else None
                )
                for r in data.get("results", [])
            ]
            
            return RerankResponse(results=results[:top_k])
    
    async def _rerank_jina(
        self,
        query: str,
        documents: List[str],
        model_config: Models,
        top_k: int,
    ) -> RerankResponse:
        """Jina Rerank API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_config.base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {model_config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_config.model_name,
                    "query": query,
                    "documents": documents,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = [
                RerankResult(
                    index=r["index"],
                    relevance_score=r["relevance_score"],
                    document=documents[r["index"]] if r["index"] < len(documents) else None
                )
                for r in data.get("results", [])
            ]
            
            return RerankResponse(results=results[:top_k])
    
    async def _rerank_bge(
        self,
        query: str,
        documents: List[str],
        model_config: Models,
        top_k: int,
    ) -> RerankResponse:
        """BGE Rerank (HuggingFace / TEI)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_config.base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {model_config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_config.model_name,
                    "query": query,
                    "documents": documents,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = [
                RerankResult(
                    index=r["index"],
                    relevance_score=r["relevance_score"],
                    document=documents[r["index"]] if r["index"] < len(documents) else None
                )
                for r in data.get("results", [])
            ]
            
            return RerankResponse(results=results[:top_k])
    
    async def _rerank_custom(
        self,
        query: str,
        documents: List[str],
        model_config: Models,
        top_k: int,
    ) -> RerankResponse:
        """自定义 OpenAI-compatible Rerank API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_config.base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {model_config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_config.model_name,
                    "query": query,
                    "documents": documents,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = [
                RerankResult(
                    index=r["index"],
                    relevance_score=r["relevance_score"],
                    document=documents[r["index"]] if r["index"] < len(documents) else None
                )
                for r in data.get("results", [])
            ]
            
            return RerankResponse(results=results[:top_k])
