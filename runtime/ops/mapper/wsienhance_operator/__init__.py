# -*- coding: utf-8 -*-
"""
WSIEnhance WSI 智能增强分析算子注册入口
"""

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='WSIEnhanceMapper',
    module_path="ops.user.wsienhance_operator.process"
)
