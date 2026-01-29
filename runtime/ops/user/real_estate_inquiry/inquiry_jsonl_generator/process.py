"""
JSON文件生成算子
功能：将不动产数据和图片信息组合生成符合JSONL格式的JSON文件
"""

import json
import os
import re
import random
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper


class JsonlGenerator:
    """JSON文件生成辅助类"""

    def __init__(
        self,
        output_dir: str = "./output",
        template_path: str = "./templates/output_json_template.json",
    ):
        """
        初始化JSON生成器

        Args:
            output_dir: 输出目录
            template_path: JSON模板文件路径
        """
        self.output_dir = output_dir
        self.template_path = template_path

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 加载JSON模板
        self.json_template = self._load_json_template()

        logger.info(f"JSON生成器初始化完成，输出目录: {output_dir}")

    def _load_json_template(self) -> Dict[str, Any]:
        """
        加载JSON模板文件

        Returns:
            JSON模板字典
        """
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                template = json.load(f)
                logger.info(f"成功加载JSON模板: {self.template_path}")
                return template
        except FileNotFoundError:
            logger.warning(f"JSON模板文件未找到: {self.template_path}，使用默认模板")
            # 返回默认模板
            return {
                "images": ["./output/img\\不动产查询表_001.jpg"],
                "messages": [
                    {
                        "role": "user",
                        "content": "<image>\n请分析这张不动产信息查询结果，并列出所有不动产的地址和建筑面积。",
                    },
                    {
                        "role": "assistant",
                        "content": "经过分析，该不动产的地址为：[对应图片的地址]，建筑面积为：[对应图片的建筑面积]。",
                    },
                ],
            }
        except Exception as e:
            logger.error(f"加载JSON模板失败: {str(e)}")
            raise

    def _generate_random_qa_pair(
        self, data: Dict[str, Any], page_number: int = 1, image_path: str = ""
    ) -> tuple:
        """
        随机生成问答对

        Args:
            data: 数据字典
            page_number: 页码（1表示第一页，2表示第二页）
            image_path: 图片路径（用于调试）

        Returns:
            (问题, 答案)
        """
        # 第一页的问答模板（包含省份、姓名证件号、表格数据）
        page1_qa_templates = [
            # 省份
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我查询的省份是哪里。",
                "extract": lambda d: f"经过分析，查询的省份为：{d.get('省份', '未提供')}。",
            },
            # 姓名和证件号
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我查询人的姓名和证件号码。",
                "extract": lambda d: self._format_name_id_answer(d),
            },
            # 地址和建筑面积
            {
                "question": "<image>\n请分析这张不动产信息查询结果，并列出所有不动产的地址和建筑面积。",
                "extract": lambda d: self._format_address_area_answer(d),
            },
            # 表格数据综合
            {
                "question": "<image>\n请分析这张不动产信息查询结果，并列出所有不动产的序号、状态和产权证号。",
                "extract": lambda d: self._format_table_summary_answer(d),
            },
            # 规划用途
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我所有不动产的规划用途。",
                "extract": lambda d: self._format_planning_purpose_answer(d),
            },
            # 数据来源
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我所有不动产的数据来源。",
                "extract": lambda d: self._format_data_source_answer(d),
            },
            # 合同号
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我所有不动产的合同号。",
                "extract": lambda d: self._format_contract_number_answer(d),
            },
        ]

        # 第二页的问答模板（只包含电脑查册人、证明流水号、打印日期）
        page2_qa_templates = [
            # 电脑查册人
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我电脑查册人是谁。",
                "extract": lambda d: f"经过分析，电脑查册人为：{d.get('电脑查册人', '未提供')}。",
            },
            # 证明流水号
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我证明流水号是多少。",
                "extract": lambda d: f"经过分析，证明流水号为：{d.get('证明流水号', '未提供')}。",
            },
            # 打印日期
            {
                "question": "<image>\n请分析这张不动产信息查询结果，告诉我打印日期和时间。",
                "extract": lambda d: f"经过分析，打印日期为：{d.get('打印日期', '未提供')}。",
            },
        ]

        # 根据页码选择合适的问答模板
        if page_number == 2:
            qa_templates = page2_qa_templates
        else:
            qa_templates = page1_qa_templates

        # 随机选择一个问答模板
        selected = random.choice(qa_templates)
        question = selected["question"]
        answer = selected["extract"](data)

        # 调试信息：打印页码和选择的问题类型
        logger.info(
            f"图片: {image_path}, 页码: {page_number}, 问题: {question[:80]}..."
        )

        return question, answer

    def _format_name_id_answer(self, data: Dict[str, Any]) -> str:
        """格式化姓名和证件号答案"""
        name_id = data.get("姓名（证件号码）", "")
        if "（" in name_id:
            name = name_id.split("（")[0]
            id_num = name_id.split("（")[1].rstrip("）")
            return f"经过分析，查询人的姓名为：{name}，证件号码为：{id_num}。"
        return f"经过分析，查询人的姓名和证件号码为：{name_id}。"

    def _format_contract_number_answer(self, data: Dict[str, Any]) -> str:
        """格式化合同号答案"""
        table_data = data.get("表格数据", [])
        if len(table_data) == 0:
            return "未找到不动产信息。"
        if len(table_data) == 1:
            return f"经过分析，该不动产的合同号为：{table_data[0].get('合同号', '')}。"

        response_parts = []
        for i, row in enumerate(table_data, 1):
            response_parts.append(f"第{i}处不动产的合同号为：{row.get('合同号', '')}")

        return "经过分析，" + "；".join(response_parts) + "。"

    def _format_address_area_answer(self, data: Dict[str, Any]) -> str:
        """格式化地址和建筑面积答案"""
        table_data = data.get("表格数据", [])
        if len(table_data) == 0:
            return "未找到不动产信息。"

        response_parts = []
        for i, row in enumerate(table_data, 1):
            response_parts.append(
                f"第{i}处不动产的地址为：{row.get('地址', '')}，建筑面积为：{row.get('建筑面积', '')}㎡"
            )

        return "经过分析，" + "；".join(response_parts) + "。"

    def _format_table_summary_answer(self, data: Dict[str, Any]) -> str:
        """格式化表格数据综合答案"""
        table_data = data.get("表格数据", [])
        if len(table_data) == 0:
            return "未找到不动产信息。"

        response_parts = []
        for i, row in enumerate(table_data, 1):
            response_parts.append(
                f"第{i}处不动产的序号为：{row.get('序号', '')}，状态为：{row.get('状态', '')}，产权证号为：{row.get('产权证号', '')}"
            )

        return "经过分析，" + "；".join(response_parts) + "。"

    def _format_planning_purpose_answer(self, data: Dict[str, Any]) -> str:
        """格式化规划用途答案"""
        table_data = data.get("表格数据", [])
        if len(table_data) == 0:
            return "未找到不动产信息。"

        planning_purposes = []
        for i, row in enumerate(table_data, 1):
            planning_purposes.append(row.get("规划用途", ""))

        if planning_purposes:
            return f"经过分析，该不动产的规划用途为：{'、'.join(planning_purposes)}。"
        else:
            return "未找到不动产信息。"

    def _format_data_source_answer(self, data: Dict[str, Any]) -> str:
        """格式化数据来源答案"""
        table_data = data.get("表格数据", [])
        if len(table_data) == 0:
            return "未找到不动产信息。"

        data_sources = []
        for i, row in enumerate(table_data, 1):
            data_sources.append(row.get("数据来源", ""))

        if data_sources:
            return f"经过分析，该不动产的数据来源为：{'、'.join(data_sources)}。"
        else:
            return "未找到不动产信息。"

    def _generate_single_json_entry(
        self, data: Dict[str, Any], image_path: str, index: int
    ) -> Dict[str, Any]:
        """
        生成单条JSON记录

        Args:
            data: 数据字典
            image_path: 图片路径
            index: 序号

        Returns:
            JSON记录字典
        """
        # 随机选择一个问答对
        question, answer = self._generate_random_qa_pair(data, index, image_path)

        # 构建记录
        record = {
            "images": [image_path],
            "messages": [
                {
                    "role": "user",
                    "content": question,
                },
                {
                    "role": "assistant",
                    "content": answer,
                },
            ],
        }

        return record

    def generate_json_file(
        self,
        data_list: List[Dict[str, Any]],
        image_paths: List[str],
        output_filename: str = "output.json",
    ) -> str:
        """
        生成JSON文件

        Args:
            data_list: 数据列表
            image_paths: 图片路径列表
            output_filename: 输出文件名

        Returns:
            JSON文件路径
        """
        try:
            # 检查数据数量是否匹配
            if len(data_list) != len(image_paths):
                raise ValueError(
                    f"数据数量({len(data_list)})与图片数量({len(image_paths)})不匹配"
                )

            # 生成JSON记录
            json_records = []
            for idx, (data, image_path) in enumerate(zip(data_list, image_paths), 1):
                try:
                    record = self._generate_single_json_entry(data, image_path, idx)
                    json_records.append(record)
                except Exception as e:
                    logger.error(f"生成第{idx}条JSON记录失败: {str(e)}")
                    continue

            # 保存JSON文件（数组格式）
            output_path = os.path.join(self.output_dir, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_records, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON文件已保存到: {output_path}，共{len(json_records)}条记录")
            return output_path

        except Exception as e:
            logger.error(f"生成JSON文件时发生错误: {str(e)}")
            raise


class JsonlGeneratorOps(Mapper):
    """
    JSON文件生成算子
    类名建议使用驼峰命名法定义，例如 JsonlGenerator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从UI参数获取配置
        self.generator = None
        self.generation_mode = kwargs.get("generationMode", "jsonl")
        self.include_table_data = kwargs.get("includeTableData", True)
        self.output_format = kwargs.get("outputFormat", "path")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """

        try:
            export_path = sample["export_path"]
            template_path = os.path.join(os.path.dirname(__file__), "templates/output_json_template.json")
            self.generator = JsonlGenerator(
                export_path,
                template_path,
            )

            # 加载数据
            with open(template_path, "r", encoding="utf-8") as f:
                data_list = json.load(f)


            # 生成JSON文件
            output_path = self.generator.generate_json_file(
                data_list, export_path+"/images", "qa_pairs.json"
            )

            return sample

        except Exception as e:
            logger.error(f"生成JSON文件时发生错误: {str(e)}")
            raise
