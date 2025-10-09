# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

import os
import importlib
import sys
from pathlib import Path

from loguru import logger

from data_platform.common.utils.custom_importer import CustomImporter

# 获取当前目录
current_dir = os.path.dirname(__file__)

base_path = Path(__file__).resolve().parent
sys.meta_path.append(CustomImporter(base_path))

# 遍历子目录
for module_name in os.listdir(current_dir):
    module_path = os.path.join(current_dir, module_name)
    # 检查是否是目录且包含 __init__.py
    if os.path.isdir(module_path) and '__init__.py' in os.listdir(module_path):
        # 动态导入模块
        try:
            importlib.import_module(f".{module_name}", package=__name__)
        except Exception as e:
            logger.error(f"Failed to load Ops {module_name}")
