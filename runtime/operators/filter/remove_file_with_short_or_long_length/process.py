#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 词数目不在指定范围会被过滤掉（支持自定义阈值）
Create: 2025/01/16
"""

import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Filter


class FileWithShortOrLongLengthFilter(Filter):
    """检查文档字数目，词数目不在指定范围会被过滤掉（支持自定义阈值）"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        file_length_list = kwargs.get("fileLength", [10, 10000000])  # [下限，上限]，默认字数下限为10, 默认字数上限为10000000
        if len(file_length_list) != 2:  # 要求传入字数目上限和字数目下限
            logger.error("method: FileWithShortOrLongLengthFilter expected 2 arguments, got %d",
                         len(file_length_list))
            raise RuntimeError(82001, "method: FileWithShortOrLongLengthFilter expected 2 arguments") from None
        # 用户不输入下限参数时前端传入''，则不对字数目下限控制
        self._file_minimum_length = 0 if not file_length_list[0] else file_length_list[0]
        # 用户不输入上限参数时前端传入''，则不对字数目上限控制
        self._file_maximum_length = float("inf") if not file_length_list[1] else file_length_list[1]

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._file_with_short_or_long_length_filter(sample[self.text_key],
                                                                            sample[self.filename_key])
        logger.info("fileName: %s, method: FileWithShortOrLongLengthFilter costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _strip_unicode_whitespace(self, text: str):
        # 常见 Unicode 空格符（涵盖普通空格、全角空格、零宽空格等）
        pattern = r'[\u0020\u00A0\u1680\u2000-\u200F\u202F\u205F\u3000]+'
        # 匹配首尾的空格符
        pattern = fr'^{pattern}|{pattern}$'
        return re.sub(pattern, '', text)

    def _file_with_short_or_long_length_filter(self, input_data: str, file_name):
        input_data_tmp = self._strip_unicode_whitespace(input_data)
        if len(input_data_tmp) < self._file_minimum_length or len(input_data_tmp) > self._file_maximum_length:
            logger.info("The length of input_data is: %s, which is not within the threshold range of %s and %s. "
                        "%s is filtered.", len(input_data_tmp), self._file_minimum_length, self._file_maximum_length,
                        file_name)
            return ""
        return input_data
