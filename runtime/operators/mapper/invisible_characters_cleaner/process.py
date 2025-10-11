#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 不可见字符去除
Create: 2025/01/13
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class InvisibleCharactersCleaner(Mapper):
    @staticmethod
    def _invisible_characters_filter(input_data: str):
        # 移除ASCII中不可见字符，包括0-7、14-19 21-31、127-160的字符
        invisible_char_pattern = '[\x00-\x07|\x0E-\x13|\x15-\x1F|\x7F-\xA0]'
        invisible_chars_re = re.compile(invisible_char_pattern)
        return invisible_chars_re.sub('', input_data)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._invisible_characters_filter(sample[self.text_key])
        logger.info("fileName: %s, method: InvisibleCharactersCleaner costs %.3f s",
                    sample[self.filename_key], time.time() - start)
        return sample
