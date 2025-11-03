"""
Tables for Ratio (Data Synthesis Ratio) module

Derived from scripts/db/data-ratio-init.sql
 - t_st_ratio_instances
 - t_st_ratio_relations
"""

import uuid
from sqlalchemy import Column, String, Text, BigInteger, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class RatioInstance(Base):
    """配比实例表（UUID 主键） -> t_st_ratio_instances

    Columns per data-ratio-init.sql:
      id, name, description, target_dataset_id, ratio_method, ratio_parameters,
      merge_method, status, totals, created_at, updated_at, created_by, updated_by
    """

    __tablename__ = "t_st_ratio_instances"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(64), nullable=True, comment="名称")
    description = Column(Text, nullable=True, comment="描述")
    target_dataset_id = Column(String(64), nullable=True, comment="模板数据集ID")
    ratio_method = Column(String(50), nullable=True, comment="配比方式，按标签（TAG）,按数据集（DATASET）")
    ratio_parameters = Column(JSON, nullable=True, comment="配比参数")
    merge_method = Column(String(50), nullable=True, comment="合并方式")
    status = Column(String(20), nullable=True, comment="状态")
    totals = Column(BigInteger, nullable=True, comment="总数")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column( TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

    def __repr__(self) -> str:
        return f"<RatioInstance(id={self.id}, name={self.name}, method={self.ratio_method}, status={self.status})>"


class RatioRelation(Base):
    """配比关系表（UUID 主键） -> t_st_ratio_relations

    Columns per data-ratio-init.sql:
      id, ratio_instance_id, source_dataset_id, ratio_value, counts, filter_conditions,
      created_at, updated_at, created_by, updated_by
    """

    __tablename__ = "t_st_ratio_relations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    ratio_instance_id = Column(String(64), nullable=False, comment="配比实例ID")
    source_dataset_id = Column(String(64), nullable=True, comment="源数据集ID")
    ratio_value = Column(String(256), nullable=True)
    counts = Column(BigInteger, nullable=True, comment="条数")
    filter_conditions = Column(Text, nullable=True, comment="过滤条件")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

    def __repr__(self) -> str:
        return (
            f"<RatioRelation(id={self.id}, ratio_instance_id={self.ratio_instance_id}, "
            f"source_dataset_id={self.source_dataset_id}, counts={self.counts})>"
        )

