#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文本切分算子
Create: 2023/11/09 10:17
"""

import random
from typing import List, Dict, Any

from loguru import logger

from data_platform.common.utils.text_splitter import TextSplitter
from data_platform.core.base_op import Slicer


class TextSegmentationOperator:
    def __init__(self, max_characters, chunk_size, chunk_overlap):
        try:
            self.text_splitter = TextSplitter(max_characters, chunk_size, chunk_overlap)
        except Exception as err:
            logger.error("init text splitter failed, error is： %s", err, exc_info=True)
            raise Exception(83001, "init text splitter failed") from None

    def process(self, input_data: str) -> List[str]:
        if input_data.strip() == "":
            logger.info("input text is empty, return empty chunks.")
            return []
        return self.text_splitter.split_text(input_data)


class Segmentation(Slicer):
    """切片算法插件"""

    def __init__(self, *args, **kwargs):
        super(Segmentation, self).__init__(*args, **kwargs)
        self.max_characters = kwargs.get("maxCharacters", -1)
        self.chunk_size = kwargs.get("chunkSize", 800)
        self.chunk_overlap = kwargs.get("chunkOverlap", 100)
        self.slice_num = kwargs.get("sliceNum", 5)
        self.op = TextSegmentationOperator(self.max_characters, self.chunk_size, self.chunk_overlap)
        self.last_ops = True

    def execute(self, sample: Dict[str, Any]) -> List[Dict]:

        try:
            chunks = self.op.process(sample[self.text_key])
        except Exception as err:
            logger.error("split text failed, error is: %s", err, exc_info=True)
            raise Exception(83002, "init text splitter failed") from None
        num_to_sample = min(self.slice_num, len(chunks))
        sampled_indices = random.sample(chunks, num_to_sample)
        for idx, chunk in enumerate(sampled_indices):
            temp_sample = {self.text_key: chunk, self.data_key: "", self.export_path_key: sample[self.export_path_key],
                           self.filename_key: sample[self.filename_key], self.fileid_key: sample[self.fileid_key],
                           "sequenceId": str(idx), "chunkSize": str(len(chunk))}
            self.save_patch_sample(temp_sample, idx, save_format="text")

        sample["fileNum"] = len(chunks)
        sample[self.text_key] = "Success"

        return [sample]
