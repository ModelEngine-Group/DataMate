#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文档表情去除
Create: 2023/12/7 15:43
"""
import time
import logging as logger
from typing import Dict, Any

import emoji

from data_platform.core.base_op import Mapper


class EmojiCleaner(Mapper):
    @staticmethod
    def _emoji_filter(input_data: str):
        res = []
        for input_s in input_data.split('\n'):
            res.append(emoji.replace_emoji(input_s, replace=''))
        return '\n'.join(res)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._emoji_filter(sample[self.text_key])
        logger.info("fileName: %s, method: EmojiCleaner costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample
