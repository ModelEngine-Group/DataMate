#!/usr/bin/python3
# -*- coding: utf-8 -*-


from typing import List

from loguru import logger
from datamate.common.utils.text_splitter import TextSplitter


class TextSegmentationOperator:
    def __init__(self, chunk_size, chunk_overlap):
        try:
            self.text_splitter = TextSplitter(-1, chunk_size, chunk_overlap)
        except Exception as err:
            logger.exception(f"init text splitter failed, error is： {err}")
            raise err

    def process(self, input_data: str) -> List[str]:
        if input_data.strip() == "":
            logger.info("input text is empty, return empty chunks.")
            return []
        return self.text_splitter.split_text(input_data)
