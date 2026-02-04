"""
Chunk Upload Database Model
分片上传数据库模型
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from app.db.models.base_entity import Base


class ChunkUploadPreRequest(Base):
    """分片上传预请求"""
    __tablename__ = "t_chunk_upload_request"

    id = Column(String(36), primary_key=True, comment="请求ID")
    total_file_num = Column(Integer, nullable=False, comment="总文件数")
    uploaded_file_num = Column(Integer, nullable=True, comment="已上传文件数")
    upload_path = Column(String(512), nullable=False, comment="文件路径")
    timeout = Column(DateTime, nullable=False, comment="上传请求超时时间")
    service_id = Column(String(64), nullable=True, comment="上传请求所属服务ID")
    check_info = Column(String(512), nullable=True, comment="业务信息")

    def increment_uploaded_file_num(self):
        """增加已上传文件数"""
        if self.uploaded_file_num is None:
            self.uploaded_file_num = 1
        else:
            self.uploaded_file_num += 1

    def is_upload_complete(self) -> bool:
        """检查是否已完成上传"""
        return (self.uploaded_file_num is not None and
                self.uploaded_file_num == self.total_file_num)

    def is_request_timeout(self) -> bool:
        """检查是否已超时"""
        from datetime import datetime
        return self.timeout is not None and datetime.utcnow() > self.timeout
