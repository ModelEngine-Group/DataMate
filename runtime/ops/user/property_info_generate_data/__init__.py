# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册不动产数据生成算子
# 注意：module_path 中的 'property_info_generate_data' 必须与压缩包名称一致
OPERATORS.register_module(
    module_name="PropertyDataGeneratorMapper",
    module_path="ops.user.property_info_generate_data.process",
)
