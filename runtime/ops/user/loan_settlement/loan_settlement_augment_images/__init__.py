# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 augment_images
OPERATORS.register_module(
    module_name='LoanSettlementImgAugOperator',
    module_path="ops.user.loan_settlement_augment_images.process"
)