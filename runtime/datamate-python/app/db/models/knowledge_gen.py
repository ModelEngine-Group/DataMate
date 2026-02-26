"""
知识库（RAG）相关 ORM 模型

表: t_rag_knowledge_base, t_rag_file
与 Java 实体保持一致。
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, JSON
from app.db.models.base_entity import BaseEntity


class RagType(str, Enum):
    """RAG 类型枚举

    对应 Java: com.datamate.rag.indexer.interfaces.dto.RagType
    """
    DOCUMENT = "DOCUMENT"  # 文档型 RAG（向量检索）
    GRAPH = "GRAPH"        # 知识图谱型 RAG（LightRAG）


class FileStatus(str, Enum):
    """文件状态枚举

    对应 Java: com.datamate.rag.indexer.domain.model.FileStatus
    """
    UNPROCESSED = "UNPROCESSED"        # 未处理
    PROCESSING = "PROCESSING"          # 处理中
    PROCESSED = "PROCESSED"            # 已处理
    PROCESS_FAILED = "PROCESS_FAILED"  # 处理失败


class KnowledgeBase(BaseEntity):
    """知识库实体

    对应 Java: com.datamate.rag.indexer.domain.model.KnowledgeBase
    表名: t_rag_knowledge_base
    """
    __tablename__ = "t_rag_knowledge_base"
    __ignore_data_scope__ = True

    id = Column(String(36), primary_key=True, comment="知识库ID")
    name = Column(String(255), nullable=False, unique=True, comment="知识库名称")
    description = Column(String(512), nullable=True, comment="知识库描述")
    type = Column(
        String(50),
        nullable=False,
        default=RagType.DOCUMENT,
        comment="RAG类型",
    )
    embedding_model = Column(String(255), nullable=False, comment="嵌入模型ID")
    chat_model = Column(String(255), nullable=True, comment="聊天模型ID")

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name}, type={self.type})>"


class RagFile(BaseEntity):
    """RAG 文件实体

    对应 Java: com.datamate.rag.indexer.domain.model.RagFile
    表名: t_rag_file
    """
    __tablename__ = "t_rag_file"
    __ignore_data_scope__ = True

    id = Column(String(36), primary_key=True, comment="RAG文件ID")
    knowledge_base_id = Column(String(36), nullable=False, index=True, comment="知识库ID")
    file_name = Column(String(512), nullable=False, comment="文件名")
    file_id = Column(String(36), nullable=False, comment="原始文件ID")
    chunk_count = Column(Integer, nullable=True, comment="分块数量")
    file_metadata = Column("metadata", JSON, nullable=True, comment="元数据（JSON格式）")
    status = Column(
        String(50),
        nullable=False,
        default=FileStatus.UNPROCESSED,
        comment="处理状态",
    )
    err_msg = Column(String(2048), nullable=True, comment="错误信息")
    progress = Column(Integer, default=0, nullable=False, comment="处理进度(0-100)")

    def __repr__(self):
        return f"<RagFile(id={self.id}, file_name={self.file_name}, status={self.status})>"
