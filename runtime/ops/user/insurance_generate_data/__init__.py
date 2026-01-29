# -*- coding: utf-8 -*-
"""
社保数据生成算子
"""
from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='InsuranceDataGenOperator',
    module_path="ops.user.insurance_generate_data.process"
)
