# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注意：这里的 'generate_docs' 必须是你打包时的文件夹名称
OPERATORS.register_module(
    module_name='DocGenOperator', 
    module_path="ops.user.generate_docs.process"
)