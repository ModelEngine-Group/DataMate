#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文档目录去除
Create: 2025/01/13
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class ContentCleaner(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.no_content_count = 3  # 连续不符合目录结构的行数阈值
        # 目录标题
        self.content_text_pattern = r"^ *(目 *录|CONTENT(S)?) *$"
        # 目录行 前缀格式
        self.content_preface_pattern = r"^ *(前言|About This Document|\d+(\.\d+)*|[a-zA-Z]+(\.\d+)*)"
        # 目录行 中间格式
        self.content_middle_pattern = r"\.{7,}"
        # 目录行 结尾格式
        self.content_end_pattern = r"(\d|错误!未定义书签。|[IXV]+) *$"
        self.content_pattern = self.content_preface_pattern + ".*" + self.content_end_pattern

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._content_filter(sample[self.text_key])
        logger.info("fileName: %s, method: ContentCleaner costs %.6f s", sample[self.filename_key],
                    time.time() - start)
        return sample

    def _content_filter(self, input_data: str):
        count = 0  # 记录不符合目录结构的次数，连续3行不满足要求，则认为已经进入正文
        # 目录起始和结束索引
        content_start_index, content_end_index = -1, -1
        lines = input_data.split("\n")
        for i, line in enumerate(lines):
            if content_start_index >= 0 and count >= self.no_content_count:
                break
            # 首先匹配目录或content字眼
            if content_start_index < 0 and re.match(self.content_text_pattern, line, re.IGNORECASE):
                content_start_index = i
                content_end_index = i
            # 匹配两种形式的目录行
            # 1. 以指定格式开始、指定格式结尾；2.该行包含点数量超过7个
            elif content_start_index >= 0 and (re.match(self.content_pattern, line, re.IGNORECASE)
                                               or re.search(self.content_middle_pattern, line)):
                content_end_index = i
                count = 0
            elif content_start_index >= 0 and not (re.match(self.content_pattern, line, re.IGNORECASE)
                                                   or re.search(self.content_middle_pattern, line)):
                count += 1

        if 0 <= content_start_index < content_end_index:
            res = "\n".join(lines[:content_start_index] + lines[content_end_index + 1:])
        else:
            # 只有目录关键字时，关键字不去除;或不符合目录结构，返回原文
            res = "\n".join(lines)
        return res
