import uuid
from xml.etree.ElementTree import tostring

from sqlalchemy import Column, String, Text, Integer, JSON, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.module.generation.schema.generation import CreateSynthesisTaskRequest


async def save_synthesis_task(db_session, synthesis_task: CreateSynthesisTaskRequest):
    """保存数据合成任务。"""
    # 转换为模型实例
    gid = str(uuid.uuid4())
    synthesis_task_instance = DataSynthesisInstance(
        id=gid,
        name=synthesis_task.name,
        description=synthesis_task.description,
        status="pending",
        model_id=synthesis_task.model_id,
        synthesis_type=synthesis_task.synthesis_type.value,
        progress=0,
        result_data_location=f"/dataset/synthesis_results/{gid}/",
        text_split_config=synthesis_task.text_split_config.model_dump(),
        synthesis_config=synthesis_task.synthesis_config.model_dump(),
        source_file_id=synthesis_task.source_file_id,
        total_files=len(synthesis_task.source_file_id),
        processed_files=0,
        total_chunks=0,
        processed_chunks=0,
        total_synthesis_data=0,
        created_at=func.now(),
        updated_at=func.now(),
        created_by="system",
        updated_by="system"
    )
    db_session.add(synthesis_task_instance)
    await db_session.commit()
    await db_session.refresh(synthesis_task_instance)
    return synthesis_task_instance


class DataSynthesisInstance(Base):
    """数据合成任务表，对应表 t_data_synthesis_instances

    create table if not exists t_data_synthesis_instances
    (
        id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
        name VARCHAR(255) NOT NULL COMMENT '任务名称',
        description TEXT COMMENT '任务描述',
        status VARCHAR(20) COMMENT '任务状态',
        synthesis_type VARCHAR(20) NOT NULL COMMENT '合成类型',
        model_id VARCHAR(255) NOT NULL COMMENT '模型ID',
        progress INT DEFAULT 0 COMMENT '任务进度(百分比)',
        result_data_location VARCHAR(1000) COMMENT '结果数据存储位置',
        text_split_config JSON NOT NULL COMMENT '文本切片配置',
        synthesis_config JSON NOT NULL COMMENT '合成配置',
        source_file_id JSON NOT NULL COMMENT '原始文件ID列表',
        total_files INT DEFAULT 0 COMMENT '总文件数',
        processed_files INT DEFAULT 0 COMMENT '已处理文件数',
        total_chunks INT DEFAULT 0 COMMENT '总文本块数',
        processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
        total_synthesis_data INT DEFAULT 0 COMMENT '总合成数据量',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        created_by VARCHAR(255) COMMENT '创建者',
        updated_by VARCHAR(255) COMMENT '更新者'
    ) COMMENT='数据合成任务表（UUID 主键）';
    """

    __tablename__ = "t_data_synthesis_instances"

    id = Column(String(36), primary_key=True, index=True, comment="UUID")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(String(20), nullable=True, comment="任务状态")
    synthesis_type = Column(String(20), nullable=False, comment="合成类型")
    model_id = Column(String(255), nullable=False, comment="模型ID")
    progress = Column(Integer, nullable=False, default=0, comment="任务进度(百分比)")
    result_data_location = Column(String(1000), nullable=True, comment="结果数据存储位置")
    text_split_config = Column(JSON, nullable=False, comment="文本切片配置")
    synthesis_config = Column(JSON, nullable=False, comment="合成配置")
    source_file_id = Column(JSON, nullable=False, comment="原始文件ID列表")
    total_files = Column(Integer, nullable=False, default=0, comment="总文件数")
    processed_files = Column(Integer, nullable=False, default=0, comment="已处理文件数")
    total_chunks = Column(Integer, nullable=False, default=0, comment="总文本块数")
    processed_chunks = Column(Integer, nullable=False, default=0, comment="已处理文本块数")
    total_synthesis_data = Column(Integer, nullable=False, default=0, comment="总合成数据量")

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True, comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True, comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")


class DataSynthesisFileInstance(Base):
    """数据合成文件任务表，对应表 t_data_synthesis_file_instances

    create table if not exists t_data_synthesis_file_instances (
        id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
        synthesis_instance_id VARCHAR(36) COMMENT '数据合成任务ID',
        file_name VARCHAR(255) NOT NULL COMMENT '文件名',
        source_file_id VARCHAR(255) NOT NULL COMMENT '原始文件ID',
        target_file_location VARCHAR(1000) NOT NULL COMMENT '目标文件存储位置',
        status VARCHAR(20) COMMENT '任务状态',
        total_chunks INT DEFAULT 0 COMMENT '总文本块数',
        processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        created_by VARCHAR(255) COMMENT '创建者',
        updated_by VARCHAR(255) COMMENT '更新者'
    ) COMMENT='数据合成文件任务表（UUID 主键）';
    """

    __tablename__ = "t_data_synthesis_file_instances"

    id = Column(String(36), primary_key=True, index=True, comment="UUID")
    synthesis_instance_id = Column(
        String(36),
        nullable=False,
        comment="数据合成任务ID",
        index=True,
    )
    file_name = Column(String(255), nullable=False, comment="文件名")
    source_file_id = Column(String(255), nullable=False, comment="原始文件ID")
    target_file_location = Column(String(1000), nullable=False, comment="目标文件存储位置")
    status = Column(String(20), nullable=True, comment="任务状态")
    total_chunks = Column(Integer, nullable=False, default=0, comment="总文本块数")
    processed_chunks = Column(Integer, nullable=False, default=0, comment="已处理文本块数")

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True, comment="创建时间")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=True,
        comment="更新时间",
    )
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")


class DataSynthesisChunkInstance(Base):
    """数据合成分块任务表，对应表 t_data_synthesis_chunk_instances

    create table if not exists t_data_synthesis_chunk_instances (
        id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
        synthesis_file_instance_id VARCHAR(36) COMMENT '数据合成文件任务ID',
        chunk_index INT COMMENT '分块索引',
        chunk_content TEXT COMMENT '分块内容',
        metadata JSON COMMENT '分块元数据'
    ) COMMENT='数据合成分块任务表（UUID 主键）';
    """

    __tablename__ = "t_data_synthesis_chunk_instances"

    id = Column(String(36), primary_key=True, index=True, comment="UUID")
    synthesis_file_instance_id = Column(
        String(36),
        nullable=False,
        comment="数据合成文件任务ID",
        index=True,
    )
    chunk_index = Column(Integer, nullable=True, comment="分块索引")
    chunk_content = Column(Text, nullable=True, comment="分块内容")
    # SQLAlchemy Declarative 保留了属性名 'metadata'，这里使用 chunk_metadata 作为属性名，
    # 底层列名仍为 'metadata' 以保持与表结构兼容。
    chunk_metadata = Column("metadata", JSON, nullable=True, comment="分块元数据")


class SynthesisData(Base):
    """数据合成结果表，对应表 t_synthesis_data

    create table if not exists t_synthesis_data (
        id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
        data json COMMENT '合成的数据',
        synthesis_file_instance_id VARCHAR(36) COMMENT '数据合成文件任务ID',
        chunk_instance_id VARCHAR(36) COMMENT '分块任务ID'
    ) COMMENT='数据合成任务队列表（UUID 主键）';
    """

    __tablename__ = "t_data_synthesis_data"

    id = Column(String(36), primary_key=True, index=True, comment="UUID")
    data = Column(JSON, nullable=True, comment="合成的数据")
    synthesis_file_instance_id = Column(
        String(36),
        nullable=False,
        comment="数据合成文件任务ID",
        index=True,
    )
    chunk_instance_id = Column(
        String(36),
        nullable=False,
        comment="分块任务ID",
        index=True,
    )
