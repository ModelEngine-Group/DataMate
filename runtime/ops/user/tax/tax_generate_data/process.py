import os
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper
from .src import DataGenerator


class TaxDataGenOperator(Mapper):
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

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            output_dir = sample['export_path']
            # 创建输出目录
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # 生成数据
            generator = DataGenerator(seed=self.seed)
            records = generator.generate_batch(count=self.count, seed=self.seed)

            # 保存数据
            for i, record in enumerate(records, 1):
                safe_name = "".join(c if c not in r'\/:*?"<>|' else "_" for c in record['纳税人姓名'])
                filename = os.path.join(output_dir, f"{safe_name}_个人所得税完税证明.json")

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=4)

                logger.info(f"[{i}/{self.count}] 已生成: {filename}")

            logger.info(f"\n成功生成 {self.count} 份数据文件，保存在 '{output_dir}' 目录中。")
        except Exception as e:
            logger.error(f"Error in RealEstateDataGenOperator: {e}")

        return sample
