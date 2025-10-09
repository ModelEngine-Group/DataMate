#!/user/bin/python
# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文档特殊字符率检查
Create: 2023/11/7 9:26
"""
import time
import logging as logger

from pathlib import Path
from typing import Dict, Any

from data_platform.core.base_op import Filter


class FileWithHighSpecialCharRateFilter(Filter):
    """检查文档特殊字符率"""

    def __init__(self, *args, **kwargs):
        super(FileWithHighSpecialCharRateFilter, self).__init__(*args, **kwargs)
        self._min_threshold = kwargs.get("specialCharRatio", 0.3)  # 特殊字符占全文比例阈值，默认值为0.3
        self._file_path = Path(__file__).parent / 'resources' / 'special_token.txt'
        with open(self._file_path, 'r', encoding='utf-8') as f:
            self._special_token = set(f.read().splitlines())

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._file_with_high_special_char_rate_filter(sample[self.text_key],
                                                                              sample[self.filename_key])
        logger.info("fileName: %s, method: FileWithHighSpecialCharRateFilter costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _file_with_high_special_char_rate_filter(self, input_data: str, file_name):
        if not input_data:
            return ""

        output_data = input_data
        total = 0
        for token in self._special_token:
            total += input_data.count(token)

        special_char_rate = total / len(input_data)
        if special_char_rate >= self._min_threshold:
            logger.info("The special char rate of the input data is %s. Threshold is %s. "
                        "The document %s is filtered.", special_char_rate, self._min_threshold, file_name)
            output_data = ""
        return output_data
