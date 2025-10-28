from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class DatasetTag(Base):
    """数据集标签关联模型"""
    
    __tablename__ = "t_dm_dataset_tags"
    
    dataset_id = Column(String(36), primary_key=True, comment="数据集ID（UUID）")
    tag_id = Column(String(36), primary_key=True, comment="标签ID（UUID）")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    
    def __repr__(self):
        return f"<DatasetTag(dataset_id={self.dataset_id}, tag_id={self.tag_id})>"
