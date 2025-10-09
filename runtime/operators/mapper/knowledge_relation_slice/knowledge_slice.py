#!/usr/bin/python3
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

from typing import List

from loguru import logger
from data_platform.common.utils.text_splitter import TextSplitter


class TextSegmentationOperator:
    def __init__(self, chunk_size, chunk_overlap):
        try:
            self.text_splitter = TextSplitter(-1, chunk_size, chunk_overlap)
        except Exception as err:
            logger.error("init text splitter failed, error is： %s", err, exc_info=True)
            raise err

    def process(self, input_data: str) -> List[str]:
        if input_data.strip() == "":
            logger.info("input text is empty, return empty chunks.")
            return []
        return self.text_splitter.split_text(input_data)
