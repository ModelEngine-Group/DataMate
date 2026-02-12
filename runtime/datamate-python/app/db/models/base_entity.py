from sqlalchemy import Column, String, TIMESTAMP, Text, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BaseEntity(Base):
    """
    Common base entity with audit fields.
    Subclasses may set `__ignore_data_scope__ = True` to opt-out of data-scope filtering.
    """
    __abstract__ = True

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(),
                        comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")

    # default: do enforce data scope unless subclass sets this to True
    __ignore_data_scope__ = False


class LineageNode(Base):
    """数据血缘：节点表（实体对象）"""

    __tablename__ = "t_lineage_node"

    id = Column(String(36), primary_key=True, comment="节点ID")
    graph_id = Column(String(36), nullable=True, comment="图ID")
    node_type = Column(String(64), nullable=False, comment="节点类型")
    name = Column(String(256), nullable=False, comment="节点名称")
    description = Column(Text, nullable=True, comment="节点描述")
    node_metadata = Column(Text, nullable=True, comment="节点扩展信息（JSON）")


class LineageEdge(Base):
    """数据血缘：边表（处理流程）"""

    __tablename__ = "t_lineage_edge"

    id = Column(String(36), primary_key=True, comment="边ID")
    graph_id = Column(String(36), nullable=True, comment="图ID")
    process_id = Column(String(36), nullable=True, comment="处理流程ID")
    edge_type = Column(String(64), nullable=False, comment="边类型")
    name = Column(String(256), nullable=True, comment="边名称")
    description = Column(Text, nullable=True, comment="边描述")
    edge_metadata = Column(Text, nullable=True, comment="边扩展信息（JSON）")
    from_node_id = Column(String(36), nullable=False, comment="源节点ID")
    to_node_id = Column(String(36), nullable=False, comment="目标节点ID")
