from sqlalchemy import Column, String, Text, Integer, BigInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class TaskLog(Base):
    """任务执行记录模型"""
    
    __tablename__ = "t_dc_task_log"
    
    id = Column(String(36), primary_key=True, comment="执行记录ID（UUID）")
    task_id = Column(String(36), nullable=False, comment="任务ID")
    task_name = Column(String(255), nullable=False, comment="任务名称")
    sync_mode = Column(String(20), default='FULL', comment="同步模式：FULL/INCREMENTAL")
    status = Column(String(20), default='RUNNING', comment="执行状态：RUNNING/SUCCESS/FAILED/STOPPED")
    start_time = Column(TIMESTAMP, nullable=True, comment="开始时间")
    end_time = Column(TIMESTAMP, nullable=True, comment="结束时间")
    duration = Column(BigInteger, nullable=True, comment="执行时长(毫秒)")
    process_id = Column(String(50), nullable=True, comment="进程ID")
    log_path = Column(String(500), nullable=True, comment="日志文件路径")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    result = Column(Text, nullable=True, comment="执行结果")
    retry_times = Column(Integer, default=0, comment="重试次数")
    create_time = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    
    def __repr__(self):
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, status={self.status})>"
