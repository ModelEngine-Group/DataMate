from sqlalchemy import Column, String, TIMESTAMP
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
