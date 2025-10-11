# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2023/11/7 9:26
"""
import json
import time
from typing import Dict, Any

from loguru import logger

from data_platform.core.base_op import Mapper

from .knowledge_relation import get_json_list

# 切片长度
CHUNK_SIZE = 500
# 相邻切片重合长度
OVERLAP_SIZE = 100


class KnowledgeRelationSlice(Mapper):
    def __init__(self, *args, **kwargs):
        super(KnowledgeRelationSlice, self).__init__(*args, **kwargs)
        if 'chunk_size' not in kwargs:
            self.chunk_size = CHUNK_SIZE
        else:
            self.chunk_size = kwargs.get("chunk_size")

        if 'overlap_size' not in kwargs:
            self.overlap_size = OVERLAP_SIZE
        else:
            self.overlap_size = kwargs.get("overlap_size")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()

        chunk_item = get_json_list(sample[self.text_key], chunk_size=self.chunk_size, overlap_size=self.overlap_size)
        chunk_item_json = json.dumps(chunk_item, ensure_ascii=False)
        sample[self.text_key] = chunk_item_json

        cost_time = time.time() - start_time
        logger.info(f'Generate knowledgeRelation slice num: {len(chunk_item)}, Cost time: {cost_time} s')

        return sample
