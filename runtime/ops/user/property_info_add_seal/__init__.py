# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册不动产盖章算子
# 注意：module_path 中的 'property_info_add_seal' 必须与压缩包名称一致
OPERATORS.register_module(
    module_name="PropertySealMapper",
    module_path="ops.user.property_info_add_seal.process",
)
