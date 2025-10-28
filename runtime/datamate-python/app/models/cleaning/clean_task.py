from sqlalchemy import Column, String, BigInteger, Integer, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class CleanTask(Base):
    """清洗任务模型"""
    
    __tablename__ = "t_clean_task"
    
    id = Column(String(64), primary_key=True, comment="任务ID")
    name = Column(String(64), nullable=True, comment="任务名称")
    description = Column(String(256), nullable=True, comment="任务描述")
    status = Column(String(256), nullable=True, comment="任务状态")
    src_dataset_id = Column(String(64), nullable=True, comment="源数据集ID")
    src_dataset_name = Column(String(64), nullable=True, comment="源数据集名称")
    dest_dataset_id = Column(String(64), nullable=True, comment="目标数据集ID")
    dest_dataset_name = Column(String(64), nullable=True, comment="目标数据集名称")
    before_size = Column(BigInteger, nullable=True, comment="清洗前大小")
    after_size = Column(BigInteger, nullable=True, comment="清洗后大小")
    file_count = Column(Integer, nullable=True, comment="文件数量")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    started_at = Column(TIMESTAMP, nullable=True, comment="开始时间")
    finished_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    created_by = Column(String(256), nullable=True, comment="创建者")
    
    def __repr__(self):
        return f"<CleanTask(id={self.id}, name={self.name}, status={self.status})>"
