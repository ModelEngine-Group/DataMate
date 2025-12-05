#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: 不可见字符去除
Create: 2025/01/13
"""
import re
import time
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class InvisibleCharactersCleaner(Mapper):
    @staticmethod
    def _invisible_characters_filter(input_data: str):
        # 移除ASCII中不可见字符，包括0-7、14-19 21-31、127-160的字符
        invisible_char_pattern = '[\x00-\x07|\x0E-\x13|\x15-\x1F|\x7F-\xA0]'
        invisible_chars_re = re.compile(invisible_char_pattern)
        return invisible_chars_re.sub('', input_data)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._invisible_characters_filter(sample[self.text_key])
        logger.info(f"fileName: {sample[self.filename_key]}, "
                    f"method: InvisibleCharactersCleaner costs {time.time() - start:6f} s")
        return sample
