"""
标注生成模块 - 用于生成多模态训练用的问答对
"""

import json
from typing import Dict, Any, List, Optional


class AnnotationBuilder:
    """标注生成器类"""

    def __init__(self, qa_types: List[str] = None):
        """
        初始化标注生成器

        Args:
            qa_types: QA类型列表，可选basic/detailed/complex
        """
        self.qa_types = qa_types or ['basic', 'detailed', 'complex']

        # 定义基础信息QA模板
        self.basic_templates = [
            {
                "questions": [
                    "这是什么类型的文档？",
                    "账户户名是什么？",
                    "银行账号是多少？"
                ],
                "answer_keys": ["户名", "账号"]
            },
            {
                "questions": [
                    "统计期间是什么时间？",
                    "流入资金笔数和总额分别是多少？",
                    "月平均流入资金是多少？"
                ],
                "answer_keys": ["统计期间", "流入资金笔数", "流入资金总额", "月平均流入资金"]
            },
            {
                "questions": [
                    "每月还款金额是多少？",
                    "目前月债务支出是多少？",
                    "借款人家庭当前月总收入是多少？"
                ],
                "answer_keys": ["每月还款金额", "目前月债务支出", "借款人家庭当前月总收入"]
            },
            {
                "questions": [
                    "债务占比是多少？",
                    "经办人和复核人分别是谁？",
                    "证明日期是什么时候？"
                ],
                "answer_keys": ["债务占比", "经办人", "复核人", "日期年份", "日期月份", "日期日"]
            }
        ]

        # 定义详细信息QA模板
        self.detailed_templates = [
            {
                "questions": [
                    "这份证明的户名是什么？",
                    "该账户的银行和账号分别是什么？",
                    "这份流水证明的统计期间是多久？"
                ],
                "answer_keys": ["户名", "账号", "统计期间"]
            },
            {
                "questions": [
                    "这份证明中流入资金有多少笔？",
                    "流入资金总额是多少？",
                    "月平均流入资金是多少？"
                ],
                "answer_keys": ["流入资金笔数", "流入资金总额", "月平均流入资金"]
            },
            {
                "questions": [
                    "每月还款金额是多少？",
                    "目前月债务支出是多少？",
                    "债务占比是多少？"
                ],
                "answer_keys": ["每月还款金额", "目前月债务支出", "债务占比"]
            }
        ]

        # 定义复杂推理QA模板
        self.complex_templates = [
            {
                "questions": [
                    "借款人家庭当前月总收入是多少？",
                    "这份证明的经办人是谁？",
                    "这份证明的复核人是谁？"
                ],
                "answer_keys": ["借款人家庭当前月总收入", "经办人", "复核人"]
            },
            {
                "questions": [
                    "这份证明的日期是哪一年？",
                    "这份证明的日期是几月？",
                    "这份证明的日期是几日？"
                ],
                "answer_keys": ["日期年份", "日期月份", "日期日"]
            },
            {
                "questions": [
                    "这份证明的备注内容是什么？",
                    "这份证明的完整日期是什么？",
                    "这份证明的债务占比是多少？"
                ],
                "answer_keys": ["备注", "日期年份", "日期月份", "日期日", "债务占比"]
            }
        ]

    def _get_templates_by_type(self, qa_type: str) -> List[Dict[str, Any]]:
        """根据QA类型获取对应的模板"""
        if qa_type == 'basic':
            return self.basic_templates
        elif qa_type == 'detailed':
            return self.detailed_templates
        elif qa_type == 'complex':
            return self.complex_templates
        else:
            return self.basic_templates

    def _build_answer(self, data: Dict[str, Any], 
                     answer_keys: List[str]) -> str:
        """根据数据字段构建答案"""
        answers = []
        for key in answer_keys:
            if key in data:
                answers.append(f"{data[key]}")
        return "，".join(answers) if answers else "未找到相关信息"

    def generate_qa_pairs(self, data: Dict[str, Any], 
                        image_path: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        生成QA对

        Args:
            data: 数据字典
            image_path: 图片路径
            count: 生成的QA对数量

        Returns:
            QA对列表
        """
        qa_pairs = []

        # 收集所有启用的模板
        all_templates = []
        for qa_type in self.qa_types:
            templates = self._get_templates_by_type(qa_type)
            all_templates.extend(templates)

        # 生成指定数量的QA对
        for i in range(count):
            # 循环使用模板
            template = all_templates[i % len(all_templates)]

            # 为每个问题构建对话
            conversations = []
            for question in template['questions']:
                conversations.append({
                    "from": "human",
                    "value": f"<image>\n{question}"
                })

                # 构建答案
                answer = self._build_answer(data, template['answer_keys'])
                conversations.append({
                    "from": "gpt",
                    "value": answer
                })

            # 构建QA对
            qa_pair = {
                "id": f"flow_qa_{i+1}",
                "image": image_path,
                "conversations": conversations
            }

            qa_pairs.append(qa_pair)

        return qa_pairs

    def save_qa_pairs(self, qa_pairs: List[Dict[str, Any]], 
                    output_dir: str, base_name: str = "qa"):
        """
        保存QA对到文件

        Args:
            qa_pairs: QA对列表
            output_dir: 输出目录
            base_name: 基础文件名

        Returns:
            保存的文件路径列表
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        saved_files = []
        for i, qa_pair in enumerate(qa_pairs, 1):
            filename = os.path.join(output_dir, f"{base_name}_{i}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(qa_pair, f, ensure_ascii=False, indent=2)
            saved_files.append(filename)

        return saved_files
