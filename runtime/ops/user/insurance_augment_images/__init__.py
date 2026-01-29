# -*- coding: utf-8 -*-
"""
图片增强合成算子
"""
from datamate.core.base_op import OPERATORS

# 注册算子
# 注意：module_name 必须与 metadata.yml 中的 raw_id 一致
OPERATORS.register_module(
    module_name='InsuranceImgAugOperator',
    module_path="ops.user.insurance_augment_images.process"
)
