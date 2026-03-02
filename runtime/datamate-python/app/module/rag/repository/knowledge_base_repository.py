"""
知识库仓储层

提供知识库数据访问操作
使用 SQLAlchemy 异步 session 进行数据库操作
"""
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.knowledge_gen import KnowledgeBase, RagType
from app.core.exception import BusinessError, ErrorCodes


class KnowledgeBaseRepository:
    """知识库仓储类

    对应 Java: com.datamate.rag.indexer.domain.repository.KnowledgeBaseRepository
    提供知识库的 CRUD 操作和查询功能
    """

    def __init__(self, db: AsyncSession):
        """初始化仓储

        Args:
            db: SQLAlchemy 异步 session
        """
        self.db = db

    async def create(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """创建知识库

        Args:
            knowledge_base: 知识库实体

        Returns:
            创建的知识库实体

        Raises:
            BusinessError: 知识库名称已存在
        """
        # 检查名称是否已存在
        existing = await self.get_by_name(knowledge_base.name)
        if existing:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_ALREADY_EXISTS)

        self.db.add(knowledge_base)
        await self.db.flush()
        return knowledge_base

    async def update(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """更新知识库

        Args:
            knowledge_base: 知识库实体（必须包含 id）

        Returns:
            更新后的知识库实体

        Raises:
            BusinessError: 知识库不存在
        """
        existing = await self.get_by_id(knowledge_base.id)
        if not existing:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 如果名称变更，检查新名称是否已存在
        if existing.name != knowledge_base.name:
            name_exists = await self.get_by_name(knowledge_base.name)
            if name_exists:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_ALREADY_EXISTS)

        # 更新字段
        existing.name = knowledge_base.name
        existing.description = knowledge_base.description

        await self.db.flush()
        return existing

    async def delete(self, knowledge_base_id: str) -> None:
        """删除知识库

        Args:
            knowledge_base_id: 知识库ID

        Raises:
            BusinessError: 知识库不存在
        """
        knowledge_base = await self.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        await self.db.delete(knowledge_base)
        await self.db.flush()

    async def get_by_id(self, knowledge_base_id: str) -> Optional[KnowledgeBase]:
        """根据 ID 获取知识库

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            知识库实体，不存在则返回 None
        """
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """根据名称获取知识库

        Args:
            name: 知识库名称

        Returns:
            知识库实体，不存在则返回 None
        """
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )
        return result.scalars().first()

    async def list(
        self,
        keyword: Optional[str] = None,
        rag_type: Optional[RagType] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[KnowledgeBase], int]:
        """分页查询知识库列表

        Args:
            keyword: 搜索关键词（模糊匹配名称或描述）
            rag_type: RAG 类型筛选
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (知识库列表, 总记录数)
        """
        # 构建查询条件
        conditions = []

        if keyword:
            conditions.append(
                or_(
                    KnowledgeBase.name.like(f"%{keyword}%"),
                    KnowledgeBase.description.like(f"%{keyword}%")
                )
            )

        if rag_type:
            conditions.append(KnowledgeBase.type == rag_type)

        # 构建查询
        query = select(KnowledgeBase)
        if conditions:
            query = query.where(and_(*conditions))

        # 查询总数
        count_query = select(func.count()).select_from(KnowledgeBase)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(KnowledgeBase.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def exists_by_name(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """检查知识库名称是否存在

        Args:
            name: 知识库名称
            exclude_id: 排除的知识库ID（用于更新时检查）

        Returns:
            True 表示名称已存在，False 表示名称可用
        """
        query = select(KnowledgeBase).where(KnowledgeBase.name == name)
        if exclude_id:
            query = query.where(KnowledgeBase.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def get_all_ids(self) -> List[str]:
        """获取所有知识库 ID

        Returns:
            知识库 ID 列表
        """
        result = await self.db.execute(
            select(KnowledgeBase.id).order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())
