import uuid

from sqlalchemy import Column, String, Text, Integer, JSON, TIMESTAMP, func

from app.db.models.base_entity import Base, BaseEntity
from app.module.generation.schema.generation import CreateSynthesisTaskRequest


async def save_synthesis_task(db_session, synthesis_task: CreateSynthesisTaskRequest):
    """保存数据合成任务。

    注意：当前 MySQL 表 `t_data_synth_instances` 结构中只包含 synth_type / synth_config 等字段，
    没有 model_id、text_split_config、source_file_id、result_data_location 等列，因此这里只保存
    与表结构一致的字段，其他信息由上层逻辑或其它表负责管理。
    """
    gid = str(uuid.uuid4())

    # 兼容旧请求结构：从请求对象中提取必要字段，
    #   - 合成类型：synthesis_type -> synth_type
    #   - 合成配置：text_split_config + synthesis_config 合并后写入 synth_config

    synth_task_instance = DataSynthInstance(
        id=gid,
        name=synthesis_task.name,
        description=synthesis_task.description,
        status="pending",
        synth_type=synthesis_task.synthesis_type.value,
        progress=0,
        synth_config=synthesis_task.synth_config.model_dump(),
        total_files=len(synthesis_task.source_file_id or []),
        processed_files=0,
        total_chunks=0,
        processed_chunks=0,
        total_synth_data=0,
        created_at=func.now(),
        updated_at=func.now(),
        created_by="system",
        updated_by="system",
    )
    db_session.add(synth_task_instance)
    await db_session.commit()
    await db_session.refresh(synth_task_instance)
    return synth_task_instance


class DataSynthInstance(BaseEntity):
    """数据合成任务表，对应表 t_data_synth_instances

    create table if not exists t_data_synth_instances
    (
        id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
        name VARCHAR(255) NOT NULL COMMENT '任务名称',
        description TEXT COMMENT '任务描述',
        status VARCHAR(20) COMMENT '任务状态',
        synth_type VARCHAR(20) NOT NULL COMMENT '合成类型',
        progress INT DEFAULT 0 COMMENT '任务进度(百分比)',
        synth_config JSON NOT NULL COMMENT '合成配置',
        total_files INT DEFAULT 0 COMMENT '总文件数',
        processed_files INT DEFAULT 0 COMMENT '已处理文件数',
        total_chunks INT DEFAULT 0 COMMENT '总文本块数',
        processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
        total_synth_data INT DEFAULT 0 COMMENT '总合成数据量',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        created_by VARCHAR(255) COMMENT '创建者',
        updated_by VARCHAR(255) COMMENT '更新者'
    ) COMMENT='数据合成任务表（UUID 主键）';
    """

    __tablename__ = "t_data_synth_instances"

    id = Column(String(36), primary_key=True, index=True, comment="UUID")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(String(20), nullable=True, comment="任务状态")
    # 与数据库字段保持一致：synth_type / synth_config
    synth_type = Column(String(20), nullable=False, comment="合成类型")
    progress = Column(Integer, nullable=False, default=0, comment="任务进度(百分比)")
    synth_config = Column(JSON, nullable=False, comment="合成配置")
    total_files = Column(Integer, nullable=False, default=0, comment="总文件数")
    processed_files = Column(Integer, nullable=False, default=0, comment="已处理文件数")
    total_chunks = Column(Integer, nullable=False, default=0, comment="总文本块数")
    processed_chunks = Column(Integer, nullable=False, default=0, comment="已处理文本块数")
    total_synth_data = Column(Integer, nullable=False, default=0, comment="总合成数据量")


class DataSynthesisFileInstance(BaseEntity):
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
    target_file_location = Column(String(1000), nullable=True, comment="目标文件存储位置")
    status = Column(String(20), nullable=True, comment="任务状态")
    total_chunks = Column(Integer, nullable=False, default=0, comment="总文本块数")
    processed_chunks = Column(Integer, nullable=False, default=0, comment="已处理文本块数")


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
