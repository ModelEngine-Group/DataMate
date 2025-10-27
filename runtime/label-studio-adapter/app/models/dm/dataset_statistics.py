from sqlalchemy import Column, String, Date, BigInteger, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

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
