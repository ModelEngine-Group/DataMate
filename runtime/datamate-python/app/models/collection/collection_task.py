from sqlalchemy import Column, String, Text, Integer, BigInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class CollectionTask(Base):
    """数据归集任务模型"""
    
    __tablename__ = "t_dc_collection_tasks"
    
    id = Column(String(36), primary_key=True, comment="任务ID（UUID）")
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    sync_mode = Column(String(20), default='ONCE', comment="同步模式：ONCE/SCHEDULED")
    config = Column(Text, nullable=False, comment="归集配置（DataX配置），包含源端和目标端配置信息")
    schedule_expression = Column(String(255), nullable=True, comment="Cron调度表达式")
    status = Column(String(20), default='DRAFT', comment="任务状态：DRAFT/READY/RUNNING/SUCCESS/FAILED/STOPPED")
    retry_count = Column(Integer, default=3, comment="重试次数")
    timeout_seconds = Column(Integer, default=3600, comment="超时时间（秒）")
    max_records = Column(BigInteger, nullable=True, comment="最大处理记录数")
    sort_field = Column(String(100), nullable=True, comment="增量字段")
    last_execution_id = Column(String(36), nullable=True, comment="最后执行ID（UUID）")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")
    
    def __repr__(self):
        return f"<CollectionTask(id={self.id}, name={self.name}, status={self.status})>"
