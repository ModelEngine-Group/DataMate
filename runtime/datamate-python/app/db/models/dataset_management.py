"""
Tables of Dataset Management Module
"""

import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, TIMESTAMP, Text, Integer, JSON, Date
from sqlalchemy.sql import func

from app.db.session import Base

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
    dataset_metadata = Column("metadata", JSON, nullable=True, comment="元数据信息")
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

class DatasetTag(Base):
    """数据集标签关联模型"""
    
    __tablename__ = "t_dm_dataset_tags"
    
    dataset_id = Column(String(36), primary_key=True, comment="数据集ID（UUID）")
    tag_id = Column(String(36), primary_key=True, comment="标签ID（UUID）")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    
    def __repr__(self):
        return f"<DatasetTag(dataset_id={self.dataset_id}, tag_id={self.tag_id})>"

class DatasetFiles(Base):
    """DM数据集文件模型"""
    
    __tablename__ = "t_dm_dataset_files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    dataset_id = Column(String(36), nullable=False, comment="所属数据集ID（UUID）")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(1000), nullable=False, comment="文件路径")
    file_type = Column(String(50), nullable=True, comment="文件格式：JPG/PNG/DCM/TXT等")
    file_size = Column(BigInteger, default=0, comment="文件大小(字节)")
    check_sum = Column(String(64), nullable=True, comment="文件校验和")
    tags = Column(JSON, nullable=True, comment="文件标签信息")
    tags_updated_at = Column(TIMESTAMP, nullable=True, comment="标签最后更新时间")
    dataset_filemetadata = Column("metadata", JSON, nullable=True, comment="文件元数据")
    status = Column(String(50), default='ACTIVE', comment="文件状态：ACTIVE/DELETED/PROCESSING")
    upload_time = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="上传时间")
    last_access_time = Column(TIMESTAMP, nullable=True, comment="最后访问时间")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<DatasetFiles(id={self.id}, dataset_id={self.dataset_id}, file_name={self.file_name})>"
    
class DatasetStatistics(Base):
    """数据集统计信息模型"""
    
    __tablename__ = "t_dm_dataset_statistics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    dataset_id = Column(String(36), nullable=False, comment="数据集ID（UUID）")
    stat_date = Column(Date, nullable=False, comment="统计日期")
    total_files = Column(BigInteger, default=0, comment="总文件数")
    total_size = Column(BigInteger, default=0, comment="总大小(字节)")
    processed_files = Column(BigInteger, default=0, comment="已处理文件数")
    error_files = Column(BigInteger, default=0, comment="错误文件数")
    download_count = Column(BigInteger, default=0, comment="下载次数")
    view_count = Column(BigInteger, default=0, comment="查看次数")
    quality_metrics = Column(JSON, nullable=True, comment="质量指标")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<DatasetStatistics(id={self.id}, dataset_id={self.dataset_id}, date={self.stat_date})>"

class Tag(Base):
    """标签集合模型"""
    
    __tablename__ = "t_dm_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(100), nullable=False, unique=True, comment="标签名称")
    description = Column(Text, nullable=True, comment="标签描述")
    category = Column(String(50), nullable=True, comment="标签分类")
    color = Column(String(7), nullable=True, comment="标签颜色(十六进制)")
    usage_count = Column(BigInteger, default=0, comment="使用次数")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, category={self.category})>"