from sqlalchemy import Column, String, BigInteger, Text
from app.db.database import Base

class CleanResult(Base):
    """清洗结果模型"""
    
    __tablename__ = "t_clean_result"
    
    instance_id = Column(String(64), primary_key=True, comment="实例ID")
    src_file_id = Column(String(64), nullable=True, comment="源文件ID")
    dest_file_id = Column(String(64), primary_key=True, comment="目标文件ID")
    src_name = Column(String(256), nullable=True, comment="源文件名")
    dest_name = Column(String(256), nullable=True, comment="目标文件名")
    src_type = Column(String(256), nullable=True, comment="源文件类型")
    dest_type = Column(String(256), nullable=True, comment="目标文件类型")
    src_size = Column(BigInteger, nullable=True, comment="源文件大小")
    dest_size = Column(BigInteger, nullable=True, comment="目标文件大小")
    status = Column(String(256), nullable=True, comment="处理状态")
    result = Column(Text, nullable=True, comment="处理结果")
    
    def __repr__(self):
        return f"<CleanResult(instance_id={self.instance_id}, dest_file_id={self.dest_file_id}, status={self.status})>"
