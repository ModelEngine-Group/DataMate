from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class CleanTemplate(Base):
    """清洗模板模型"""
    
    __tablename__ = "t_clean_template"
    
    id = Column(String(64), primary_key=True, unique=True, comment="模板ID")
    name = Column(String(64), nullable=True, comment="模板名称")
    description = Column(String(256), nullable=True, comment="模板描述")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(256), nullable=True, comment="创建者")
    
    def __repr__(self):
        return f"<CleanTemplate(id={self.id}, name={self.name})>"
