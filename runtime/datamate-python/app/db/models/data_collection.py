import uuid
from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, BigInteger, Numeric, JSON, Boolean
from sqlalchemy.sql import func

from app.db.models.base_entity import BaseEntity


class CollectionTemplate(BaseEntity):
    """归集模板表（UUID 主键） -> t_dc_collection_templates"""

    __tablename__ = "t_dc_collection_templates"
    __ignore_data_scope__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="模板ID（UUID）")
    name = Column(String(255), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    source_type = Column(String(64), nullable=False, comment="源数据源类型")
    source_name = Column(String(64), nullable=False, comment="源数据源名称")
    target_type = Column(String(64), nullable=False, comment="目标数据源类型")
    target_name = Column(String(64), nullable=False, comment="目标数据源名称")
    template_content = Column(JSON, nullable=False, comment="模板内容")
    built_in = Column(Boolean, default=False, comment="是否系统内置模板")

class CollectionTask(BaseEntity):
    """归集任务表（UUID 主键） -> t_dc_collection_tasks"""

    __tablename__ = "t_dc_collection_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    sync_mode = Column(String(20), nullable=False, server_default="ONCE", comment="同步模式：ONCE/SCHEDULED")
    template_id = Column(String(36), nullable=False, comment="归集模板ID")
    template_name = Column(String(255), nullable=False, comment="归集模板名称")
    target_path = Column(String(1000), nullable=True, server_default="", comment="目标存储路径")
    config = Column(JSON, nullable=False, comment="归集配置（DataX配置），包含源端和目标端配置信息")
    schedule_expression = Column(String(255), nullable=True, comment="Cron调度表达式")
    status = Column(String(20), nullable=True, server_default="DRAFT", comment="任务状态：DRAFT/READY/RUNNING/SUCCESS/FAILED/STOPPED")
    retry_count = Column(Integer, nullable=True, server_default="3", comment="重试次数")
    timeout_seconds = Column(Integer, nullable=True, server_default="3600", comment="超时时间（秒）")
    last_execution_id = Column(String(36), nullable=True, comment="最后执行ID（UUID）")

class TaskExecution(BaseEntity):
    """任务执行记录表（UUID 主键） -> t_dc_task_executions"""

    __tablename__ = "t_dc_task_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="执行记录ID（UUID）")
    task_id = Column(String(36), nullable=False, comment="任务ID")
    task_name = Column(String(255), nullable=False, comment="任务名称")
    status = Column(String(20), nullable=True, server_default="RUNNING", comment="执行状态：RUNNING/SUCCESS/FAILED/STOPPED")
    log_path = Column(String(1000), nullable=True, server_default="", comment="日志文件路径")
    started_at = Column(TIMESTAMP, nullable=True, comment="开始时间")
    completed_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    duration_seconds = Column(Integer, nullable=True, server_default="0", comment="执行时长（秒）")
    error_message = Column(Text, nullable=True, comment="错误信息")
