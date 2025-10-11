#!/user/bin/python
# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 检查文档字重复率插件
Create: 2023/11/7 9:26
"""
import re
import time
import logging as logger

from collections import Counter
from typing import Dict, Any

from data_platform.core.base_op import Filter


class FileWithHighRepeatWordRateFilter(Filter):
    """检查文档字重复率插件"""

    def __init__(self, *args, **kwargs):
        super(FileWithHighRepeatWordRateFilter, self).__init__(*args, **kwargs)
        self._min_threshold = kwargs.get("repeatWordRatio", 0.5)  # 重复字符占整行的比例阈值，默认值为0.5

    @staticmethod
    def _extract_word(input_data):
        # 只统计中文字的重复率
        extracted_word = re.sub(r'[^\u4e00-\u9fff]', '', input_data)
        return extracted_word

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._file_with_high_repeat_word_rate_filter(sample[self.text_key],
                                                                             sample[self.filename_key])
        logger.info("fileName: %s, method: FileWithHighRepeatWordRateFilter costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _file_with_high_repeat_word_rate_filter(self, input_data: str, file_name):
        tmp = self._extract_word(input_data)
        if not tmp:
            return input_data
        output_data = input_data
        words_count = Counter(tmp)
        max_value = max(words_count.values())
        repeat_word_rate = max_value / len(tmp)
        if repeat_word_rate >= self._min_threshold:
            output_data = ""
            logger.info("The repeat word rate of the input data is %s. Threshold is %s. "
                        "The document %s is filtered.", repeat_word_rate, self._min_threshold, file_name)
        return output_data
