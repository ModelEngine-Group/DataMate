#!/user/bin/python

import re
from typing import List
from collections import deque

from loguru import logger


class TextSplitter:
    """文本切片"""
    # 基于常用标点符号分句，保持句子完整
    COMMON_PUNCTUATIONS = ["，", "。", "？", "！", "；", ",", "?", "!", ";"]
    PUNC_PATTERN = f"[{''.join(COMMON_PUNCTUATIONS)}]"

    def __init__(self, max_characters: int, chunk_size: int, chunk_overlap: int):
        """文本切片初始化
        Args:
            max_characters :文件最大字符，超过截断，-1不处理
            chunk_size: 块大小
            chunk_overlap: 块重叠度
        """
        if chunk_size <= chunk_overlap:
            logger.error(f"param chunk_size should larger than chunk_overlap, "
                         f"current chunk_size: {chunk_size}, chunk_overlap: {chunk_overlap}")
            raise Exception(83000, str(ValueError)) from None
        self.max_characters = max_characters
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n"]

    @staticmethod
    def split_text_by_separator(text: str, separator: str):
        """指定分隔符对文本进行切分，并且切分后的片段需要保留分隔符"""
        # 处理一个换行符与两个换行符之间的冲突
        if text.startswith("\n\n") and separator == "\n":
            chunks = re.split(f"({separator})", text.strip())
            chunks[0] = f"\n\n{chunks[0]}"
        else:
            chunks = re.split(f"({separator})", text)
        new_chunks = [chunks[idx] + chunks[idx + 1] for idx in range(1, len(chunks), 2)]
        new_chunks = [chunks[0]] + new_chunks
        return [chunk for chunk in new_chunks if chunk.strip() != ""]

    @staticmethod
    def split_sentences(chunk: str):
        """对切片按照标点符号切分成句子，并且保持标点符号不丢失"""
        sentences = re.split(TextSplitter.PUNC_PATTERN, chunk)
        delimiters = [s for s in chunk if s in TextSplitter.COMMON_PUNCTUATIONS]
        restore_chunks = []
        for chunk, delimiter in zip(sentences[:-1], delimiters):
            restore_chunks.append(chunk + delimiter)
        return restore_chunks + [sentences[-1]]

    def split_text(self, input_data: str):
        if self.max_characters > 0:
            logger.info(f"The document characters should be within: {self.max_characters}")
            input_data = input_data[:self.max_characters]
        logger.info(f"characters of the document: {len(input_data)}")
        chunks = self.split_text_recursive(input_data, self.separators)
        final_chunks = self.merge_chunks(chunks)
        final_chunks = self.split_text_by_chunk_size(final_chunks)
        return [chunk.strip() for chunk in final_chunks if chunk]

    def split_text_recursive(self, input_data: str, separators: List[str]):
        """对文档按照分隔符优先级进行递归切分：
            1. 符合chunk_size要求的切片不再切分。
            2. 大于chunk_size要求的切片，继续进行递归切分。
        Args:
            input_data: 输入文本
            separators: 分隔符

        Returns:
            List[str]: 切分后的文本片段

        """
        chunks = []
        cur_separator = ""
        next_separators = []
        for idx, sep in enumerate(separators):
            sep = re.escape(sep)
            if re.search(sep, input_data.strip()):
                cur_separator = sep
                next_separators = separators[idx + 1:]
                break

        if not cur_separator:
            return [input_data]
        else:
            cur_chunks = TextSplitter.split_text_by_separator(input_data, cur_separator)

        for chunk in cur_chunks:
            if len(chunk.strip()) <= self.chunk_size:
                chunks.append(chunk)
            else:
                if not next_separators:
                    chunks.append(chunk)
                else:
                    next_chunks = self.split_text_recursive(chunk, next_separators)
                    chunks.extend(next_chunks)
        return chunks

    def merge_chunks(self, chunks: List[str]):
        """对切分后的文本片段进行合并，合并过程考虑overlap"""
        final_chunks = []
        idx = 0
        while idx < len(chunks):
            if len(chunks[idx]) >= self.chunk_size:
                final_chunks.append(chunks[idx])
                idx += 1
                continue
            merge_idxes = self.get_merge_idxes(idx, chunks)
            content = ""
            for inner_idx in merge_idxes:
                content += chunks[inner_idx]
            final_chunks.append(content)
            idx = merge_idxes[-1] + 1
        return final_chunks

    def get_merge_idxes(self, cur_idx: int, chunks: List[str]):
        """获取可以合并的分片index，前向尽可能满足overlap，后向尽可能满足chunk_size"""
        idxes = deque([cur_idx])
        overlap_idx = cur_idx - 1
        cur_len = len(chunks[cur_idx])
        cur_idx += 1
        # 获取overlap的index
        over_lap_len = 0
        while overlap_idx >= 0:
            over_lap_len += len(chunks[overlap_idx])
            if over_lap_len > self.chunk_overlap or (cur_len + over_lap_len) > self.chunk_size:
                over_lap_len -= len(chunks[overlap_idx])
                break
            idxes.appendleft(overlap_idx)
            overlap_idx -= 1
        cur_len += over_lap_len
        # 获取merge的index
        while cur_idx < len(chunks):
            cur_len += len(chunks[cur_idx])
            if cur_len > self.chunk_size:
                break
            idxes.append(cur_idx)
            cur_idx += 1
        return idxes

    def split_chunks(self, chunks: List[str]):
        """对超过`chunk_size`限制的切片进行截断，过程中需要考虑overlap参数"""
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                start = 0
                end = self.chunk_size
                while end < len(chunk):
                    final_chunks.append(chunk[start: end])
                    start += self.chunk_size - self.chunk_overlap
                    end = start + self.chunk_size
                final_chunks.append(chunk[start:])
        return final_chunks

    def split_text_by_chunk_size(self, chunks: List[str]):
        """对切片后超长的文本块进行二次切分，使用截断，并考虑overlap"""
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
                continue
            sentences = TextSplitter.split_sentences(chunk)
            sub_chunks = self.merge_chunks(sentences)
            final_chunks.extend(self.split_chunks(sub_chunks))
        return final_chunks
