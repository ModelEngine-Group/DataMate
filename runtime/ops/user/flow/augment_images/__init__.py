# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 augment_images
OPERATORS.register_module(
    module_name='FlowImgAugOperator',
    module_path="ops.user.augment_images.process"
)