# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
since:  
"""

from data_platform.core.base_op import OPERATORS

OPERATORS.register_module(module_name='QAConditionEvaluator',
                          module_path="ops.llms.qa_condition_evaluator.process")
