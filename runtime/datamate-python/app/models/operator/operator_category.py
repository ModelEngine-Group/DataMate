from sqlalchemy import Column, String, Integer
from app.db.database import Base

class OperatorCategory(Base):
    """算子分类模型"""
    
    __tablename__ = "t_operator_category"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(64), nullable=True, comment="分类名称")
    type = Column(String(64), nullable=True, comment="分类类型")
    parent_id = Column(Integer, nullable=True, comment="父分类ID")
    
    def __repr__(self):
        return f"<OperatorCategory(id={self.id}, name={self.name}, type={self.type})>"
