#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

import math
from multiprocessing import Pool, cpu_count

from six import iteritems
from six.moves import range
from loguru import logger

PARAM_K1 = 1.5
PARAM_B = 0.75
EPSILON = 0.25


def effective_n_jobs(n_jobs):
    if n_jobs == 0:
        raise ValueError('n_jobs == 0 in Parallel has no meaning')
    elif n_jobs is None:
        return 1
    elif n_jobs < 0:
        n_jobs = max(cpu_count() + 1 + n_jobs, 1)
    return n_jobs


class SimilarityAlgBM25(object):

    def __init__(self, corpus_docs):

        self.corpus_files_size = 0
        self.avg_dl = 0
        self.doc_file_freqs = []
        self.idf_dict = {}
        self.doc_len = []
        self._initialize(corpus_docs)

    def get_sim_score(self, document, index):

        score = 0
        doc_freqs = self.doc_file_freqs[index]
        for word in document:
            if word not in doc_freqs:
                continue
            try:
                score += (self.idf_dict[word] * doc_freqs[word] * (PARAM_K1 + 1)
                          / (doc_freqs[word] + PARAM_K1 * (1 - PARAM_B + PARAM_B * self.doc_len[index] / self.avg_dl)))
            except KeyError as ke:
                logger.warning('key not found in doc_freqs dict: ', word)
        return score

    def get_sim_scores(self, document):

        scores = []
        for index in range(self.corpus_files_size):
            cur_score = self.get_sim_score(document, index)
            scores.append(cur_score)
        return scores

    def get_scores_bow(self, document):

        scores = []
        for index in range(self.corpus_files_size):
            score = self.get_sim_score(document, index)
            if score > 0:
                scores.append((index, score))
        return scores

    def _initialize(self, corpus_files):
        """
        Calculates frequencies of terms in documents and in corpus_files. 
        Also computes inverse document frequencies.
        """
        nd = {}  # word -> number of documents with word
        num_doc = 0
        for document_file in corpus_files:
            self.corpus_files_size += 1
            self.doc_len.append(len(document_file))
            num_doc += len(document_file)

            frequencies_dict = {}
            for word in document_file:
                if word not in frequencies_dict:
                    frequencies_dict[word] = 0
                frequencies_dict[word] += 1
            self.doc_file_freqs.append(frequencies_dict)

            for word, _ in iteritems(frequencies_dict):
                if word not in nd:
                    nd[word] = 0
                nd[word] += 1

        self.avg_dl = float(num_doc) / self.corpus_files_size
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0

        negative_idfs_list = []
        for word, freq in iteritems(nd):
            idf = math.log(self.corpus_files_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf_dict[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs_list.append(word)
        self.average_idf = float(idf_sum) / len(self.idf_dict)

        eps = EPSILON * self.average_idf
        for word in negative_idfs_list:
            self.idf_dict[word] = eps
