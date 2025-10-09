#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 暴力色情文本过滤
Create: 2024/12/26 15:43
"""
import logging as logger
import time
from pathlib import Path
from typing import Dict, Any

from data_platform.common.utils.aho_corasick import AhoCorasic
from data_platform.core.base_op import Mapper


class SexualAndViolentWordCleaner(Mapper):
    """外部输入的暴力、色情文本过滤插件"""
    root_path = Path(__file__).parent / 'resources'
    VIOLENT_FILE_PATH = str(root_path / 'violent.txt')
    SEXUAL_FILE_PATH = str(root_path / 'sexual.txt')
    SPECIAL_SYMBOLS_PATH = str(root_path / 'special_symbols.txt')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.violent_words = self.load_words_list(self.VIOLENT_FILE_PATH)
        self.sexual_words = self.load_words_list(self.SEXUAL_FILE_PATH)
        self.special_symbols = self.load_words_list(self.SPECIAL_SYMBOLS_PATH)
        self.words = self.violent_words | self.sexual_words
        self.ac_automaton = AhoCorasic(self.words)

    @staticmethod
    def load_words_list(path):
        """词表加载"""
        with open(path, 'r', encoding='utf-8') as f:
            words = set(f.read().splitlines())
        return words

    @staticmethod
    def words_replace(target_strings: list, text: str):
        """
        目标字符串替换。

        Args:
            target_strings: 前缀树根节点。
            text: 待清洗文本。
        returns:
            清洗后文本。
        """
        target_strings.sort(key=lambda x: -len(x))
        for s in target_strings:
            tmp_text = text.replace(s, '*' * len(s))
            text = tmp_text
        return text

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._sexual_and_violent_word_filter(sample[self.text_key])
        logger.info("fileName: %s, method: SexualAndViolentWordCleaner costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _sexual_and_violent_word_filter(self, text):
        """词语过滤主函数，分行过滤"""
        filtered_rows = []
        for row in text.split('\n'):
            matched_words = self.ac_automaton.search(row, self.special_symbols)
            filtered_rows.append(self.words_replace(matched_words, row))
        return '\n'.join(filtered_rows)
