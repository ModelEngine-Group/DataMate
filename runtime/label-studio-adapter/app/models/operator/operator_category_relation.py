from sqlalchemy import Column, String, Integer
from app.db.database import Base

class OperatorCategoryRelation(Base):
    """算子分类关联模型"""
    
    __tablename__ = "t_operator_category_relation"
    
    category_id = Column(Integer, primary_key=True, comment="分类ID")
    operator_id = Column(String(64), primary_key=True, comment="算子ID")
    
    def __repr__(self):
        return f"<OperatorCategoryRelation(category_id={self.category_id}, operator_id={self.operator_id})>"
