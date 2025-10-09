#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: URL网址匿名化
Create: 2024/12/26 15:43
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class AnonymizedUrlCleaner(Mapper):
    """将文档中的网址匿名化"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_pattern = r'((?:(?:https?|ftp|file)://|(?<![a-zA-Z\-\.])www\.)' \
                           r'[\-A-Za-z0-9\+&@\(\)#/%\?=\^~_|!:\,\.\;]+[\-A-Za-z0-9\+&@#/%=\~_\|])' \
                           r'(?![\-A-Za-z0-9\+&@#/%=\~_\|])'
        self.url_re_compile = re.compile(self.url_pattern, re.MULTILINE)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._url_filter(sample[self.text_key])
        logger.info("fileName: %s, method: UrlCleaner costs %.6f s", sample[self.filename_key],
                    time.time() - start)
        return sample

    def _url_filter(self, input_data: str):
        input_data = ''.join(['【', input_data, '】'])
        text = self.url_re_compile.sub("<url>", input_data)
        return text[1:-1]
