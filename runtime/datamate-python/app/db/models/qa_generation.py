"""
Tables for QA Generation module

QA对生成任务表:
 - t_qa_generation_instances (QA生成任务实例表)
 - t_qa_pairs (QA对数据表)
"""

import uuid
from sqlalchemy import Column, String, Text, BigInteger, Integer, TIMESTAMP, JSON, DECIMAL
from sqlalchemy.sql import func

from app.db.session import Base


class QAGenerationInstance(Base):
    """QA生成任务实例表 -> t_qa_generation_instances

    字段说明:
      - id: 主键UUID
      - name: 任务名称
      - description: 任务描述
      - source_dataset_id: 源数据集ID
      - target_dataset_id: 目标数据集ID (存储生成的QA对JSONL文件)
      - text_split_config: 文本切片配置 (JSON)
      - qa_generation_config: QA生成配置 (JSON)
      - status: 任务状态 (PENDING, RUNNING, COMPLETED, FAILED)
      - total_files: 总文件数
      - processed_files: 已处理文件数
      - total_chunks: 总文本块数
      - processed_chunks: 已处理文本块数
      - total_qa_pairs: 生成的QA对总数
      - error_message: 错误信息
      - llm_api_key: LLM API密钥 (加密存储)
      - llm_base_url: LLM Base URL
      - created_at: 创建时间
      - updated_at: 更新时间
      - created_by: 创建者
      - updated_by: 更新者
    """

    __tablename__ = "t_qa_generation_instances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    source_dataset_id = Column(String(36), nullable=False, comment="源数据集ID (t_dm_datasets.id)")
    target_dataset_id = Column(String(36), nullable=True, comment="目标数据集ID (t_dm_datasets.id)")
    text_split_config = Column(JSON, nullable=False, comment="文本切片配置")
    qa_generation_config = Column(JSON, nullable=False, comment="QA生成配置")
    status = Column(String(20), nullable=False, default="PENDING", comment="任务状态")
    total_files = Column(Integer, nullable=True, default=0, comment="总文件数")
    processed_files = Column(Integer, nullable=True, default=0, comment="已处理文件数")
    total_chunks = Column(Integer, nullable=True, comment="总文本块数")
    processed_chunks = Column(Integer, nullable=True, default=0, comment="已处理文本块数")
    total_qa_pairs = Column(Integer, nullable=True, default=0, comment="生成的QA对总数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    llm_api_key = Column(Text, nullable=False, comment="LLM API密钥")
    llm_base_url = Column(String(512), nullable=False, comment="LLM Base URL")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

    def __repr__(self) -> str:
        return (
            f"<QAGenerationInstance(id={self.id}, name={self.name}, "
            f"status={self.status}, files={self.processed_files}/{self.total_files})>"
        )


class QAPair(Base):
    """QA对数据表 -> t_qa_pairs
    
    存储生成的问答对，每一行包含一个文本块及其对应的问题和答案
    
    字段说明:
      - id: 主键UUID
      - task_id: QA生成任务ID
      - source_file_id: 源文件ID (t_dm_dataset_files.id)
      - source_file_name: 源文件名
      - chunk_index: 文本块索引
      - text_chunk: 文本块内容
      - question: 问题
      - answer: 答案
      - question_type: 问题类型
      - confidence_score: 置信度分数
      - metadata: 其他元数据
      - created_at: 创建时间
    """

    __tablename__ = "t_qa_pairs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    task_id = Column(String(36), nullable=False, comment="QA生成任务ID (t_qa_generation_instances.id)")
    source_file_id = Column(String(36), nullable=False, comment="源文件ID (t_dm_dataset_files.id)")
    source_file_name = Column(String(255), nullable=False, comment="源文件名")
    chunk_index = Column(Integer, nullable=False, comment="文本块索引")
    text_chunk = Column(Text, nullable=False, comment="文本块内容")
    question = Column(Text, nullable=False, comment="问题")
    answer = Column(Text, nullable=False, comment="答案")
    question_type = Column(String(50), nullable=True, comment="问题类型")
    confidence_score = Column(DECIMAL(5, 4), nullable=True, comment="置信度分数")
    extra_metadata = Column("metadata", JSON, nullable=True, comment="其他元数据")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")

    def __repr__(self) -> str:
        return (
            f"<QAPair(id={self.id}, source_file={self.source_file_name}, "
            f"chunk={self.chunk_index}, q={self.question[:50]}...)>"
        )
