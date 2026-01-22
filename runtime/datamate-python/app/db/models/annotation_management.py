"""Tables of Annotation Management Module"""

import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, Text, Integer, JSON, ForeignKey
from sqlalchemy.sql import func

from app.db.models.base_entity import BaseEntity

class AnnotationTemplate(BaseEntity):
    """标注配置模板模型"""

    __tablename__ = "t_dm_annotation_templates"
    __ignore_data_scope__ = True

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
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")

    def __repr__(self):
        return f"<AnnotationTemplate(id={self.id}, name={self.name}, data_type={self.data_type})>"

    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None

class LabelingProject(BaseEntity):
    """标注项目模型"""

    __tablename__ = "t_dm_labeling_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    dataset_id = Column(String(36), nullable=False, comment="数据集ID")
    name = Column(String(100), nullable=False, comment="项目名称")
    labeling_project_id = Column(String(8), nullable=False, comment="Label Studio项目ID")
    template_id = Column(String(36), ForeignKey('t_dm_annotation_templates.id', ondelete='SET NULL'), nullable=True, comment="使用的模板ID")
    configuration = Column(JSON, nullable=True, comment="项目配置（可能包含对模板的自定义修改）")
    progress = Column(JSON, nullable=True, comment="项目进度信息")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")

    def __repr__(self):
        return f"<LabelingProject(id={self.id}, name={self.name}, dataset_id={self.dataset_id})>"

    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None


class AutoAnnotationTask(BaseEntity):
    """自动标注任务模型，对应表 t_dm_auto_annotation_tasks"""

    __tablename__ = "t_dm_auto_annotation_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="任务名称")
    dataset_id = Column(String(36), nullable=False, comment="数据集ID")
    dataset_name = Column(String(255), nullable=True, comment="数据集名称（冗余字段，方便查询）")
    config = Column(JSON, nullable=False, comment="任务配置（模型规模、置信度等）")
    file_ids = Column(JSON, nullable=True, comment="要处理的文件ID列表，为空则处理数据集所有图像")
    status = Column(String(50), nullable=False, default="pending", comment="任务状态: pending/running/completed/failed")
    progress = Column(Integer, default=0, comment="任务进度 0-100")
    total_images = Column(Integer, default=0, comment="总图片数")
    processed_images = Column(Integer, default=0, comment="已处理图片数")
    detected_objects = Column(Integer, default=0, comment="检测到的对象总数")
    output_path = Column(String(500), nullable=True, comment="输出路径")
    error_message = Column(Text, nullable=True, comment="错误信息")
    completed_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    deleted_at = Column(TIMESTAMP, nullable=True, comment="删除时间（软删除）")

    def __repr__(self) -> str:  # pragma: no cover - repr 简单返回
        return f"<AutoAnnotationTask(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_deleted(self) -> bool:
        """检查是否已被软删除"""
        return self.deleted_at is not None
