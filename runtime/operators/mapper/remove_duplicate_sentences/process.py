#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文档局部内容去重
Create: 2025/01/07
"""

import logging as logger
import re
import time
from collections import Counter
from typing import Dict, Any

from data_platform.core.base_op import Filter


def duplicate_sentences_filter(input_data: str, file_name: str, duplicate_th: int = 5) -> str:
    """ 文本局部内容去重：去除某些重复出现的段落或句子
    以段落为基本单位，去除重复次数超过规定阈值的段落, 只保留第一次出现的段落的原始内容, 且不去除段落的首尾空格。

    Args:
        input_data: 输入数据
        file_name: 文件名称
        duplicate_th: 最大重复次数阈值，默认小于5次
    Returns:
        str: 清洗后数据
    """
    paragraphs = input_data.split("\n")
    trust_set = {'<table>', '<tbody>', '<tr>', '<td>', '</table>', '</tbody>', '</tr>', '</td>', ""}

    # 进行一次遍历，记录每个段落的出现位置
    order_paragraphs = []
    paragraph_counts = Counter([line.strip() for line in re.split("\\n", input_data)])

    try:
        for paragraph in paragraphs:
            # trust_set 中的元素不纳入统计
            if paragraph.strip() in trust_set:
                order_paragraphs.append(paragraph)
                continue
            paragraph_strip = paragraph.strip()
            if duplicate_th > paragraph_counts[paragraph_strip] >= 0:
                order_paragraphs.append(paragraph)
            elif paragraph_counts[paragraph_strip] >= duplicate_th:
                order_paragraphs.append(paragraph)
                paragraph_counts[paragraph_strip] = -1

    except Exception as err:
        logger.error("fileName: %s, method: RemoveDuplicateSentencess. An error occurred when using "
                     "filtering duplicate sentences. The error is: %s", file_name, err, exc_info=True)
        return input_data

    # 将去重后的段落重新组合成文本
    result_text = '\n'.join(order_paragraphs)
    return result_text


class DuplicateSentencesFilter(Filter):
    """文档局部内容去重插件"""

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        duplicate_th = 5  # 段落重复次数阈值
        file_name = sample[self.filename_key]
        start = time.time()
        sample[self.text_key] = duplicate_sentences_filter(sample[self.text_key], file_name, duplicate_th)
        logger.info("fileName: %s, RemoveDuplicateSentencess costs %.6f s", file_name,
                    time.time() - start)
        return sample
