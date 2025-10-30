"""
Tables of Annotation Management Module
"""

import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, TIMESTAMP, Text, Integer, JSON, Date
from sqlalchemy.sql import func

from app.db.session import Base

class AnnotationTemplate(Base):
    """标注模板模型"""
    
    __tablename__ = "t_dm_annotation_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID主键ID")
    name = Column(String(32), nullable=False, comment="模板名称")
    description = Column(String(255), nullable=True, comment="模板描述")
    configuration = Column(JSON, nullable=True, comment="配置信息（JSON格式）")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")
    
    def __repr__(self):
        return f"<AnnotationTemplate(id={self.id}, name={self.name})>"
    
    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None
    
class LabelingProject(Base):
    """标注工程表"""
    
    __tablename__ = "t_dm_labeling_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID主键ID")
    dataset_id = Column(String(36), nullable=False, comment="数据集ID")
    name = Column(String(32), nullable=False, comment="项目名称")
    labeling_project_id = Column(String(8), nullable=False, comment="Label Studio项目ID")
    configuration = Column(JSON, nullable=True, comment="标签配置")
    progress = Column(JSON, nullable=True, comment="标注进度统计")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")
    
    def __repr__(self):
        return f"<LabelingProject(id={self.id}, dataset_id={self.dataset_id}, name={self.name})>"
    
    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None