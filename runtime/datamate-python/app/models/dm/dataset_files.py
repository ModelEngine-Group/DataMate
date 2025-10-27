from sqlalchemy import Column, String, JSON, BigInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

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
    metadata = Column(JSON, nullable=True, comment="文件元数据")
    status = Column(String(50), default='ACTIVE', comment="文件状态：ACTIVE/DELETED/PROCESSING")
    upload_time = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="上传时间")
    last_access_time = Column(TIMESTAMP, nullable=True, comment="最后访问时间")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<DatasetFiles(id={self.id}, dataset_id={self.dataset_id}, file_name={self.file_name})>"