# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 flow_add_seal
OPERATORS.register_module(
    module_name='FlowSealAddOperator',
    module_path="ops.user.flow_add_seal.process"
)