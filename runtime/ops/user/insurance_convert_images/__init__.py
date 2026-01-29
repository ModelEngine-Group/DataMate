# -*- coding: utf-8 -*-
"""
图片转换模块 - 将Word文档转换为JPG图片
"""
from datamate.core.base_op import OPERATORS

# 注册算子
OPERATORS.register_module(
    module_name='InsuranceDocToImgOperator',
    module_path="ops.user.insurance_convert_images.process"
)
