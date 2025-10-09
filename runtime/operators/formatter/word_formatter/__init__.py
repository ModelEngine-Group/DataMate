# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.


from data_platform.core.base_op import OPERATORS

OPERATORS.register_module(module_name='WordFormatter',
                          module_path="ops.formatter.word_formatter.process")
