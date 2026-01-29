"""
标注生成算子 - 不动产权证
"""
import os
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datamate.core.base_op import Mapper
from .src import AnnotationBuilder


class RealEstateAnnotationGenOperator(Mapper):
    """
    标注生成算子：RealEstateAnnotationGenOperator
    生成模型训练所需的图文对数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中的参数
        self.format = kwargs.get('formatParam', 'multimodal')
        self.split = float(kwargs.get('splitParam', 0.8))
        # 处理 seed，前端 input 传过来可能是字符串
        seed_val = kwargs.get('seedParam', 42)
        self.seed = int(seed_val) if seed_val else None

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
                logger.error(f"Warning: Input path not found: {input_path}")
                return sample

            input_path = Path(input_path)

            # 查找JSON文件
            json_files = list(input_path.glob("*.json"))
            if not json_files:
                logger.warning("未找到JSON文件")
                return sample

            # 查找图像目录
            images_dir = input_path / "images"
            if not images_dir.exists():
                logger.warning("未找到图像目录")
                return sample

            # 创建标注生成器
            builder = AnnotationBuilder(
                json_file=str(json_files[0]),
                images_dir=str(images_dir)
            )

            # 生成标注
            output_file = input_path / "qa_pairs.jsonl"
            count = builder.generate_annotations(str(output_file))

            # 记录生成的文件路径
            sample['qa_pairs_file'] = str(output_file)
            sample['qa_pairs_count'] = count
            logger.info(f"成功生成 {count} 条QA对")

        except Exception as e:
            logger.error(f"Error in RealEstateAnnotationGenOperator: {e}")
            
        return sample
