#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: MinerU PDF文本抽取
Create: 2025/10/29 17:24
"""
import json
import time
from loguru import logger
from typing import Dict, Any

from datamate.core.base_op import Mapper
from datamate.common.utils.rest_client import http_request


class MineruFormatter(Mapper):
    """基于外部API，抽取PDF中的文本"""

    def __init__(self, *args, **kwargs):
        super(MineruFormatter, self).__init__(*args, **kwargs)
        self.base_url = "http://datamate-mineru:9001"
        self.pdf_extract_url = f"{self.base_url}/api/pdf-extract"

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        filename = sample[self.filename_key]
        try:
            data = {"source_path": sample[self.filepath_key], "export_path": sample[self.export_path_key]}
            response = http_request(method="POST", url=self.pdf_extract_url, data=data)
            sample[self.text_key] = json.loads(response.text).get("result")
            logger.info(
                f"fileName: {filename}, method: MineruFormatter costs {(time.time() - start):6f} s")
        except UnicodeDecodeError as err:
            logger.exception(f"fileName: {filename}, method: MineruFormatter causes decode error: {err}")
            raise
        return sample
