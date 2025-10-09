# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 基于LLM通过用户设置维度和相应描述进行QA对评估
Create: 2023/11/7 9:26
"""
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger


from data_platform.core.base_op import LLM


class QAConditionEvaluator(LLM):
    def __init__(self, *args, **kwargs):
        super(QAConditionEvaluator, self).__init__(*args, **kwargs)
        self.pattern = r'结果[:：] ?[YN]'
        self.template_path = Path(__file__).parent / "resources/template.txt"
        self.examples_path = Path(__file__).parent / "resources/examples.json"
        self.task_id = kwargs.get("taskId", "default_id")
        self.dimensions = kwargs.get("dimension", [
                    {
                        "dimension": "回答是否有针对性",
                        "description": "回答应对问题中的所有疑问点提供正面、直接的回答，"
                                       "不应引起疑惑。同时，答案不应有任何内容的遗漏，需构成一个完整的陈述。"
                    },
                    {
                        "dimension": "问题是否独立",
                        "description": "仅分析问题，问题的主体和客体都比较明确，即使有省略，也符合语言习惯。"
                                       "在不需要补充其他信息的情况下不会引起疑惑。"
                    },
                    {
                        "dimension": "语法是否错误",
                        "description": "问题为疑问句，答案为陈述句; 不存在词语搭配不当的情况;连接词和标点符号不存在错用情况；"
                                       "逻辑混乱的情况不存在；语法结构都正确且完整;"
                    }
                ])

        self.llm = self.get_llm(*args, **kwargs)
        self.prompts = self.build_llm_prompt(*args, **kwargs)

    @staticmethod
    def _process_examples(dimension_example: List) -> str:
        if not dimension_example:
            return "\n"
        res = "\n以下是一些案例供你参考："
        for single_example in dimension_example:
            res += (f"\n问题：{single_example['question']}"
                    f"\n回答：{single_example['answer']}"
                    f"\n分析思路：{single_example['evaluate']}"
                    f"\n结果：{single_example['result']}\n")
        return res

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        qas = json.loads(sample[self.text_key])
        single_content_res = []
        for qa in qas:
            single_qa_res = []
            for dimension, prompt in self.prompts.items():
                local_result = self._llm_call_parse(qa, prompt, retry=2)
                single_qa_res.append({"dimension": dimension, "result": local_result})
            qa_response = {"qaId": qa["qaId"], "result": single_qa_res}
            single_content_res.append(qa_response)

        sample[self.text_key] = "Sucess"
        self.save_sample(single_content_res, sample)
        cost_time = time.time() - start
        logger.info(f"task id: {self.task_id}, method: QAConditionEvaluator costs {cost_time:.6f} s")
        return sample

    def build_llm_prompt(self, *args, **kwargs) -> Dict:
        templates = self.template_path.read_text(encoding="utf-8")
        examples_dict = json.loads(self.examples_path.read_text(encoding="utf-8"))
        prompts_dict = {}
        for dimension in self.dimensions:
            name, des = dimension["dimension"], dimension["description"]
            dimension_example = self._process_examples(examples_dict.get(name))
            dimension_prompt = templates.format(criterion=des, examples=dimension_example, question="{question}",
                                                answer="{answer}")
            prompts_dict[name] = dimension_prompt
        return prompts_dict

    def _llm_call_parse(self, data: Dict, prompt: str, retry: int = 2):
        try:
            for _ in range(retry):
                response = self.llm(prompt.format(question=data["question"], answer=data["answer"]))
                result = re.findall(self.pattern, response)
                if result:
                    return "Y" in result[0]
        except RuntimeError as e:
            logger.error(f"method: QAConditionEvaluator execution error, cause by {e}")
        return False
