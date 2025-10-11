#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 过滤语言概率太低的文档（支持自定义阈值）
Create: 2023/12/7 15:43
"""
import sys
import time
import logging as logger

from pathlib import Path
from typing import Dict, Any

from data_platform.core.base_op import Filter
from data_platform.common.utils.aho_corasick import build_trie, add_fail_pointer

sys.setrecursionlimit(5000)


class AhoCorasic:
    """AC自动机算法进行目标字符串搜索"""

    def __init__(self, words):
        self._root = add_fail_pointer(build_trie(words))

    def search_and_count(self, text: str, special_symbols: set):
        """
        匹配敏感词，统计敏感词字数。

        Args:
            text: 文本
            special_symbols: 特殊字符（需跳过）
        Returns:
            统计敏感词字数
        """
        target_count = 0
        node = self._root

        valid_len = 0  # 当前遍历的有效长度
        for _, s in enumerate(text):
            if s in special_symbols:  # 跳过特殊字符
                continue

            matched = True
            while s not in node.child:  # 当node.child没有字符s
                if node == self._root:  # 当node为root（无node.fail），有效长度归0且跳出
                    valid_len = 0
                    matched = False
                    break
                elif node.fail == self._root:  # node.fail为root场景，有效长度归0，但可继续
                    valid_len = 0
                node = node.fail  # 移动到失败指针节点
            if not matched:
                continue

            node = node.child.get(s)
            valid_len += 1
            if node.word:  # node是单词尾字母
                target_count += valid_len
                valid_len = 0
        return target_count


class FileWithManySensitiveWordsFilter(Filter):
    """外部输入的暴力、色情文本过滤插件"""

    def __init__(self, *args, **kwargs):
        super(FileWithManySensitiveWordsFilter, self).__init__(*args, **kwargs)
        root_path = Path(__file__).parent / 'resources'
        violent_file_path = str(root_path / 'violent.txt')
        sexual_file_path = str(root_path / 'sexual.txt')
        political_file_path = str(root_path / 'political.txt')
        special_symbols_path = str(root_path / 'special_symbols.txt')
        self._file_sensitive_words_rate = kwargs.get("sensitiveWordsRate", 0.01)  # 参数默认值为0.01
        self.violent_words = self.load_words_list(violent_file_path)
        self.sexual_words = self.load_words_list(sexual_file_path)
        self.political_words = self.load_words_list(political_file_path)
        self.special_symbols = self.load_words_list(special_symbols_path)
        self.symbols = self.special_symbols | {"\n", "\t", "\r"}  # 符号，不纳入文本字数统计
        self.words = self.violent_words | self.sexual_words | self.political_words
        self.ac_automaton = AhoCorasic(self.words)

    @staticmethod
    def load_words_list(path):
        """词表加载"""
        with open(path, 'r', encoding='utf-8') as f:
            words = set(f.read().splitlines())
        return words

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._file_with_many_sensitive_words_filter(sample[self.text_key],
                                                                            sample[self.filename_key])
        logger.info("fileName: %s, method: FileWithManySensitiveWordsFilter costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _file_with_many_sensitive_words_filter(self, input_data: str, file_name):
        """过滤敏感词过多的文档"""
        total_count = 0
        for s in input_data:
            if s not in self.symbols:
                total_count += 1
        if total_count == 0:
            return input_data

        # 敏感词率 = 敏感词字数 / 总字数，符号不纳入统计
        sensitive_rate = self.ac_automaton.search_and_count(input_data, self.special_symbols) / total_count
        if sensitive_rate >= self._file_sensitive_words_rate:
            logger.info(
                "This document contains too many sensitive words. The proportion of sensitive words is %s. "
                "Threshold is %s. The document %s is filtered.", sensitive_rate, self._file_sensitive_words_rate,
                file_name)
            return ""
        else:
            return input_data
