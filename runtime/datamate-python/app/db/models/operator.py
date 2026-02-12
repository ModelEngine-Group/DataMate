"""
Operator Market Data Models
算子市场数据模型
"""
from sqlalchemy import Column, String, Integer, Boolean, BigInteger, Text, JSON, TIMESTAMP, Index
from sqlalchemy.sql import func

from app.db.models.base_entity import Base, BaseEntity


class Operator(BaseEntity):
    """算子实体"""
    __tablename__ = "t_operator"

    id = Column(String(36), primary_key=True, index=True, comment="算子ID")
    name = Column(String(255), nullable=False, comment="算子名称")
    description = Column(Text, nullable=True, comment="算子描述")
    version = Column(String(50), nullable=False, comment="算子版本")
    inputs = Column(Text, nullable=True, comment="输入定义（JSON）")
    outputs = Column(Text, nullable=True, comment="输出定义（JSON）")
    runtime = Column(Text, nullable=True, comment="运行时配置（JSON）")
    settings = Column(Text, nullable=True, comment="算子设置（JSON）")
    file_name = Column(String(255), nullable=True, comment="文件名")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")
    metrics = Column(Text, nullable=True, comment="算子指标（JSON）")
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    is_star = Column(Boolean, default=False, nullable=False, comment="是否收藏")

    __table_args__ = (
        Index("idx_is_star", "is_star"),
    )


class Category(BaseEntity):
    """算子分类实体"""
    __tablename__ = "t_operator_category"

    id = Column(String(36), primary_key=True, index=True, comment="分类ID")
    name = Column(String(255), nullable=False, comment="分类名称")
    value = Column(String(255), nullable=True, comment="分类值")
    type = Column(String(50), nullable=True, comment="分类类型")
    parent_id = Column(String(36), nullable=False, default="0", comment="父分类ID")


class CategoryRelation(BaseEntity):
    """算子分类关系实体"""
    __tablename__ = "t_operator_category_relation"

    category_id = Column(String(36), primary_key=True, comment="分类ID")
    operator_id = Column(String(36), primary_key=True, comment="算子ID")

    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_operator_id", "operator_id"),
    )


class OperatorRelease(BaseEntity):
    """算子发布版本实体"""
    __tablename__ = "t_operator_release"

    id = Column(String(36), primary_key=True, comment="算子ID")
    version = Column(String(50), primary_key=True, comment="版本号")
    release_date = Column(TIMESTAMP, nullable=False, default=func.now(), comment="发布时间")
    changelog = Column(JSON, nullable=True, comment="更新日志列表")


# Ignore data scope for operator models
for model in [Operator, Category, CategoryRelation, OperatorRelease]:
    model.__ignore_data_scope__ = True
