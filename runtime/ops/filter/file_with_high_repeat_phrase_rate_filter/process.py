#!/user/bin/python
# -- encoding: utf-8 --

"""
Description: 词重复率过高文档过滤插件
Create: 2023/11/7 9:26
"""
import re
import time

from collections import Counter
from pathlib import Path
from typing import Dict, Any
from loguru import logger

import jieba
from datamate.core.base_op import Filter


class FileWithHighRepeatPhraseRateFilter(Filter):
    """词重复率过高文档过滤插件"""
    PUNCTUATION_PATTERN = re.compile(r'^[\u3000-\u303F\uff00-\uffef\s\W_]+$')

    def __init__(self, *args, **kwargs):
        super(FileWithHighRepeatPhraseRateFilter, self).__init__(*args, **kwargs)
        self._min_threshold = kwargs.get("repeatPhraseRatio", 0.5)  # 重复词符占全文的比例阈值，默认值为0.5
        self._hit_stopword_trigger = kwargs.get("hitStopwords", False)  # 计算重复词率时是否去除停用词，默认为False不去除，True为去除
        self._file_path = Path(__file__).parent / 'resources' / 'hit_stopwords.txt'
        self._hit_stopwords = []
        if self._hit_stopword_trigger:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                self._hit_stopwords = f.read().splitlines()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._file_with_high_repeat_phrase_rate_filter(sample[self.text_key],
                                                                               sample[self.filename_key])
        logger.info(f"fileName: {sample[self.filename_key]}, "
                    f"method: FileWithHighRepeatPhraseRateFilter costs {(time.time() - start):6f} s")
        return sample

    def _tokenize_by_jieba(self, text: str):
        """基于jieba对输入文本进行切分

        Args:
            text: 输入文档内容
        Returns:
            words_list: 切割后的词列表
        """

        for word in jieba.lcut(text):
            if not self.PUNCTUATION_PATTERN.match(word) and word not in self._hit_stopwords:
                yield word

    def _file_with_high_repeat_phrase_rate_filter(self, input_data: str, file_name):
        if len(input_data) < 2:  # 词语长度至少2个字符
            return input_data
        words_list = self._tokenize_by_jieba(input_data)
        words_count = dict(Counter(words_list))
        words_count_max, words_total_count = 0, 0
        for words in words_count:
            # 只统计中文、字母，且长度大于1的词语
            if len(words) > 1 and words.isalpha():
                words_count_max = max(words_count_max, words_count.get(words))
                words_total_count += words_count.get(words)
        output_data = input_data
        repeat_phrase_rate = words_count_max / words_total_count if words_total_count > 0 else 0
        if repeat_phrase_rate >= self._min_threshold:
            # 只要有一个词重复率高于阈值，就会过滤文档
            output_data = ""
            logger.info(f"The repeat phrase rate of the input data is {repeat_phrase_rate}. "
                        f"Threshold is {self._min_threshold}. The document {file_name} is filtered.")
        return output_data
