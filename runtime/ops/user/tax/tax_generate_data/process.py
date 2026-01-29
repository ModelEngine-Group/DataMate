# -*- coding: utf-8 -*-

"""
数据生成算子：TaxDataGeneratorOperator
基于内置的 DataGenerator 生成个人所得税完税证明模拟数据
"""
import json
import os
import random
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper
from .src import DataGenerator


class TaxDataGeneratorOperator(Mapper):
    """
    数据生成算子
    用于生成个人所得税完税证明的模拟数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 metadata.yml 的参数获取配置
        # 与 UI 配置项保持一致：numParam / seedParam
        self.num = int(kwargs.get('numParam', 5))
        self.seed = kwargs.get('seedParam', '42')

        # 设置随机种子，便于复现
        if self.seed:
            try:
                random.seed(int(self.seed))
            except (ValueError, TypeError):
                logger.warning(f"无效的随机种子: {self.seed}，使用默认值")
                random.seed(42)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据生成

        Args:
            sample: 输入的数据样本（约定包含 export_path 字段）

        Returns:
            处理后的样本（保持原样返回）
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            output_dir = sample.get('export_path')
            if not output_dir:
                logger.error("未在 sample 中找到 'export_path'，无法写入文件")
                sample['text'] = ""
                return sample

            # 创建输出目录
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # 导入并使用生成器
            generator = DataGenerator(seed=int(self.seed) if self.seed else None)
            records = generator.generate_batch(count=self.num, seed=int(self.seed) if self.seed else None)

            # 保存为 JSON 文件
            for i, record in enumerate(records, 1):
                try:
                    taxpayer = record.get('纳税人姓名', '未知纳税人')
                    safe_name = "".join(c if c not in r'\\/:*?\"<>|' else "_" for c in taxpayer)
                    filename = os.path.join(output_dir, f"{safe_name}_个人所得税完税证明.json")

                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(record, f, ensure_ascii=False, indent=4)

                    logger.info(f"[{i}/{self.num}] 已生成: {filename}")
                except Exception as e:
                    logger.error(f"写入第 {i} 条记录失败: {e}")

            logger.info(f"\n成功生成 {len(records)} 份数据文件，保存在 '{output_dir}' 目录中。")

        except Exception as e:
            logger.error(f"TaxDataGeneratorOperator 执行失败: {e}")

        return sample
