# -*- coding: utf-8 -*-
"""
结婚证图像合成到实拍背景算子 - MarriageAugmentImages
将结婚证图片合成到多种实拍背景（斜拍、阴影、水印等），输出合成图。
"""
import os
import re
import random
from pathlib import Path
from typing import Dict, Any, List

from loguru import logger
from datamate.core.base_op import Mapper

from .src.image_augmentor import (
    cv_imread,
    detect_document_corners,
    run_synthesis,
    load_cached_coordinates,
    save_cached_coordinates,
    order_points,
)


class MarriageAugmentImages(Mapper):
    """结婚证图像合成到实拍背景：源图来自 export_path，背景来自 backgrounds/ 或 bgPathParam。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        scenes_val = kwargs.get('scenesParam')
        try:
            self.scenes = int(scenes_val) if scenes_val and str(scenes_val).isdigit() else None
        except (TypeError, ValueError):
            self.scenes = None
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = [s.strip() for s in scenes_val.split(',') if s.strip()]
        else:
            self.allowed_scenes = list(scenes_val) if scenes_val else ['normal']
        self.skip_detect = kwargs.get('skipDetectParam', True)
        self.bg_path_param = (kwargs.get('bgPathParam') or '').strip()
        self.bg_dir = os.path.join(os.path.dirname(__file__), 'backgrounds')
        self.coord_cache_file = os.path.join(os.path.dirname(__file__), 'coordinates_cache.json')

    def _determine_scene_mode(self, bg_filename: str) -> str:
        if '3-' in bg_filename or '斜拍' in bg_filename or '反光' in bg_filename:
            return 'tilted'
        if '4-' in bg_filename or '阴影' in bg_filename:
            return 'shadow'
        if '5-' in bg_filename or '水印' in bg_filename or '8-' in bg_filename:
            return 'watermark'
        if '6-' in bg_filename or '不完整' in bg_filename:
            return 'incomplete'
        return 'normal'

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            export_path = sample.get('export_path')
            if not export_path or not os.path.exists(export_path):
                logger.warning("MarriageAugmentImages: 未找到 export_path")
                return sample

            export_path = str(Path(export_path).resolve())
            bg_dir = self.bg_path_param if (self.bg_path_param and os.path.isdir(self.bg_path_param)) else self.bg_dir
            if not os.path.isdir(bg_dir):
                logger.warning(f"MarriageAugmentImages: 背景目录不存在: {bg_dir}")
                return sample

            bg_files: List[Path] = []
            for ext in ('*.jpg', '*.jpeg', '*.png'):
                bg_files.extend(Path(bg_dir).glob(ext))
            bg_files = [f for f in bg_files if 'debug' not in f.name.lower()]
            if not bg_files:
                logger.warning("MarriageAugmentImages: 未找到背景图")
                return sample

            filtered_bg = []
            for f in bg_files:
                mode = self._determine_scene_mode(f.name)
                if mode in self.allowed_scenes:
                    filtered_bg.append(f)
            if not filtered_bg:
                filtered_bg = bg_files

            if self.scenes is not None and self.scenes < len(filtered_bg):
                selected_bg = random.sample(filtered_bg, self.scenes)
            else:
                selected_bg = filtered_bg

            src_files: List[Path] = []
            for ext in ('*.jpg', '*.jpeg', '*.png'):
                src_files.extend(Path(export_path).glob(ext))
            src_files = [f for f in src_files if f.name != 'random_content.json']
            if not src_files:
                logger.warning("MarriageAugmentImages: 未找到源图")
                return sample

            for bg_file in selected_bg:
                bg_path = str(bg_file)
                if self.skip_detect:
                    corners = load_cached_coordinates(self.coord_cache_file, bg_path)
                    if corners is not None:
                        corners = order_points(corners)
                    else:
                        logger.info(f"  跳过背景（无缓存）: {bg_file.name}")
                        continue
                else:
                    corners = detect_document_corners(bg_path, self.coord_cache_file)
                    if corners is None:
                        logger.warning(f"  无法检测背景区域: {bg_file.name}")
                        continue

                bg_name = bg_file.stem
                bg_label = re.sub(r'^\d+[-_.]?', '', bg_name)

                for src_file in src_files:
                    src_base = src_file.stem
                    out_name = f"{src_base}-{bg_label}.jpg"
                    out_path = os.path.join(export_path, out_name)
                    mode = self._determine_scene_mode(bg_file.name)
                    if run_synthesis(str(src_file), bg_path, corners, out_path, mode=mode):
                        logger.info(f"MarriageAugmentImages: 已合成 {out_name}")
                    else:
                        logger.error(f"MarriageAugmentImages: 合成失败 {out_name}")

        except Exception as e:
            logger.error(f"MarriageAugmentImages execute error: {e}")
            import traceback
            traceback.print_exc()
        return sample
