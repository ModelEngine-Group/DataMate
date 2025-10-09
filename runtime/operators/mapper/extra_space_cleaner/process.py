#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 多余空格去除
Create: 2025/01/13
"""
import logging as logger
import re
import time
from pathlib import Path
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class ExtraSpaceCleaner(Mapper):
    """去除多余空格、多余空行，包括文档首尾空格、首尾tab
    【注意】去除多余空格前，会先将文档中所有空格规范化为\u0020
    """

    def __init__(self, *args, **kwargs):
        # 匹配文档中非常见的unicode 空格
        super().__init__(*args, **kwargs)
        self.white_space_pattern = ('[\u00A0 \u1680 \u2000-\u200D \u2028-\u2029'
                                    ' \u202F \u205F \u3000 \u180E \u2060 \uFEFF]')
        self._file_path = Path(__file__).parent / 'resources' / 'special_token.txt'
        self.escaped_special_chars = self._get_escaped_special_chars()  # 加载标点符号
        # 匹配文章中，连续多个空格
        extra_space_pattern = r" {2,}"
        # 匹配多个空格、换行符混排情况
        extra_line_pattern = r"( |\n){2,}"
        # 匹配中文、符号间多余空格
        extra_space_in_chinese_pattern = r"(?<=[\u4e00-\u9fa5" + self.escaped_special_chars + r"]) +(?=[\u4e00-\u9fa5" \
                                         + self.escaped_special_chars + r"])"
        self.extra_space_re_compile = re.compile(extra_space_pattern)
        self.extra_space_in_chinese_re_compile = re.compile(extra_space_in_chinese_pattern)
        self.extra_line_re_compile = re.compile(extra_line_pattern)
        self.white_space_pattern_compile = re.compile(self.white_space_pattern)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._clean_extra_space(sample[self.text_key])
        logger.info("fileName: %s, method: ExtraSpaceCleaner costs %.6f s", sample[self.filename_key],
                    time.time() - start)
        return sample

    def _get_escaped_special_chars(self) -> str:
        with open(self._file_path, 'r', encoding='utf-8') as f:
            self._special_token = f.read().splitlines()
        res = ''.join([re.escape(char) for char in self._special_token])  # 将特殊字符转义并拼接成字符串
        return res

    def _clean_extra_space(self, input_data: str) -> str:
        # 将文档中非常见的 unicode 空格，如 u2008，转换为正常空格（半角空格）
        input_data = self.white_space_pattern_compile.sub('\u0020', input_data)
        # 移除文档首尾、句中或标点符号附近多余空格和 tab
        input_data = input_data.strip()
        # 逐行移除首尾空格
        text = "\n".join([line.strip() for line in input_data.split("\n")])
        text = ''.join(['【', text, '】'])
        # 连续空格替换为一个正常空格
        remove_extra_space = self.extra_space_re_compile.sub("\u0020", text)
        # 去除中文、符号间的空格
        remove_extra_space_in_chinese = self.extra_space_in_chinese_re_compile.sub("", remove_extra_space)
        # 去除连续换行符
        remove_duplicate_line = self.extra_line_re_compile.sub("\n", remove_extra_space_in_chinese)
        return remove_duplicate_line[1:-1]
