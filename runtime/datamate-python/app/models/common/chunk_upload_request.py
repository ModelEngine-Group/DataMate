from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class ChunkUploadRequest(Base):
    """文件切片上传请求模型"""
    
    __tablename__ = "t_chunk_upload_request"
    
    id = Column(String(36), primary_key=True, comment="UUID")
    total_file_num = Column(Integer, nullable=True, comment="总文件数")
    uploaded_file_num = Column(Integer, nullable=True, comment="已上传文件数")
    upload_path = Column(String(256), nullable=True, comment="文件路径")
    timeout = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="上传请求超时时间")
    service_id = Column(String(64), nullable=True, comment="上传请求所属服务：DATA-MANAGEMENT(数据管理)")
    check_info = Column(Text, nullable=True, comment="业务信息")
    
    def __repr__(self):
        return f"<ChunkUploadRequest(id={self.id}, service_id={self.service_id}, progress={self.uploaded_file_num}/{self.total_file_num})>"
