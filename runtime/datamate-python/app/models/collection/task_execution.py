from sqlalchemy import Column, String, Text, Integer, BigInteger, DECIMAL, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class TaskExecution(Base):
    """任务执行明细模型"""
    
    __tablename__ = "t_dc_task_executions"
    
    id = Column(String(36), primary_key=True, comment="执行记录ID（UUID）")
    task_id = Column(String(36), nullable=False, comment="任务ID")
    task_name = Column(String(255), nullable=False, comment="任务名称")
    status = Column(String(20), default='RUNNING', comment="执行状态：RUNNING/SUCCESS/FAILED/STOPPED")
    progress = Column(DECIMAL(5, 2), default=0.00, comment="进度百分比")
    records_total = Column(BigInteger, default=0, comment="总记录数")
    records_processed = Column(BigInteger, default=0, comment="已处理记录数")
    records_success = Column(BigInteger, default=0, comment="成功记录数")
    records_failed = Column(BigInteger, default=0, comment="失败记录数")
    throughput = Column(DECIMAL(10, 2), default=0.00, comment="吞吐量（条/秒）")
    data_size_bytes = Column(BigInteger, default=0, comment="数据量（字节）")
    started_at = Column(TIMESTAMP, nullable=True, comment="开始时间")
    completed_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    duration_seconds = Column(Integer, default=0, comment="执行时长（秒）")
    config = Column(JSON, nullable=True, comment="执行配置")
    error_message = Column(Text, nullable=True, comment="错误信息")
    datax_job_id = Column(Text, nullable=True, comment="datax任务ID")
    result = Column(Text, nullable=True, comment="执行结果")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")
    
    def __repr__(self):
        return f"<TaskExecution(id={self.id}, task_id={self.task_id}, status={self.status})>"
