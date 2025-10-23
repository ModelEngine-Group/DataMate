from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class DatasetMapping(Base):
    """数据集映射模型"""
    
    __tablename__ = "mapping"
    
    mapping_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_dataset_id = Column(String(36), nullable=False, comment="源数据集ID")
    labelling_project_id = Column(String(36), nullable=False, comment="标注项目ID")
    labelling_project_name = Column(String(255), nullable=True, comment="标注项目名称")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="最后更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间")
    
    def __repr__(self):
        return f"<DatasetMapping(uuid={self.mapping_id}, source={self.source_dataset_id}, labelling={self.labelling_project_id})>"
    
    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None