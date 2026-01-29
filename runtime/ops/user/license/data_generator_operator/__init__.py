# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 data_generator_operator
OPERATORS.register_module(
    module_name='DataGeneratorOperator',
    module_path="ops.user.data_generator_operator.process"
)