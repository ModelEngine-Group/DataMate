
"""
Description: 文档表情去除
Create: 2023/12/7 15:43
"""
import time
from typing import Dict, Any

import emoji
from loguru import logger

from datamate.core.base_op import Mapper


class EmojiCleaner(Mapper):
    @staticmethod
    def _emoji_filter(input_data: str):
        res = []
        for input_s in input_data.split('\n'):
            res.append(emoji.replace_emoji(input_s, replace=''))
        return '\n'.join(res)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._emoji_filter(sample[self.text_key])
        logger.info(f"fileName: {sample[self.filename_key]}, method: EmojiCleaner costs {time.time() - start:6f} s")
        return sample
