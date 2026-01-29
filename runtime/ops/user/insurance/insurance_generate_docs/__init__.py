# -*- coding: utf-8 -*-
"""
社保文档生成算子
"""
from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='InsuranceDocGenOperator',
    module_path="ops.user.insurance_generate_docs.process"
)
