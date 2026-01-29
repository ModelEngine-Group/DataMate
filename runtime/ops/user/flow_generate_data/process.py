"""
流水数据生成算子 - process.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from datamate.core.base_op import Mapper
from .src import DataGenerator


class FlowDataGenOperator(Mapper):
    """
    流水数据生成算子：FlowDataGenOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.count = int(kwargs.get('countParam', 5))

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
        # 输出目录
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            # 获取输入文件路径
            input_path = sample.get('filePath')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Template file not found: {input_path}")
                return sample

            # 获取输出路径
            export_path = sample.get('export_path')

            # 确保输出目录存在
            output_path = Path(export_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # 创建数据生成器
            generator = DataGenerator(seed=self.seed)

            # 生成指定数量的数据记录
            records = []
            for i in range(self.count):
                # 构建输出文件名
                output_file = output_path / f'filled_model_0125_{i+1}.docx'

                # 填充文档
                values = generator.fill_document(
                    template_path=input_path,
                    output_path=str(output_file),
                    font_name='宋体',
                    font_size=12
                )

                records.append(values)
                logger.info(f"Generated document: {output_file}")

            # 将所有记录保存到sample中
            # sample['text'] = json.dumps(records, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error in FlowDataGenOperator: {e}")
            import traceback
            traceback.print_exc()

        return sample
