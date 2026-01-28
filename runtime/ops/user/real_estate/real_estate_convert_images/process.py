"""
图像转换算子 - 不动产权证
"""
import os
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from datamate.core.base_op import Mapper
from .src import ImageConverter

class RealEstateDocToImgOperator(Mapper):
    """
    文档转图片算子：RealEstateDocToImgOperator
    将JSON数据渲染到模板图像上
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.dpi = int(kwargs.get('dpiParam', 200))
        self.pattern = kwargs.get('patternParam', "*.json")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            # 获取输入文件路径
            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input file not found: {input_path}")
                return sample

            # 查找JSON文件
            input_path = Path(input_path)
            json_files = list(input_path.glob(self.pattern))

            if not json_files:
                logger.warning(f"未找到匹配的JSON文件: {self.pattern}")
                return sample

            full_path = sample.get('filePath')
            folder_path = os.path.dirname(full_path)
            # 创建转换器
            converter = ImageConverter(
                output_dir=str(input_path),
                input_dir=folder_path,
                dpi=self.dpi,
                instance_id=str(sample.get("instance_id", "001"))
            )

            # 批量转换
            output_files = converter.convert_batch([str(f) for f in json_files])

            # 记录生成的文件路径
            sample['generated_images'] = output_files
            logger.info(f"成功生成 {len(output_files)} 张图像")

        except Exception as e:
            logger.error(f"Error converting data to image: {e}")

        return sample
