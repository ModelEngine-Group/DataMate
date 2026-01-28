"""
QA生成算子 - process.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper
from .src import AnnotationBuilder


class FlowQAGenOperator(Mapper):
    """
    QA生成算子：FlowQAGenOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.qa_count = int(kwargs.get('qaCountParam', 10))

        # 处理QA类型参数
        qa_types_val = kwargs.get('qaTypeParam', [])
        if isinstance(qa_types_val, str):
            self.qa_types = qa_types_val.split(',')
        else:
            self.qa_types = qa_types_val if qa_types_val else ['basic', 'detailed', 'complex']

    def _load_json_data(self, json_path: str) -> Dict[str, Any]:
        """
        加载JSON数据文件

        Args:
            json_path: JSON文件路径

        Returns:
            数据字典
        """
        if not os.path.exists(json_path):
            logger.error(f"JSON文件不存在: {json_path}")
            return {}

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载JSON文件: {json_path}")
            return data
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return {}

    def _find_image_files(self, input_dir: Path) -> List[Path]:
        """
        查找图片文件

        Args:
            input_dir: 输入目录

        Returns:
            图片文件列表
        """
        image_files = list(input_dir.glob("*.png")) +                     list(input_dir.glob("*.jpg")) +                     list(input_dir.glob("*.jpeg"))
        return sorted(image_files)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            # 获取输入路径
            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input directory not found: {input_path}")
                return sample

            # 获取输出路径
            export_path = sample.get('export_path')

            # 构建输出目录
            output_dir = Path(export_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 查找JSON文件
            input_dir = Path(input_path)
            json_files = list(input_dir.glob("*.json"))

            if not json_files:
                logger.warning(f"No JSON files found in {input_dir}")
                return sample

            # 查找图片文件
            image_files = self._find_image_files(input_dir / 'images')

            if not image_files:
                logger.warning(f"No image files found in {input_dir}")
                return sample

            # 创建标注生成器
            builder = AnnotationBuilder(qa_types=self.qa_types)

            # 为每个JSON文件生成QA对
            total_qa_count = 0
            for json_file in json_files:
                # 加载数据
                data = self._load_json_data(str(json_file))
                if not data:
                    continue

                # 查找对应的图片文件
                base_name = json_file.stem
                matching_images = [img for img in image_files 
                               if img.stem == base_name]

                if not matching_images:
                    logger.warning(f"No matching image found for {json_file.name}")
                    continue

                # 为每个图片生成QA对
                for img_file in matching_images:
                    # 生成QA对
                    qa_pairs = builder.generate_qa_pairs(
                        data=data,
                        image_path=str(img_file),
                        count=self.qa_count
                    )

                    # 保存QA对
                    saved_files = builder.save_qa_pairs(
                        qa_pairs=qa_pairs,
                        output_dir=str(output_dir),
                        base_name=f"{base_name}_qa"
                    )

                    total_qa_count += len(saved_files)
                    logger.info(f"已生成 {len(saved_files)} 个QA文件: {base_name}")

        except Exception as e:
            logger.error(f"Error in FlowQAGenOperator: {e}")
            import traceback
            traceback.print_exc()

        return sample
