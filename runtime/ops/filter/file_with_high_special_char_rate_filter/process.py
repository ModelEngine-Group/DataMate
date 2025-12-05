#!/user/bin/python
# -- encoding: utf-8 --

"""
Description: 文档特殊字符率检查
Create: 2023/11/7 9:26
"""
import time

from pathlib import Path
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Filter


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
        self.read_file_first(sample)
        sample[self.text_key] = self._file_with_high_special_char_rate_filter(sample[self.text_key],
                                                                              sample[self.filename_key])
        logger.info(f"fileName: {sample[self.filename_key]}, "
                    f"method: FileWithHighSpecialCharRateFilter costs {(time.time() - start):6f} s")
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
            logger.info(f"The special char rate of the input data is {special_char_rate}. "
                        f"Threshold is {self._min_threshold}. The document {file_name} is filtered.")
            output_data = ""
        return output_data
