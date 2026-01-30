# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册不动产文档生成算子
# 注意：module_path 中的 'property_info_generate_doc' 必须与压缩包名称一致
OPERATORS.register_module(
    module_name="PropertyDocFillerMapper",
    module_path="ops.user.property_info_generate_doc.process",
)
