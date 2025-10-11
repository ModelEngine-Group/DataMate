#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 全角转半角
Create: 2025/01/13
"""
import logging as logger
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class FullWidthCharacterCleaner(Mapper):
    """将文档中的所有全角字符转换成半角字符"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_to_half_dict = {
            '＂': '"', '＃': '#', '＄': '$', '％': '%', '＆': '&', '＇': "'", '＊': '*', '＋': '+',
            '－': '-', '．': '.', '／': '/', '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9', '＜': '<', '＝': '=', '＞': '>',
            '＠': '@', 'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G',
            'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
            'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W',
            'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z', '［': '[', '＼': '\\', '］': ']', '＾': '^', '＿': '_',
            '｀': '`', 'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g',
            'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
            'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w',
            'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z', '｛': '{', '｜': '|', '｝': '}', '～': '~'
        }

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._full_width_character_filter(sample[self.text_key])
        logger.info("fileName: %s, method: FullWidthCharactersCleaner costs %.6f s" % (
            sample[self.filename_key], time.time() - start
        ))
        return sample

    def _full_width_character_filter(self, input_data: str):
        res = []
        for input_str in input_data.split('\n'):
            res.append("".join(self._full_to_half_dict.get(char, char) for char in input_str))
        return '\n'.join(res)
