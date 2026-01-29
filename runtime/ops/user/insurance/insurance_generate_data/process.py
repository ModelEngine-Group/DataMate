# -*- coding: utf-8 -*-
import os
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper
from .src.data_generator import generate_csv


class InsuranceDataGenOperator(Mapper):
    """
    社保数据生成算子：InsuranceDataGenOperator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = int(kwargs.get('countParam', 5))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成社保数据 CSV
        """
        try:
            file_path = sample['filePath']
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            logger.info(f"开始生成社保数据，count={self.count}")
            csv_path, count = generate_csv(count=self.count, output_dir=sample['export_path'])
            logger.info(f"CSV生成完成: {csv_path}, count={count}")
        except Exception as e:
            logger.error(f"InsuranceDataGenOperator 执行失败: {e}")

        return sample
