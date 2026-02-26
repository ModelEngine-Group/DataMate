"""
RAG 模块非 ORM 实体

RagChunk 为 Milvus 中存储的文档分块 DTO，非数据库表。
ORM 实体 KnowledgeBase、RagFile 已移至 app.db.models.knowledge_gen。
"""
# noqa: D104 (RagChunk 是领域模型，不是 DB 表)


class RagChunk:
    """RAG 分块模型

    对应 Java: com.datamate.rag.indexer.domain.model.RagChunk
    注意：这不是数据库实体，而是 Milvus 中存储的文档分块
    """

    def __init__(
        self,
        chunk_id: str,
        rag_file_id: str,
        text: str,
        metadata: dict,
        vector: list[float] = None,
        sparse_vector: dict[int, float] = None
    ):
        """初始化文档分块

        Args:
            chunk_id: 分块ID
            rag_file_id: 关联的 RAG 文件 ID
            text: 分块文本内容
            metadata: 元数据（包含文件信息、分块索引等）
            vector: 密集向量（嵌入向量）
            sparse_vector: 稀疏向量（BM25 向量）
        """
        self.chunk_id = chunk_id
        self.rag_file_id = rag_file_id
        self.text = text
        self.metadata = metadata
        self.vector = vector
        self.sparse_vector = sparse_vector

    def to_dict(self) -> dict:
        """转换为字典格式（用于 Milvus 插入）

        Returns:
            包含所有字段的字典
        """
        return {
            "id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "vector": self.vector,
            "sparse": self.sparse_vector or {}
        }

    def __repr__(self):
        return f"<RagChunk(id={self.chunk_id}, text={self.text[:50]}...)>"
