from sqlalchemy import Column, String, Text, BigInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class Tag(Base):
    """标签模型"""
    
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
