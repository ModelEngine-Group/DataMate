# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 image_composer_operator
OPERATORS.register_module(
    module_name='LicenseImageComposerOperator',
    module_path="ops.user.license_image_composer_operator.process"
)