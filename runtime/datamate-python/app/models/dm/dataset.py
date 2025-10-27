from sqlalchemy import Column, String, Text, BigInteger, Integer, Boolean, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class Dataset(Base):
    """数据集模型（支持医学影像、文本、问答等多种类型）"""
    
    __tablename__ = "t_dm_datasets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="数据集名称")
    description = Column(Text, nullable=True, comment="数据集描述")
    dataset_type = Column(String(50), nullable=False, comment="数据集类型：IMAGE/TEXT/QA/MULTIMODAL/OTHER")
    category = Column(String(100), nullable=True, comment="数据集分类：医学影像/问答/文献等")
    path = Column(String(500), nullable=True, comment="数据存储路径")
    format = Column(String(50), nullable=True, comment="数据格式：DCM/JPG/JSON/CSV等")
    schema_info = Column(JSON, nullable=True, comment="数据结构信息")
    size_bytes = Column(BigInteger, default=0, comment="数据大小(字节)")
    file_count = Column(BigInteger, default=0, comment="文件数量")
    record_count = Column(BigInteger, default=0, comment="记录数量")
    retention_days = Column(Integer, default=0, comment="数据保留天数（0表示长期保留）")
    tags = Column(JSON, nullable=True, comment="标签列表")
    metadata = Column(JSON, nullable=True, comment="元数据信息")
    status = Column(String(50), default='DRAFT', comment="状态：DRAFT/ACTIVE/ARCHIVED")
    is_public = Column(Boolean, default=False, comment="是否公开")
    is_featured = Column(Boolean, default=False, comment="是否推荐")
    version = Column(BigInteger, nullable=False, default=0, comment="版本号")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name={self.name}, type={self.dataset_type})>"
