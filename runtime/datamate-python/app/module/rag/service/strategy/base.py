"""
策略模式 - 知识库策略基类

定义知识库检索和处理的抽象接口，支持不同类型的知识库（向量、知识图谱等）。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class KnowledgeBaseStrategy(ABC):
    """知识库策略抽象基类

    所有知识库策略（向量、知识图谱等）必须实现此接口。

    接口设计原则：
    - query(): 直接获取数据，不涉及相似度计算，返回值格式不统一
    - search(): 基于输入文本的相似度检索，返回值必须统一为 UnifiedSearchResult
    - process_file(): 处理单个文件，不同策略有不同的处理逻辑
    """

    def __init__(self, db: AsyncSession):
        """初始化策略

        Args:
            db: 数据库异步 session
        """
        self.db = db

    @abstractmethod
    async def query(
        self,
        knowledge_base_id: str,
        **kwargs
    ) -> Any:
        """直接查询知识库数据（不涉及相似度计算）

        不同知识库类型的返回格式可以不同：
        - 向量知识库：返回 PagedResponse[RagChunkResp]（分页分块列表）
        - 知识图谱：返回图谱数据（格式由 LightRAG 定义）

        Args:
            knowledge_base_id: 知识库 ID
            **kwargs: 额外参数（如 rag_file_id, paging_query 等）

        Returns:
            查询结果（格式由具体策略决定）
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_text: str,
        knowledge_base_ids: List[str],
        top_k: int = 10,
        threshold: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """基于输入文本的相似度检索

        所有知识库类型必须返回统一格式：UnifiedSearchResult

        Args:
            query_text: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            top_k: 返回结果数量
            threshold: 相似度阈值（可选）
            **kwargs: 额外参数

        Returns:
            统一格式的检索结果列表，每个元素包含：
            - id: 结果 ID
            - text: 文本内容
            - score: 相似度分数
            - metadata: 元数据字典
            - resultType: 结果类型（"vector" 或 "graph"）
            - knowledgeBaseId: 知识库 ID
            - knowledgeBaseName: 知识库名称
        """
        pass

    @abstractmethod
    async def process_file(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        **kwargs
    ) -> None:
        """处理单个文件

        不同知识库类型有不同的处理逻辑：
        - 向量知识库：文档分块 -> 向量化 -> 存储到 Milvus
        - 知识图谱：文档分块 -> 构建知识图谱 -> 存储到 LightRAG

        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            **kwargs: 额外参数（如 process_type, chunk_size 等）

        Raises:
            BusinessError: 处理失败时抛出
        """
        pass
