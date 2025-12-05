#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: URL网址匿名化
Create: 2024/12/26 15:43
"""
import re
import time
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


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
        self.read_file_first(sample)
        sample[self.text_key] = self._url_filter(sample[self.text_key])
        logger.info(f"fileName: {sample[self.filename_key]}, method: UrlCleaner costs {time.time() - start:6f} s")
        return sample

    def _url_filter(self, input_data: str):
        input_data = ''.join(['【', input_data, '】'])
        text = self.url_re_compile.sub("<url>", input_data)
        return text[1:-1]
