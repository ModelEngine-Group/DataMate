# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 generate_annotations
OPERATORS.register_module(
    module_name='LoanSettlementAnnotationGenOperator',
    module_path="ops.user.loan_settlement_generate_annotations.process"
)