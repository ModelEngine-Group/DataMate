# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注意：这里的 'tax_generate_docs' 必须是你打包时的文件夹名称
OPERATORS.register_module(
    module_name='TaxDocGenOperator',
    module_path="ops.user.tax_generate_docs.process"
)