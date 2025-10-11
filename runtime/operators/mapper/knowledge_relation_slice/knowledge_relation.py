#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

__all__ = ['build_llm_prompt', 'get_json_list']

import math

import jieba
from loguru import logger

from . import graph_sim_func as bm25
from .knowledge_slice import TextSegmentationOperator


def build_llm_prompt(text):
    #
    prompt = """
    ===
    <Role>:
    你是一位问答对QA智能撰写专家，你擅长根据给定的内容给出准确、完整、详细的多个问答对。

    ===
    <Instructions>:
    - 你需要根据已知信息（context），准确、详细的生成多个QA对。
    - 生成的问答对中答案少于10个中文字符时，放弃该问答对。
    - 确保所有问答对的答案都是已知信息的一部分，且可以组成已知信息，确保没有信息遗漏。
    - 仅根据已知信息生成问答对，答案要详细，且不能创造臆想已知信息中没有的内容。
    - 确保生成的多个QA对之间不要进行排序，Q:或A:前后不要出现数字序号。
    - Q:使用疑问句方式，问号结尾；A:使用陈述句方式，句号结尾，确保回答完整。
    - 输出格式如下：
    Q:......
    A:......
    
    ===
    <task>
    满足上述条件的情况下，现根据context:'''{}'''
    生成的多个QA问答对为:

    """

    return prompt.format(text)


class KnowledgeSlice:
    # edatamate切片算法插件
    def __init__(self, file_text, chunk_size=500, overlap_size=100):
        self.file_text = file_text
        self.slice_op = TextSegmentationOperator(chunk_size, overlap_size)

    def execute(self):
        try:
            chunks = self.slice_op.process(self.file_text)
        except Exception as err:
            logger.error("split text failed, error is: %s", err, exc_info=True)
            chunks = []

        return chunks


class BM25Model:
    def __init__(self, data_list):
        self.data_list = data_list
        self.corpus = self.load_corpus()

    def bm25_similarity(self, query, num_best=1):
        query = jieba.lcut(query)
        bm = bm25.SimilarityAlgBM25(self.corpus)
        scores = bm.get_sim_scores(query)
        id_score = [(i, score) for i, score in enumerate(scores)]
        id_score.sort(key=lambda e: e[1], reverse=True)

        return id_score[0: num_best]

    def load_corpus(self):
        corpus = [jieba.lcut(data) for data in self.data_list]

        return corpus


class KnowledgeGraph:
    # class for document segmentation and create relation between knowledge
    def __init__(self, corpus_file_string, chunk_size=500, overlap_size=100, kg_relation=True):
        self.corpus_file_string = corpus_file_string
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.kg_relation = kg_relation
        self.slicing_corpus = []
        self.knowledge_slice = KnowledgeSlice(self.corpus_file_string, self.chunk_size, self.overlap_size)

    @staticmethod
    def update_gallery_list(gallery_list, iterated_dict):
        # get a gallery list which not in iterated_dict
        gallery_list_update = []
        gallery_list_index = []
        for i, _ in enumerate(gallery_list):
            if i not in iterated_dict:
                gallery_list_update.append(gallery_list[i])
                gallery_list_index.append(i)

        return gallery_list_update, gallery_list_index

    def document_slicing(self):
        json_list = []
        all_slices_info = self.knowledge_slice.execute()

        for _, item in enumerate(all_slices_info):
            json_list.append({
                "slice_data": item
            })

        self.slicing_corpus = json_list

    def build_knowledge_relation(self, slicing_corpus_list):
        # knowledge relation for each paragraph
        if not self.kg_relation:
            return slicing_corpus_list
        iterated_dict = {}
        kr_result_json_list = []
        gallery_list = []
        kr_relation_list = []

        if len(slicing_corpus_list) < 3:
            return slicing_corpus_list

        for _, item in enumerate(slicing_corpus_list):
            gallery_list.append(item['slice_data'])

        for k, item in enumerate(slicing_corpus_list):
            if k not in iterated_dict:
                iterated_dict[k] = 1
                cur_gallery_list, cur_gallery_src_index = self.update_gallery_list(gallery_list, iterated_dict)
                if len(cur_gallery_list) < 1:
                    kr_result_json_list.append({
                        "slice_data": item['slice_data']
                    })
                    return kr_result_json_list
                bm25_class = BM25Model(cur_gallery_list)
                id_scores = bm25_class.bm25_similarity(item['slice_data'], 1)
                kr_result_doc = item['slice_data'] + cur_gallery_list[id_scores[0][0]]
                kr_result_json_list.append({
                    "slice_data": kr_result_doc
                })
                if cur_gallery_src_index[id_scores[0][0]] not in iterated_dict:
                    iterated_dict[cur_gallery_src_index[id_scores[0][0]]] = 1
            else:
                continue

        return kr_result_json_list

    def build_graph_efficiently(self, search_space_size=50):
        # build knowledge relation in a efficient way
        knowledge_total_num = len(self.slicing_corpus)
        knowledge_chunk_num = math.ceil(knowledge_total_num / search_space_size)
        knowledge_relation_result = []

        for i in range(0, knowledge_chunk_num):
            cur_max_index = (i + 1) * search_space_size
            if cur_max_index > knowledge_total_num:
                corpus_list = self.slicing_corpus[i * search_space_size:]
            else:
                corpus_list = self.slicing_corpus[i * search_space_size:cur_max_index]
            # to do knowledge relation
            cur_knowledge_relation_result = self.build_knowledge_relation(corpus_list)
            knowledge_relation_result.extend(cur_knowledge_relation_result)

        return knowledge_relation_result

    def knowledge_corpus_list_json(self):
        # deal the corpus and return structed information json_list
        self.document_slicing()
        kr_result_list_json = self.build_graph_efficiently()

        return kr_result_list_json


def get_json_list(txt_string, chunk_size=500, overlap_size=100, kg_relation=True):
    if len(txt_string) > 0:
        kg_extract = KnowledgeGraph(txt_string, chunk_size, overlap_size, kg_relation)
        kr_result_json_list = kg_extract.knowledge_corpus_list_json()
    else:
        kr_result_json_list = []

    return kr_result_json_list
