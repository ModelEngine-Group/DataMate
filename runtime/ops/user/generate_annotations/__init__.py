# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 annotation_gen_op
OPERATORS.register_module(
    module_name='AnnotationGenOperator', 
    module_path="ops.user.annotation_gen_op.process"
)