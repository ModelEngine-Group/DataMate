# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 假设算子包名为 seal_generator
# 请确保打包时的 zip 文件名为 seal_generator.zip
OPERATORS.register_module(
    module_name='LoanSettlementSealGeneratorMapper',
    module_path="ops.user.loan_settlement_seal_generator.process"
)