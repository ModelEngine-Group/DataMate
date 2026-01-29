# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 注意：module_name 必须与 metadata.yml 中的 raw_id 一致
# module_path 中的 'tax_generate_data' 必须与打包文件夹名称一致
OPERATORS.register_module(
    module_name='TaxDataGeneratorOperator',
    module_path="ops.user.tax_generate_data.process"
)
