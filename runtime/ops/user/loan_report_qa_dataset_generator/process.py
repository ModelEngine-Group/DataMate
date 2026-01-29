# -*- coding: utf-8 -*-

"""
Description:
    QA数据集生成器 - 从贷款报告数据和图片生成QA对话数据集
Create: 2025/01/28
"""

import glob
import json
import os
import random
import re
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class LoanReportQADatasetGenerator(Mapper):
    """QA数据集生成器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output_file = None
        self._train_ratio = int(kwargs.get("train_ratio", 80))
        self._val_ratio = int(kwargs.get("val_ratio", 10))
        self._test_ratio = int(kwargs.get("test_ratio", 10))
        self._doc_type = kwargs.get("doc_type", "个人贷款调查报告")

    def _load_json_data(self, filepath: str) -> Dict[str, Any]:
        """加载JSON数据文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generate_qa_conversations(self, loan_data: Dict[str, Any]) -> list:
        """根据贷款数据生成QA对话"""
        conversations = []

        # 提取关键字段
        basic_info = loan_data.get('基本信息', {})
        loan_app = loan_data.get('贷款申请信息', {})
        borrower = loan_data.get('借款人信息', {})
        repayment = loan_data.get('偿还能力评估', {})
        mortgage = loan_data.get('风险抵押详细信息', {})
        conclusion = loan_data.get('调查结论', {})

        borrower_name = loan_app.get('借款人姓名', '')
        borrower_id = loan_app.get('借款人身份证号码', '')
        spouse_name = loan_app.get('借款人配偶姓名', '')
        loan_amount = loan_app.get('单笔金额(元)', '')
        loan_term = loan_app.get('单笔期限(月)', '')
        interest_rate = loan_app.get('申请贷款利率基准利率浮动', '')
        occupation = borrower.get('职业性质', '')
        age = borrower.get('年龄(20-65岁)', '')
        marital = borrower.get('婚姻状况', '')
        monthly_income = repayment.get('借款人月收入(元)', '')
        monthly_payment = repayment.get('本笔贷款月供支出(元)', '')
        family_income = repayment.get('家庭月收入总额(元)', '')
        loan_dti = repayment.get('本笔收入负债比(DTI≤50%)', '')
        total_dti = repayment.get('总收入负债比(DTI≤55%)', '')
        ltv = mortgage.get('LTV(申请金额/押品评估价值)', '')
        property_address = mortgage.get('房产名称及座别(座落地址)', '')
        property_value = mortgage.get('评估价值(元)', '')
        conclusion_text = conclusion.get('整体结论', '')

        # 生成QA对
        conversations.append({"from": "human", "value": f"<image>\n这是什么类型的文档？"})
        conversations.append({"from": "gpt", "value": f"这是一份{self._doc_type}"})

        conversations.append({"from": "human", "value": f"借款人的姓名和身份证号码是多少？"})
        conversations.append({"from": "gpt", "value": f"借款人姓名是{borrower_name}，身份证号码是{borrower_id}"})

        conversations.append({"from": "human", "value": f"贷款金额、期限和还款方式是什么？"})
        conversations.append({"from": "gpt", "value": f"贷款金额{loan_amount}，贷款期限{loan_term}个月，还款方式为等额本息"})

        conversations.append({"from": "human", "value": f"贷款利率是多少？"})
        conversations.append({"from": "gpt", "value": f"{interest_rate}"})

        conversations.append({"from": "human", "value": f"借款人的职业、年龄和婚姻状况是什么？"})
        conversations.append({"from": "gpt", "value": f"职业是{occupation}，年龄{age}岁，婚姻状况为{marital}"})

        if spouse_name:
            conversations.append({"from": "human", "value": f"借款人配偶的姓名是什么？"})
            conversations.append({"from": "gpt", "value": f"借款人配偶姓名是{spouse_name}"})

        conversations.append({"from": "human", "value": f"借款人月收入和家庭月收入总额分别是多少？"})
        conversations.append({"from": "gpt", "value": f"借款人月收入{monthly_income}，家庭月收入总额{family_income}"})

        conversations.append({"from": "human", "value": f"本笔贷款月供和收入负债比是多少？"})
        conversations.append({"from": "gpt", "value": f"本笔贷款月供{monthly_payment}，本笔收入负债比{loan_dti}，总收入负债比{total_dti}"})

        conversations.append({"from": "human", "value": f"抵押物地址和评估价值是多少？"})
        conversations.append({"from": "gpt", "value": f"抵押物地址为{property_address}，评估价值{property_value}"})

        conversations.append({"from": "human", "value": f"LTV是多少？"})
        conversations.append({"from": "gpt", "value": f"{ltv}"})

        conversations.append({"from": "human", "value": f"调查报告的整体结论是什么？"})
        conversations.append({"from": "gpt", "value": f"{conclusion_text}"})

        # JSON格式提取
        conversations.append({"from": "human", "value": f"请提取所有关键信息，以JSON格式输出"})

        json_output = {
            "借款人姓名": borrower_name,
            "借款人身份证号码": borrower_id,
            "借款人配偶姓名": spouse_name if spouse_name else "",
            "贷款金额": loan_amount,
            "贷款期限": loan_term,
            "贷款利率": interest_rate,
            "职业性质": occupation,
            "借款人年龄": age,
            "婚姻状况": marital,
            "借款人月收入": monthly_income,
            "家庭月收入总额": family_income,
            "本笔贷款月供": monthly_payment,
            "本笔收入负债比": loan_dti,
            "总收入负债比": total_dti,
            "抵押物地址": property_address,
            "评估价值": property_value,
            "LTV": ltv,
            "调查结论": conclusion_text
        }
        conversations.append({"from": "gpt", "value": json.dumps(json_output, ensure_ascii=False)})

        return conversations

    def _extract_sequence_and_name(self, filename: str) -> tuple:
        """从文件名提取序号和姓名"""
        # 文件名格式: 个人贷款调查报告_0000001-杨勇.jpg
        match = re.match(r'个人贷款调查报告_(\d{7})-(.+)\.jpg', filename)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据集生成"""
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        self._output_file = sample['export_path'] + "/dataset.jsonl"

        # 获取数据目录
        data_dir = sample['export_path']
        images_dir = data_dir + "/images"

        if not os.path.exists(data_dir):
            logger.error(f"数据目录不存在: {data_dir}")
            return sample

        if not os.path.exists(images_dir):
            logger.error(f"图片目录不存在: {images_dir}")
            return sample

        # 读取数据文件
        json_files = glob.glob(os.path.join(data_dir, '*.json'))
        if not json_files:
            logger.warning(f"未找到JSON数据文件")
            return sample

        data_dict = {}
        for json_file in json_files:
            filename = os.path.basename(json_file)
            match = filename.replace('虚拟贷款调查报告_', '').replace('.json', '')
            parts = match.split('-', 1)
            if len(parts) == 2:
                seq, name = parts[0], parts[1]
                data_dict[seq] = {
                    'name': name,
                    'filepath': json_file,
                    'data': self._load_json_data(json_file)
                }

        logger.info(f"加载了 {len(data_dict)} 条数据记录")

        # 解析图片文件
        jpg_files = glob.glob(os.path.join(images_dir, '*.jpg'))
        if not jpg_files:
            logger.warning(f"未找到图片文件")
            return sample

        # 构建样本
        samples = []
        for jpg_file in jpg_files:
            filename = os.path.basename(jpg_file)
            seq, name = self._extract_sequence_and_name(filename)

            if seq is None or seq not in data_dict:
                logger.warning(f"跳过: {filename} (无法匹配数据)")
                continue

            data_info = data_dict[seq]
            loan_data = data_info['data']
            conversations = self._generate_qa_conversations(loan_data)

            sample_item = {
                "id": f"loan_report_{seq}_{name}",
                "image": f"images/{filename}",
                "conversations": conversations
            }
            samples.append(sample_item)
            logger.info(f"添加样本: {filename}")

        if not samples:
            logger.warning(f"未能生成任何样本")
            return sample

        logger.info(f"共生成 {len(samples)} 个样本")

        # 划分数据集
        random.seed(42)
        random.shuffle(samples)

        total = len(samples)
        train_end = int(total * self._train_ratio / 100)
        val_end = train_end + int(total * self._val_ratio / 100)

        train_samples = samples[:train_end]
        val_samples = samples[train_end:val_end]
        test_samples = samples[val_end:]

        # 构建最终数据集
        dataset = {
            "info": {
                "description": f"{self._doc_type}数据集",
                "document_type": self._doc_type,
                "total_samples": total,
                "format": "multimodal",
                "created_at": datetime.now().isoformat()
            },
            "train": train_samples,
            "validation": val_samples,
            "test": test_samples,
            "split": {
                "train": len(train_samples),
                "validation": len(val_samples),
                "test": len(test_samples)
            }
        }

        # 保存数据集
        with open(self._output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        logger.info(f"数据集已保存至: {self._output_file}")
        logger.info(f"训练集: {len(train_samples)} 样本")
        logger.info(f"验证集: {len(val_samples)} 样本")
        logger.info(f"测试集: {len(test_samples)} 样本")

        return sample
