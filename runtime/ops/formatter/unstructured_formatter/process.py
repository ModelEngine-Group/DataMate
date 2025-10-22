
#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: 非结构化文本抽取
Create: 2025/10/22 15:15
"""
import time
from typing import Dict, Any

from loguru import logger
from unstructured.partition.auto import partition

from datamate.core.base_op import Mapper


class UnstructuredFormatter(Mapper):
    """把输入的非结构化文本抽取为txt"""

    def __init__(self, *args, **kwargs):
        super(UnstructuredFormatter, self).__init__(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        filepath = sample.get(self.filepath_key)
        filename = sample.get(self.filename_key)
        try:
            elements = partition(filename=filepath)
            sample[self.text_key] = "\n\n".join([str(el) for el in elements])
            logger.info(f"fileName: {filename}, method: UnstructuredFormatter costs {(time.time() - start):6f} s")
        except UnicodeDecodeError as err:
            logger.exception(f"fileName: {filename}, method: UnstructuredFormatter causes decode error: {err}")
            raise
        return sample
