# -*- coding: utf-8 -*-
"""
收入证明生成算子 - DataMate算子注册
"""

from datamate.core.base_op import OPERATORS

# 注册算子到DataMate系统
# module_name: 必须与metadata.yml中的raw_id和process.py中的类名一致
# module_path: 算子process.py的导入路径
OPERATORS.register_module(
    module_name='IncomeCertificateGenerator',
    module_path="ops.user.income_certificate_generator.process"
)
