# -*- coding: utf-8 -*-
"""
WSIEnhance 全幻灯片成像处理算子注册入口
"""

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='WSIEnhanceMapper',
    module_path="ops.user.wsi_enhance_operator.process"
)
