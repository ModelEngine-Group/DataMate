#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 空格标准化
Create: 2025/01/15
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class UnicodeSpaceCleaner(Mapper):
    @classmethod
    def _clean_unicode_space(cls, input_data: str):
        """将文档中不同的 unicode 空格，如 u2008，转换为正常空格（半角空格）"""
        white_space_pattern = '[\u00A0 \u1680 \u2000-\u200D \u2028-\u2029 \u202F \u205F \u3000 \u180E \u2060 \uFEFF]'
        return re.compile(white_space_pattern).sub('\u0020', input_data)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._clean_unicode_space(sample[self.text_key])
        logger.info("fileName: %s, method: UnicodeSpaceCleaner costs %.6f s" % (
            sample[self.filename_key], time.time() - start
        ))
        return sample
