# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper
from .src.image_augmenter import augment_images


class InsuranceImgAugOperator(Mapper):
    """
    图片增强合成算子：InsuranceImgAugOperator
    将凭证图片与背景图进行合成，支持多种拍摄场景
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 处理模式：normal/tilted/shadow/watermark/incomplete/all
        self.mode = kwargs.get('modeParam', 'all')

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行图片增强合成
        sample 可包含 'export_path' 或其他路径参数；本算子主要依赖内部 src 的默认路径
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            input_path = sample.get('export_path') + "/images"
            parent_path = Path(file_path).parent
            bg_dir = parent_path / "backgrounds"
            coord_file = parent_path / "coordinates_cache.json"

            logger.info(f"开始图片增强合成，模式: {self.mode}")
            augment_images(input_path, input_path, bg_dir, coord_file, mode=self.mode)
            logger.info(f"图片增强完成")
        except Exception as e:
            logger.error(f"InsuranceImgAugOperator 执行失败: {e}")

        return sample
