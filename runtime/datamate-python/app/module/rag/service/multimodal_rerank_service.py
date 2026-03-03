"""
多模态重排序服务

支持文本、图片、视频的混合重排序
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
    content_type: Optional[str] = None  # "text", "image", "video"


class RerankResponse(BaseModel):
    """重排序响应"""
    results: List[RerankResult]


class MultimodalRerankService:
    """多模态重排序服务
    
    针对文本、图片、视频采用不同的重排序策略：
    - 文本：直接使用文本 rerank API
    - 图片/视频：生成文本描述后 rerank
    """
    
    def __init__(self, models_service: ModelsService):
        self.models_service = models_service
    
    async def rerank_multimodal(
        self,
        query: str,
        results: List[dict],
        rerank_model_id: str,
        top_k: int = 5,
        vision_model_id: Optional[str] = None,  # 用于生成图片描述的模型
    ) -> RerankResponse:
        """多模态重排序
        
        Args:
            query: 查询文本
            results: 检索结果（包含文本、图片、视频）
            rerank_model_id: 重排序模型ID
            top_k: 返回前K个结果
            vision_model_id: 视觉模型ID（用于生成图片/视频描述）
            
        Returns:
            RerankResponse: 重排序结果
        """
        if not results:
            return RerankResponse(results=[])
        
        # 1. 分类结果：文本、图片、视频
        text_results = []
        image_results = []
        video_results = []
        
        for idx, result in enumerate(results):
            metadata = result.get("entity", {}).get("metadata", {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            is_image = metadata.get("is_image") == "true"
            is_video = metadata.get("is_video") == "true"
            
            if is_video:
                video_results.append((idx, result))
            elif is_image:
                image_results.append((idx, result))
            else:
                text_results.append((idx, result))
        
        logger.info(f"分类结果: 文本={len(text_results)}, 图片={len(image_results)}, 视频={len(video_results)}")
        
        # 2. 为图片/视频生成文本描述
        enhanced_documents = []
        
        # 处理文本结果
        for idx, result in text_results:
            text = result.get("entity", {}).get("text", "")
            enhanced_documents.append({
                "index": idx,
                "document": text,
                "content_type": "text"
            })
        
        # 处理图片结果
        if image_results and vision_model_id:
            image_descriptions = await self._generate_image_descriptions(
                image_results, vision_model_id
            )
            for idx, result in image_results:
                description = image_descriptions.get(idx, "图片内容")
                enhanced_documents.append({
                    "index": idx,
                    "document": description,
                    "content_type": "image"
                })
        elif image_results:
            # 没有视觉模型，使用元数据
            for idx, result in image_results:
                text = result.get("entity", {}).get("text", "")
                enhanced_documents.append({
                    "index": idx,
                    "document": text,
                    "content_type": "image"
                })
        
        # 处理视频结果
        if video_results and vision_model_id:
            video_descriptions = await self._generate_video_descriptions(
                video_results, vision_model_id
            )
            for idx, result in video_results:
                description = video_descriptions.get(idx, "视频内容")
                enhanced_documents.append({
                    "index": idx,
                    "document": description,
                    "content_type": "video"
                })
        elif video_results:
            for idx, result in image_results:
                text = result.get("entity", {}).get("text", "")
                enhanced_documents.append({
                    "index": idx,
                    "document": text,
                    "content_type": "video"
                })
        
        # 3. 调用文本 rerank API
        model_config = await self.models_service.get_model_detail(rerank_model_id)
        if not model_config:
            raise BusinessError(ErrorCodes.SYSTEM_MODEL_NOT_FOUND)
        
        documents = [doc["document"] for doc in enhanced_documents]
        
        rerank_response = await self._call_rerank_api(
            query, documents, model_config, top_k
        )
        
        # 4. 合并结果
        final_results = []
        for rerank_item in rerank_response.results:
            doc_info = enhanced_documents[rerank_item.index]
            final_results.append(RerankResult(
                index=doc_info["index"],
                relevance_score=rerank_item.relevance_score,
                document=doc_info["document"],
                content_type=doc_info["content_type"]
            ))
        
        return RerankResponse(results=final_results[:top_k])
    
    async def _generate_image_descriptions(
        self,
        image_results: List[tuple],
        vision_model_id: str,
    ) -> Dict[int, str]:
        """为图片生成文本描述
        
        Args:
            image_results: 图片结果列表 [(index, result), ...]
            vision_model_id: 视觉模型ID
            
        Returns:
            {index: description} 字典
        """
        descriptions = {}
        
        try:
            vision_model = await self.models_service.get_model_detail(vision_model_id)
            if not vision_model:
                logger.warning(f"视觉模型 {vision_model_id} 不存在")
                return descriptions
            
            for idx, result in image_results:
                try:
                    metadata = result.get("entity", {}).get("metadata", {})
                    if isinstance(metadata, str):
                        import json
                        metadata = json.loads(metadata)
                    
                    # 获取图片 URL 或 base64
                    dataset_id = metadata.get("dataset_id")
                    file_id = metadata.get("original_file_id")
                    
                    if not dataset_id or not file_id:
                        descriptions[idx] = "图片内容"
                        continue
                    
                    # 调用视觉模型生成描述
                    description = await self._call_vision_model(
                        dataset_id, file_id, vision_model
                    )
                    descriptions[idx] = description
                    
                except Exception as e:
                    logger.error(f"生成图片描述失败 (index={idx}): {str(e)}")
                    descriptions[idx] = "图片内容"
        
        except Exception as e:
            logger.error(f"批量生成图片描述失败: {str(e)}")
        
        return descriptions
    
    async def _generate_video_descriptions(
        self,
        video_results: List[tuple],
        vision_model_id: str,
    ) -> Dict[int, str]:
        """为视频生成文本描述
        
        Args:
            video_results: 视频结果列表 [(index, result), ...]
            vision_model_id: 视觉模型ID
            
        Returns:
            {index: description} 字典
        """
        descriptions = {}
        
        try:
            vision_model = await self.models_service.get_model_detail(vision_model_id)
            if not vision_model:
                logger.warning(f"视觉模型 {vision_model_id} 不存在")
                return descriptions
            
            for idx, result in video_results:
                try:
                    metadata = result.get("entity", {}).get("metadata", {})
                    if isinstance(metadata, str):
                        import json
                        metadata = json.loads(metadata)
                    
                    # 获取视频信息
                    dataset_id = metadata.get("dataset_id")
                    file_id = metadata.get("original_file_id")
                    
                    if not dataset_id or not file_id:
                        descriptions[idx] = "视频内容"
                        continue
                    
                    # 调用视觉模型生成描述（提取关键帧）
                    description = await self._call_vision_model_for_video(
                        dataset_id, file_id, vision_model
                    )
                    descriptions[idx] = description
                    
                except Exception as e:
                    logger.error(f"生成视频描述失败 (index={idx}): {str(e)}")
                    descriptions[idx] = "视频内容"
        
        except Exception as e:
            logger.error(f"批量生成视频描述失败: {str(e)}")
        
        return descriptions
    
    async def _call_vision_model(
        self,
        dataset_id: str,
        file_id: str,
        vision_model: Models,
    ) -> str:
        """调用视觉模型生成图片描述
        
        Args:
            dataset_id: 数据集ID
            file_id: 文件ID
            vision_model: 视觉模型配置
            
        Returns:
            图片描述文本
        """
        # 构造图片 URL
        image_url = f"/api/data-management/datasets/{dataset_id}/files/{file_id}/download"
        
        # 调用多模态模型 API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{vision_model.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {vision_model.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": vision_model.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "请用简短的文字描述这张图片的内容（用于搜索排序）："
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 100,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            description = data.get("choices", [{}])[0].get("message", {}).get("content", "图片内容")
            return description
    
    async def _call_vision_model_for_video(
        self,
        dataset_id: str,
        file_id: str,
        vision_model: Models,
    ) -> str:
        """调用视觉模型生成视频描述（基于关键帧）
        
        Args:
            dataset_id: 数据集ID
            file_id: 文件ID
            vision_model: 视觉模型配置
            
        Returns:
            视频描述文本
        """
        # TODO: 实现视频关键帧提取和描述生成
        # 1. 提取视频关键帧（如每5秒一帧）
        # 2. 为每个关键帧生成描述
        # 3. 合并所有描述
        
        # 简化实现：返回视频元数据
        return "视频内容"
    
    async def _call_rerank_api(
        self,
        query: str,
        documents: List[str],
        model_config: Models,
        top_k: int,
    ) -> RerankResponse:
        """调用 Rerank API
        
        Args:
            query: 查询文本
            documents: 文档列表
            model_config: 模型配置
            top_k: 返回数量
            
        Returns:
            RerankResponse
        """
        provider = model_config.provider.lower()
        
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
