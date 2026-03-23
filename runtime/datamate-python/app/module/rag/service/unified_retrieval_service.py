"""
统一检索服务

提供知识库内容的统一检索接口，支持多种知识库类型(向量、知识图谱等)。
使用策略模式实现不同知识库类型的检索逻辑。
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.db.models.knowledge_gen import KnowledgeBase
from app.module.rag.repository import KnowledgeBaseRepository
from app.module.rag.schema.request import PagingQuery, ChunkFilterQuery, RetrieveReq
from app.module.rag.schema.response import PagedResponse
from .strategy import KnowledgeBaseStrategyFactory

logger = logging.getLogger(__name__)


class UnifiedRetrievalService:
    """统一检索服务

    揯供统一的检索接口,根据知识库类型自动选择策略。
    """

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)

    async def query(
        self,
        knowledge_base_id: str,
        **kwargs
    ) -> Any:
        """直接查询知识库数据(不涉及相似度计算)

        Args:
            knowledge_base_id: 知识库 ID
            **kwargs: 额外参数
                - 向量知识库: rag_file_id, paging_query
                - 知识图谱: node_label

        Returns:
            查询结果(格式由具体知识库类型决定)
        """
        kb = await self._get_knowledge_base(knowledge_base_id)
        strategy = KnowledgeBaseStrategyFactory.create_strategy(kb.type, self.db)
        return await strategy.query(knowledge_base_id, **kwargs)

    async def search(
        self,
        request: RetrieveReq
    ) -> List[Dict[str, Any]]:
        """基于输入文本的相似度检索

        Args:
            request: 检索请求

        Returns:
            统一格式的检索结果列表(UnifiedSearchResult)
        """
        if not request.knowledge_base_ids:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                "至少需要一个知识库 ID"
            )

        kb = await self._get_knowledge_base(request.knowledge_base_ids[0])
        strategy = KnowledgeBaseStrategyFactory.create_strategy(kb.type, self.db)

        return await strategy.search(
            query_text=request.query,
            knowledge_base_ids=request.knowledge_base_ids,
            top_k=request.top_k,
            threshold=request.threshold,
        )

    async def get_chunks(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        query: ChunkFilterQuery,
    ) -> PagedResponse:
        """获取指定 RAG 文件的分块列表(仅向量知识库)

        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            query: 分页和过滤参数

        Returns:
            分块列表(分页)
        """
        return await self.query(
            knowledge_base_id,
            rag_file_id=rag_file_id,
            chunk_filter_query=query,
        )

    async def _get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        """获取知识库实体

        Args:
            knowledge_base_id: 知识库 ID

        Returns:
            知识库实体

        Raises:
            BusinessError: 知识库不存在
        """
        kb = await self.kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
        return kb
