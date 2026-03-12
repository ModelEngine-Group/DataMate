"""
System Parameter Model
系统参数模型
"""

from sqlalchemy import Column, String, Boolean, Text
from app.db.models.base_entity import BaseEntity


class SysParam(BaseEntity):
    """系统参数实体"""

    __tablename__ = "t_sys_param"
    __ignore_data_scope__ = True  # 系统参数不进行数据权限过滤

    id = Column(String(100), primary_key=True, comment="参数ID")
    param_value = Column(Text, nullable=False, comment="参数值")
    param_type = Column(
        String(50),
        nullable=False,
        default="string",
        comment="参数类型（string、integer、boolean）",
    )
    option_list = Column(
        Text, nullable=True, comment="选项列表（JSON格式，仅对enum类型有效）"
    )
    description = Column(String(255), nullable=True, default="", comment="参数描述")
    is_built_in = Column(Boolean, nullable=False, default=False, comment="是否内置")
    can_modify = Column(Boolean, nullable=False, default=True, comment="是否可修改")
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
