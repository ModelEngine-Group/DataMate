# -*- coding: utf-8 -*-
import os
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper
from .src.doc_generator import batch_fill_templates


class InsuranceDocGenOperator(Mapper):
    """
    社保文档生成算子：InsuranceDocGenOperator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成社保文档
        """
        try:
            file_path = sample['filePath']
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            input_dir = sample['export_path']
            logger.info(f"开始生成社保文档，模板: {file_path}")
            output_dir, count = batch_fill_templates(file_path, input_dir, input_dir)
            logger.info(f"文档生成完成: {output_dir}, count={count}")
        except Exception as e:
            logger.error(f"InsuranceDocGenOperator 执行失败: {e}")

        return sample
