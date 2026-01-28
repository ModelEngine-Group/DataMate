# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 注意：module_name 必须与 metadata.yml 中的 raw_id 一致
# module_path 中的 'doc_to_img_op' 必须与打包文件夹名称一致
OPERATORS.register_module(
    module_name='DocToImgOperator', 
    module_path="ops.user.doc_to_img_op.process"
)