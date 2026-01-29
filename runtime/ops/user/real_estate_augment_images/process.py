"""
图像增强算子 - 不动产权证
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from datamate.core.base_op import Mapper
from .src import ImageAugmenter


class RealEstateImgAugOperator(Mapper):
    """
    图像增强合成算子：RealEstateImgAugOperator
    将电子凭证图像合成到真实拍摄场景中
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 处理场景参数
        self.scenes = int(kwargs.get('scenes', 2))
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = scenes_val.split(',')
        else:
            self.allowed_scenes = scenes_val if scenes_val else ['normal']

        # 处理switch类型参数，可能是字符串'true'/'false'或布尔值
        skip_detect_val = kwargs.get('skipDetectParam', True)
        if isinstance(skip_detect_val, str):
            self.skip_detect = skip_detect_val.lower() in ('true', '1', 'yes')
        else:
            self.skip_detect = bool(skip_detect_val)

        # 预加载背景图列表
        self.bg_dir = os.path.join(os.path.dirname(__file__), "backgrounds")

        # 坐标缓存文件路径
        self.coord_cache_file = os.path.join(os.path.dirname(__file__), "coordinates_cache.json")

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
            input_path = str(sample.get('export_path')) + "/images"
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input path not found: {input_path}")
                return sample

            # 查找源图像文件
            input_path = Path(input_path)
            src_files = list(input_path.glob("*.jpg"))
            src_files.extend(list(input_path.glob("*.png")))

            if not src_files:
                logger.warning("未找到源图像文件")
                return sample

            # 创建增强器
            augmenter = ImageAugmenter(
                coord_cache_file=self.coord_cache_file,
                bg_dir=self.bg_dir
            )

            # 执行图像增强
            output_files = augmenter.augment_images(
                src_files=[str(f) for f in src_files],
                scenes=self.allowed_scenes,
                skip_detect=self.skip_detect,
                output_dir=str(input_path)
            )

            # 记录生成的文件路径
            sample['augmented_images'] = output_files
            logger.info(f"成功增强 {len(output_files)} 张图像")

        except Exception as e:
            logger.error(f"Error in ImgAugOperator: {e}")

        return sample
