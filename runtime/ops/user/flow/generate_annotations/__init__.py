# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 generate_annotations
OPERATORS.register_module(
    module_name='FlowQAGenOperator',
    module_path="ops.user.generate_annotations.process"
)