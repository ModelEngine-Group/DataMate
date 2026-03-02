# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册该算子，确保 path 指向当前文件夹名 video_analysis_operator
OPERATORS.register_module(
    module_name='VideoAnalysisOperator',
    module_path="ops.user.video_analysis_operator.process"
)