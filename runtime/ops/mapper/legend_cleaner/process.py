#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: 图注表注去除
Create: 2024/12/5 15:43
"""
import re
import time
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class LegendCleaner(Mapper):
    @staticmethod
    def _get_legend_re_compile():
        chinese_legend_prefix = r"(图|表|图片|表格)"
        chinese_legend_number = r"(\d+((\.|-)\d+)*|[a-zA-Z]{1,2}((\.|-)\d+)*)"
        chinese_legend_pattern = r"(?<=\n)" + chinese_legend_prefix + "( )*" + chinese_legend_number + " +.*\n"
        english_legend_pattern = r"(Figure|Table|Fig\.?)"
        english_legend_number = r"(S?\d+((\.|-)\d+)*|[a-zA-Z]{1,2}\d?((\.|-)\d+)*)"
        english_legend_pattern = (r"(?<=\n)" + english_legend_pattern + "( )*"
                                  + english_legend_number + r"(\.|:)? +.*\n")
        legend_re_compile = re.compile('|'.join([chinese_legend_pattern, english_legend_pattern]), re.IGNORECASE)
        return legend_re_compile

    @classmethod
    def _clean_html_tag(cls, input_data: str):
        """移除文档中图注表注等"""
        input_data = ''.join(['\n', input_data, '\n'])
        text = cls._get_legend_re_compile().sub("", input_data)
        return text[1:-1]

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._clean_html_tag(sample[self.text_key])
        logger.info(f"fileName: {sample[self.filename_key]}, method: LegendCleaner costs {time.time() - start:6f} s")
        return sample
