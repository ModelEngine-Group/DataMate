#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 繁体转简体
Create: 2025/01/15
"""
import logging as logger
import time
from typing import Dict, Any

from zhconv import convert

from data_platform.core.base_op import Mapper


class TraditionalChineseCleaner(Mapper):
    """繁体转简体过滤插件"""

    @staticmethod
    def _traditional_chinese_filter(input_data: str):
        """ 繁体转简体"""
        res = []
        for input_str in input_data.split('\n'):
            res.append(convert(input_str, 'zh-hans'))
        return '\n'.join(res)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._traditional_chinese_filter(sample[self.text_key])
        logger.info("fileName: %s, method: TraditionalChinese costs %.6f s" % (
            sample[self.filename_key], time.time() - start
        ))
        return sample
