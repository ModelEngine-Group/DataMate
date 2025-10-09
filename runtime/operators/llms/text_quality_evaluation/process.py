# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 基于LLM通过用户设置维度和相应描述进行文本质量评估
Create: 2025/3/14 11:00
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import Dict, Any

from loguru import logger

from data_platform.common.utils.text_splitter import TextSplitter
from data_platform.core.base_op import LLM
from .constant import EVAL_DIMENSION_MAP, BUSINESS_EVAL_DIMENSION_MAP
from .prompt_config import TEXT_QUALITY_EVALUATE_TEMPLATE

CHUNK_SIZE = 4000
CHUNK_OVERLAP = 0


class TextQualityEvaluation(LLM):
    def __init__(self, *args, **kwargs):
        super(TextQualityEvaluation, self).__init__(*args, **kwargs)
        self.total_length = 0
        self.text_list = []
        self.total_scores = [0, 0, 0, 0, 0, 0]
        self.text_splitter = TextSplitter(1024 * 1024, CHUNK_SIZE, CHUNK_OVERLAP)
        self.pattern = r'\d+\.\d+'
        self.task_id = kwargs.get("taskId", "default_id")

        self.llm = self.get_llm(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        tmp_text_list = self.text_splitter.split_text(sample[self.text_key])
        logger.info(f"task id: {self.task_id}, the length of chunks: {len(tmp_text_list)}")
        self.text_list = tmp_text_list
        text_res = {}
        self._evaluate_concurrently_text(text_res)

        sample[self.text_key] = "Success"
        self.save_sample([text_res], sample)
        cost_time = time.time() - start
        logger.info(f"task id: {self.task_id}, method: TextQualityEvaluation costs {cost_time:.6f} s")
        self.text_list = []
        return sample

    def _evaluate_concurrently_text(self, text_res, max_workers: int = 5):
        for eval_dimension in EVAL_DIMENSION_MAP + BUSINESS_EVAL_DIMENSION_MAP:
            text_res[eval_dimension["score_name"]] = 0
        self.total_scores = [0, 0, 0, 0, 0, 0]
        self.total_length = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 使用 partial 绑定多参数
            future_to_params = {
                executor.submit(
                    partial(self.get_current_score_concurrently, text)): text
                for text in self.text_list
            }
            for future in as_completed(future_to_params):
                self.parse_execute_result(future, future_to_params)
        for _, eval_dimension in enumerate(EVAL_DIMENSION_MAP + BUSINESS_EVAL_DIMENSION_MAP):
            total_score = self.total_scores[_]
            text_res[eval_dimension["score_name"]] = 0
            if self.total_length > 0:
                text_res[eval_dimension["score_name"]] = total_score / self.total_length

    def parse_execute_result(self, future, future_to_params):
        text = future_to_params[future]
        try:
            scores = future.result()
            if scores and len(scores) == len(self.total_scores):
                self.total_length += len(text)
                for _, score in enumerate(scores):
                    self.total_scores[_] = self.total_scores[_] + score * len(text)
        except Exception as e:
            logger.error(f"Evaluate error, error details: {e}")

    def get_current_score_concurrently(self, text, retry: int = 2):
        dimension_list = []
        for eval_dimension in EVAL_DIMENSION_MAP + BUSINESS_EVAL_DIMENSION_MAP:
            dimension = eval_dimension["dimension"] + ":" + eval_dimension["description"]
            dimension_list.append(dimension)
        prompt = TEXT_QUALITY_EVALUATE_TEMPLATE.format(context=text, dimension0=dimension_list[0],
                                                       dimension1=dimension_list[1], dimension2=dimension_list[2],
                                                       dimension3=dimension_list[3], dimension4=dimension_list[4],
                                                       dimension5=dimension_list[5])
        retry_time = 0
        while True:
            try:
                return self.get_scores(prompt)
            except RuntimeError as e:
                if retry_time < retry:
                    retry_time += 1
                else:
                    logger.warning(f"Request LLM error, details: {e}")
                    return []

    def get_scores(self, prompt):
        response = self.llm(prompt)
        scores_str_list = response.split(",")
        scores = []
        for scores_str in scores_str_list:
            decimals = re.findall(self.pattern, scores_str)
            if decimals:
                score = float(decimals[-1])
                if 0 <= score <= 1:
                    scores.append(score)
        logger.info(f"current evaluate scores: {scores}")
        return scores
