# -*- coding: utf-8 -*-
import importlib
import os
import sys
from pathlib import Path

from loguru import logger


# 获取当前目录
current_dir = os.path.dirname(__file__)

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
