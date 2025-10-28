from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class Operator(Base):
    """算子模型"""
    
    __tablename__ = "t_operator"
    
    id = Column(String(64), primary_key=True, comment="算子ID")
    name = Column(String(64), nullable=True, comment="算子名称")
    description = Column(String(256), nullable=True, comment="算子描述")
    version = Column(String(256), nullable=True, comment="版本")
    inputs = Column(String(256), nullable=True, comment="输入类型")
    outputs = Column(String(256), nullable=True, comment="输出类型")
    runtime = Column(Text, nullable=True, comment="运行时信息")
    settings = Column(Text, nullable=True, comment="配置信息")
    file_name = Column(Text, nullable=True, comment="文件名")
    is_star = Column(Boolean, nullable=True, comment="是否收藏")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<Operator(id={self.id}, name={self.name}, version={self.version})>"
