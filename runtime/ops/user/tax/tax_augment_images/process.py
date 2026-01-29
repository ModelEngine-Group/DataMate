# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper
from .src import ImageAugmenter


class TaxImgAugOperator(Mapper):
    """
    图像增强合成算子：TaxImgAugOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 场景数量（兼容字符串或数值）
        self.scenes = int(kwargs.get('scenesParam', 2))
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = scenes_val.split(',')
        else:
            self.allowed_scenes = scenes_val if scenes_val else ['normal']

        self.skip_detect = kwargs.get('skipDetectParam', True)

    def _determine_scene_mode(self, bg_filename: str) -> str:
        if "3-" in bg_filename or "斜拍" in bg_filename:
            return "tilted"
        elif "4-" in bg_filename or "阴影" in bg_filename:
            return "shadow"
        elif "5-" in bg_filename or "水印" in bg_filename:
            return "watermark"
        elif "6-" in bg_filename or "不完整" in bg_filename:
            return "incomplete"
        else:
            return "normal"

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量合成图片。
        期望 sample 中包含 'export_path'（源图片目录）或 'src_dir'，并可包含 'output_path'。
        返回原样 sample。
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            # 输入目录优先从 sample 中获取
            input_dir = sample.get('export_path') + "/images"
            if not input_dir or not os.path.exists(input_dir):
                logger.error(f"Warning: Input directory not found: {input_dir}")
                return sample

            # 输出目录
            output_dir = input_dir
            os.makedirs(output_dir, exist_ok=True)

            # 获取输入路径
            parent_path = Path(file_path).parent
            coords_files = list(Path(parent_path).glob("*.json"))

            if len(coords_files) == 0:
                coord_cache_file = parent_path / "coordinates_cache.json"
            else:
                coord_cache_file = coords_files[0]
            bg_dir = parent_path / "backgrounds"

            # 初始化增强器
            augmenter = ImageAugmenter(
                backgrounds_dir=str(bg_dir),
                output_dir=str(output_dir),
                coord_file=str(coord_cache_file)
            )

            # 处理
            augmenter.process_images(str(input_dir))

        except Exception as e:
            logger.error(f"Error in TaxImgAugOperator: {e}")

        return sample
