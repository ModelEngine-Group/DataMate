# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 generate_data
OPERATORS.register_module(
    module_name='FlowDataGenOperator',
    module_path="ops.user.flow_generate_data.process"
)