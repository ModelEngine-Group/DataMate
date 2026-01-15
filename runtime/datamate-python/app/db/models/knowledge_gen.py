"""
Tables of RAG Management Module
"""
import uuid
from sqlalchemy import Column, String, TIMESTAMP, Text, Integer, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class RagKnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "t_rag_knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="知识库名称")
    type = Column(String(50), nullable=False, comment="知识库类型")
    description = Column(String(512), nullable=True, comment="知识库描述")
    embedding_model = Column(String(255), nullable=False, comment="嵌入模型")
    chat_model = Column(String(255), nullable=True, comment="聊天模型")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(),
                      comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

    def __repr__(self):
        return f"<RagKnowledgeBase(id={self.id}, name={self.name}, type={self.type})>"


class RagFile(Base):
    """知识库文件模型"""
    __tablename__ = "t_rag_file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    knowledge_base_id = Column(String(36), nullable=False, comment="知识库ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_id = Column(String(255), nullable=False, comment="文件ID")
    chunk_count = Column(Integer, nullable=True, comment="切片数")
    file_metadata = Column("metadata", JSON, nullable=True, comment="元数据")
    status = Column(String(50), nullable=True, comment="文件状态")
    err_msg = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(),
                      comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

