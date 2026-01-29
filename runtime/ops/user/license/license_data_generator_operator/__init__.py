# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 data_generator_operator
OPERATORS.register_module(
    module_name='LicenseDataGeneratorOperator',
    module_path="ops.user.license_data_generator_operator.process"
)