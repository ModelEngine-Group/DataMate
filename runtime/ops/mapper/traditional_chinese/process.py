#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: 繁体转简体
Create: 2025/01/15
"""
import time
from typing import Dict, Any

from zhconv import convert
from loguru import logger

from datamate.core.base_op import Mapper


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
        self.read_file_first(sample)
        sample[self.text_key] = self._traditional_chinese_filter(sample[self.text_key])
        logger.info(
            f"fileName: {sample[self.filename_key]}, method: TraditionalChinese costs {time.time() - start:6f} s")
        return sample
