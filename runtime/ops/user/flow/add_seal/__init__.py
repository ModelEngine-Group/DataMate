# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 add_seal
OPERATORS.register_module(
    module_name='SealAddOperator',
    module_path="ops.user.add_seal.process"
)