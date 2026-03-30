# -*- coding: utf-8 -*-
"""
MedCleanStd 医疗文本清洗标准化算子注册入口
"""

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='MedCleanStdMapper',
    module_path="ops.user.medcleanstd_operator.process"
)
