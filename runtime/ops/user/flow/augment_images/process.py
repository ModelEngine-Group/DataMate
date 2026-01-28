"""
图像增强合成算子 - process.py
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper
from .src import ImageAugmentor


class FlowImgAugOperator(Mapper):
    """
    图像增强合成算子：FlowImgAugOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 处理场景参数 (checkbox 返回的是 list 或 逗号分隔字符串，需兼容)
        self.scenes = int(kwargs.get('scenesParam', 2))
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = scenes_val.split(',')
        else:
            self.allowed_scenes = scenes_val if scenes_val else ['normal']

        self.skip_detect = kwargs.get('skipDetectParam', True)

        # 背景图目录
        self.bg_dir = os.path.join(os.path.dirname(__file__), "backgrounds")

        # 坐标缓存文件路径 (存放在算子目录下)
        self.coord_cache_file = os.path.join(os.path.dirname(__file__), "coordinates_cache.json")

    def _determine_scene_mode(self, bg_filename: str) -> str:
        """根据背景图文件名确定场景模式"""
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
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            # 获取输入路径
            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input directory not found: {input_path}")
                return sample

            # 获取输出路径
            export_path = sample.get('export_path')
            if not export_path:
                export_path = input_path

            # 构建输入和输出目录
            input_dir = Path(input_path) / "images"
            output_dir = input_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # 获取源图文件
            src_files = list(input_dir.glob("*.png"))
            if not src_files:
                logger.warning(f"No source images found in {input_dir}")
                return sample

            # 获取背景图文件
            bg_path = Path(self.bg_dir)
            all_bg_files = [f for f in bg_path.glob("*") 
                          if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]

            # 过滤允许的场景
            filtered_bg_files = []
            for bg_file in all_bg_files:
                bg_name = bg_file.name
                scene_mode = self._determine_scene_mode(bg_name)
                if scene_mode in self.allowed_scenes:
                    filtered_bg_files.append(bg_file)

            if not filtered_bg_files:
                logger.warning(f"No background images found for allowed scenes: {self.allowed_scenes}")
                return sample

            # 判断是否使用随机选择
            use_random_selection = self.scenes is not None and self.scenes < len(filtered_bg_files)

            # 创建图像增强器
            augmentor = ImageAugmentor(
                bg_dir=self.bg_dir,
                coord_cache_file=self.coord_cache_file,
                skip_detect=self.skip_detect,
                allowed_scenes=self.allowed_scenes
            )

            # 处理每张源图
            augmented_count = 0
            for i, src_file in enumerate(src_files, 1):
                src_name = src_file.stem
                logger.info(f"\n[处理源图 {i}/{len(src_files)}] {src_file.name}")

                # 如果启用随机选择，从背景图中随机选择指定数量
                if use_random_selection:
                    selected_bg_files = random.sample(filtered_bg_files, self.scenes)
                    logger.info(f"  随机选择了 {len(selected_bg_files)} 个场景")
                else:
                    selected_bg_files = filtered_bg_files

                # 对每个背景图进行合成
                for bg_file in selected_bg_files:
                    bg_name = bg_file.stem
                    scene_mode = self._determine_scene_mode(bg_name)

                    # 输出文件名：源图名_背景图名.jpg
                    output_filename = f"{src_name}_{bg_name}.jpg"
                    output_path = output_dir / output_filename

                    logger.info(f"  -> 背景图: {bg_file.name} ({scene_mode})")

                    # 检测或加载坐标
                    if self.skip_detect:
                        corners = augmentor._load_cached_coordinates(bg_file.name)
                        if corners is None:
                            logger.info(f"    跳过：无缓存坐标")
                            continue
                    else:
                        corners = augmentor._detect_document_corners(str(bg_file))
                        if corners is None:
                            logger.info(f"    跳过：无法检测到文档区域")
                            continue

                        # 保存检测到的坐标到缓存
                        augmentor._save_cached_coordinates(str(bg_file), corners)

                    # 根据场景模式选择处理方式
                    enable_ratio_fix = True
                    enable_auto_rotate = scene_mode in ['tilted', 'shadow', 'watermark', 'incomplete']
                    enable_watermark = scene_mode == 'watermark'

                    # 执行合成
                    success = augmentor._base_synthesis_pipeline(
                        src_path=str(src_file),
                        dst_path=str(bg_file),
                        dst_corners=corners,
                        output_path=str(output_path),
                        mode=scene_mode,
                        enable_ratio_fix=enable_ratio_fix,
                        enable_auto_rotate=enable_auto_rotate,
                        enable_watermark=enable_watermark
                    )

                    if success:
                        logger.info(f"    成功: {output_filename}")
                        augmented_count += 1
                    else:
                        logger.error(f"    失败: {output_filename}")

        except Exception as e:
            logger.error(f"Error in FlowImgAugOperator: {e}")
            import traceback
            traceback.print_exc()

        return sample
