# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper
from .src import ImageConverter


class TaxDocToImgOperator(Mapper):
    """
    文档转图片算子：TaxDocToImgOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.dpi = int(kwargs.get('dpiParam', 200))
        # pattern 用于匹配输入文件类型
        self.pattern = kwargs.get('patternParam', "*.docx")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑：将指定目录下的文档转换为图片，并可选择删除原始文档
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input path not found: {input_path}")
                return sample

            input_path = Path(input_path)
            doc_files = list(input_path.glob(self.pattern))

            # 计算输出目录：优先使用 export_path/output_path，否则使用输入目录下的 images
            output_base = sample.get('export_path')
            output_dir = os.path.join(str(output_base), "images")

            # ImageConverter signature: ImageConverter(output_dir: str, dpi: int = 200)
            converter = ImageConverter(
                output_dir=output_dir,
                dpi=self.dpi,
            )
            converter.convert_batch([str(f) for f in doc_files])

        except Exception as e:
            logger.error(f"Error converting doc to image: {e}")

        return sample
