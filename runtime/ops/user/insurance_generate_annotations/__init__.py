# -*- coding: utf-8 -*-
"""
QA对生成算子
"""
from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='InsuranceAnnotationGenOperator',
    module_path="ops.user.insurance_generate_annotations.process"
)
