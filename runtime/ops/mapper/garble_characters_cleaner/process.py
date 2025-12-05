#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description:
    本插件实现将文档中乱码去除功能
    实现逻辑：
        1. 正则判断该字符的unicode编码是否在乱码范围内。若在范围内，则去除，不在范围内，则保留。
        2. 运行前，加载乱码字符范围的配置文件，即charset.json。该json文件中，key为字符集名称，value为unicode编码范围的集合。

Create: 2025/01/13
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class GrableCharactersCleaner(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_path = str(Path(__file__).parent / 'resources' / 'charset.json')
        self.unicode_grable_code_list = self.get_unicode_grable_code_list()  # 乱码unicode编码的十进制范围的集合
        self.grable_re_compile = re.compile("[" + self.unicode_grable_code_list + "]")

    def get_unicode_grable_code_list(self):
        """获取乱码unicode编码范围"""
        res = ""
        with open(self._file_path, 'r', encoding='utf-8') as f:
            charset_number_list = json.load(f)
        for number_ranges in charset_number_list.values():
            for number_range in number_ranges:
                number_range_list = number_range.split(",")
                if len(number_range_list) < 2:
                    logger.error(f"number_range_list size is {len(number_range_list)}, formatting error")
                    continue
                res += number_range_list[0] + "-" + number_range_list[1]
        return res

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._grable_characters_filter(sample[self.text_key])
        logger.info(
            f"fileName: {sample[self.filename_key]}, method: GrableCharactersCleaner costs {time.time() - start:6f} s")
        return sample

    def _grable_characters_filter(self, input_data: str):
        """去除文档中的乱码"""
        return self.grable_re_compile.sub("", input_data)
