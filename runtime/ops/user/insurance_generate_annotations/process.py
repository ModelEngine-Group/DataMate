# -*- coding: utf-8 -*-
import os
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper
from .src.annotation_builder import generate_annotations


class InsuranceAnnotationGenOperator(Mapper):
    """
    QA对生成算子：InsuranceAnnotationGenOperator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qa_type = kwargs.get('typeParam', 'all')

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行QA对生成，返回 sample
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            input_path = sample.get('export_path')

            logger.info(f"开始生成 {self.qa_type} QA对")
            generate_annotations(qa_type=self.qa_type, input_dir=input_path, output_dir=input_path)
            logger.info(f"QA对生成完成")
        except Exception as e:
            logger.error(f"InsuranceAnnotationGenOperator 执行失败: {e}")

        return sample
