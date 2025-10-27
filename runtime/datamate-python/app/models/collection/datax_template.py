from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class DataxTemplate(Base):
    """DataX模板配置模型"""
    
    __tablename__ = "t_dc_datax_templates"
    
    id = Column(String(36), primary_key=True, comment="模板ID（UUID）")
    name = Column(String(255), nullable=False, unique=True, comment="模板名称")
    source_type = Column(String(50), nullable=False, comment="源数据源类型")
    target_type = Column(String(50), nullable=False, comment="目标数据源类型")
    template_content = Column(Text, nullable=False, comment="模板内容")
    description = Column(Text, nullable=True, comment="模板描述")
    version = Column(String(20), default='1.0.0', comment="版本号")
    is_system = Column(Boolean, default=False, comment="是否系统模板")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    
    def __repr__(self):
        return f"<DataxTemplate(id={self.id}, name={self.name}, source={self.source_type}, target={self.target_type})>"
