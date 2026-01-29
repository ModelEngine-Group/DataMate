"""
标注生成器 - 不动产权证
生成模型训练所需的图文对数据
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


class AnnotationBuilder:
    """标注生成器 - 不动产权证"""

    # 问题模板（按字段顺序，跳过第一个"沧"）
    QUESTIONS = [
        "这份不动产登记记录的年份是？",
        "该不动产所在县（市、区）是？",
        "该登记记录的文档编号是多少？",
        "不动产权利人姓名是？",
        "该不动产的所有权形式是？",
        "不动产登记地址是？",
        "不动产权证书号是多少？",
        "该不动产的权利类型是什么？",
        "该不动产的权利性质是什么？",
        "该不动产的用途是什么？",
        "该不动产的土地使用权面积和房屋建筑面积分别是多少？",
        "该不动产的土地使用期限是？"
    ]

    def __init__(self, json_file: str = "generated_records.json", 
                 images_dir: str = "images"):
        """
        初始化标注生成器

        Args:
            json_file: JSON数据文件路径
            images_dir: 图像目录路径
        """
        self.json_file = json_file
        self.images_dir = Path(images_dir)

    def load_json_data(self) -> List[List[Dict[str, Any]]]:
        """
        加载JSON数据

        Returns:
            记录列表
        """
        if not os.path.exists(self.json_file):
            logger.error(f"JSON文件不存在: {self.json_file}")
            return []

        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:
                return data
            else:
                logger.error(f"JSON数据格式不正确")
                return []
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return []

    def get_image_files(self) -> List[str]:
        """
        获取图像文件列表

        Returns:
            图像文件路径列表
        """
        if not self.images_dir.exists():
            logger.warning(f"图像目录不存在: {self.images_dir}")
            return []

        image_files = [
            os.path.join("images", f).replace(os.sep, "/")
            for f in os.listdir(str(self.images_dir))
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))
        ]
        image_files.sort()
        return image_files

    def match_image_to_record(self, record_index: int, image_files: List[str]) -> str:
        """
        匹配图像到记录

        Args:
            record_index: 记录索引
            image_files: 图像文件列表

        Returns:
            匹配的图像路径或空字符串
        """
        record_index = record_index + 1  # 记录索引从1开始
        for img in image_files:
            if f"_{record_index:02d}." in img:
                return img
        return ""

    def generate_qa_pairs(self, record: List[Dict[str, Any]], 
                        record_index: int, image_files: List[str]) -> Dict[str, Any]:
        """
        生成单条记录的QA对

        Args:
            record: 单条记录
            record_index: 记录索引
            image_files: 图像文件列表

        Returns:
            QA对字典
        """
        # 提取从第2个元素开始的12个type值（跳过"沧"）
        fields = [item["type"] for item in record[1:]]

        if len(fields) != 12:
            logger.warning(f"字段数量不正确: {len(fields)}, 预期12")
            return None

        # 构建单个QA对列表
        qa_list = [
            {"question": q, "answer": a.strip()}
            for q, a in zip(self.QUESTIONS, fields)
        ]

        # 匹配图像
        matched_image = self.match_image_to_record(record_index, image_files)

        if not matched_image:
            logger.warning(f"未找到第{record_index + 1}条记录对应的图片文件")

        # 创建输出数据结构
        output_data = {
            "file_info": matched_image,
            "individual_qa_pairs": qa_list,
            "complete_qa_pairs": {
                "question": "请提供这份不动产登记记录的完整信息。",
                "answer": f"年份：{fields[0]}，县（市、区）：{fields[1]}，文档编号：{fields[2]}，权利人：{fields[3]}，所有权形式：{fields[4]}，登记地址：{fields[5]}，不动产权证书号：{fields[6]}，权利类型：{fields[7]}，权利性质：{fields[8]}，用途：{fields[9]}，面积信息：{fields[10]}，土地使用期限：{fields[11]}"
            }
        }

        return output_data

    def generate_annotations(self, output_file: str = "qa_pairs.jsonl") -> int:
        """
        批量生成标注

        Args:
            output_file: 输出文件路径

        Returns:
            成功生成的记录数量
        """
        # 加载数据
        records = self.load_json_data()
        if not records:
            return 0

        # 获取图像文件
        image_files = self.get_image_files()

        # 生成QA对
        success_count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for idx, record in enumerate(records):
                qa_data = self.generate_qa_pairs(record, idx, image_files)
                if qa_data is None:
                    continue

                # 写入jsonl文件
                f.write(json.dumps(qa_data, ensure_ascii=False) + "\n")
                success_count += 1

        logger.info(f"成功生成 {success_count} 条QA对，保存到 {output_file}")
        return success_count
