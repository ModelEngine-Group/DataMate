"""
Tables of Annotation Management Module
"""

import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, TIMESTAMP, Text, Integer, JSON, Date, ForeignKey
from sqlalchemy.sql import func

from app.db.session import Base

class AnnotationTemplate(Base):
    """标注配置模板模型"""
    
    __tablename__ = "t_dm_annotation_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(500), nullable=True, comment="模板描述")
    data_type = Column(String(50), nullable=False, comment="数据类型: image/text/audio/video/timeseries")
    labeling_type = Column(String(50), nullable=False, comment="标注类型: classification/detection/segmentation/ner/relation/etc")
    configuration = Column(JSON, nullable=False, comment="标注配置（包含labels定义等）")
    style = Column(String(32), nullable=False, comment="样式配置: horizontal/vertical")
    category = Column(String(50), default='custom', comment="模板分类: medical/general/custom/system")
    built_in = Column(Boolean, default=False, comment="是否系统内置模板")
    version = Column(String(20), default='1.0', comment="模板版本")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")
    
    def __repr__(self):
        return f"<AnnotationTemplate(id={self.id}, name={self.name}, data_type={self.data_type})>"
    
    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None
    
class LabelingProject(Base):
    """标注项目模型"""
    
    __tablename__ = "t_dm_labeling_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    dataset_id = Column(String(36), nullable=False, comment="数据集ID")
    name = Column(String(100), nullable=False, comment="项目名称")
    labeling_project_id = Column(String(8), nullable=False, comment="Label Studio项目ID")
    template_id = Column(String(36), ForeignKey('t_dm_annotation_templates.id', ondelete='SET NULL'), nullable=True, comment="使用的模板ID")
    configuration = Column(JSON, nullable=True, comment="项目配置（可能包含对模板的自定义修改）")
    progress = Column(JSON, nullable=True, comment="项目进度信息")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")
    
    def __repr__(self):
        return f"<LabelingProject(id={self.id}, name={self.name}, dataset_id={self.dataset_id})>"
    
    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None