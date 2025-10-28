from sqlalchemy import Column, String, Integer, Text
from app.db.database import Base

class OperatorInstance(Base):
    """算子实例模型"""
    
    __tablename__ = "t_operator_instance"
    
    instance_id = Column(String(256), primary_key=True, comment="实例ID")
    operator_id = Column(String(256), primary_key=True, comment="算子ID")
    op_index = Column(Integer, primary_key=True, comment="算子索引")
    settings_override = Column(Text, nullable=True, comment="配置覆盖")
    
    def __repr__(self):
        return f"<OperatorInstance(instance_id={self.instance_id}, operator_id={self.operator_id}, index={self.op_index})>"
