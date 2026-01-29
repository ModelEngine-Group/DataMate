"""
数据生成算子 - 不动产权证
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datamate.core.base_op import Mapper
from .src import DataGenerator

class RealEstateDataGenOperator(Mapper):
    """
    数据生成算子：RealEstateDataGenOperator
    用于生成不动产权证模拟数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中的参数
        self.count = int(kwargs.get('countParam', 5))

        # 处理 seed
        seed_val = kwargs.get('seedParam', 42)
        self.seed = int(seed_val) if seed_val else None

        self.output_dir = kwargs.get('outputDirParam', '/dataset').strip()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            # 创建数据生成器
            generator = DataGenerator(seed=self.seed)

            # 生成数据
            records = generator.generate_records(self.count)

            # 如果配置了输出目录，则保存文件
            if self.output_dir:
                output_path = Path(str(sample.get('export_path')))
                output_path.mkdir(parents=True, exist_ok=True)

                # 保存生成的数据
                output_file = output_path / "generated_records.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)

                logger.info(f"数据已生成并保存到: {output_file}")

                # 将文件路径写入 sample 返回
                sample['text'] = json.dumps(records, ensure_ascii=False, indent=2)
                sample['generated_records_path'] = str(output_file)

        except Exception as e:
            logger.error(f"Error in RealEstateDataGenOperator: {e}")
            
        return sample
