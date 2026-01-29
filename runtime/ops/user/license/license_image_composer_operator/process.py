# -*- coding: utf-8 -*-

"""
图像合成算子：ImageComposerOperator
将数据渲染到营业执照模板上
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper
from .src.image_composer import compose_all


class LicenseImageComposerOperator(Mapper):
    """
    图像合成算子
    将数据渲染到营业执照模板上
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 metadata.yml 的参数获取配置
        self.font_path = kwargs.get('fontParam', '')
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行图像合成
        
        Args:
            sample: 输入的数据样本，包含 texts_json, coords_file, template 等字段
        
        Returns:
            处理后的数据样本，包含生成的图片路径
        """
        try:
            # 获取输入路径
            file_path = sample.get('filePath')
            if not file_path.endswith('.jpg') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            parent_path = Path(file_path).parent

            coords_files = list(Path(parent_path).glob("*.json"))
            if len(coords_files) == 0:
                sample['text'] = ""
                logger.error(f"坐标文件不存在: {coords_files}")
                return sample
            coords_file = coords_files[0]

            template_paths = list(Path(parent_path).glob("*.jpg"))
            if len(template_paths) == 0:
                sample['text'] = ""
                logger.error(f"坐标文件不存在: {template_paths}")
                return sample
            template_path = template_paths[0]
            
            if not os.path.exists(template_path):
                logger.error(f"模板文件不存在: {template_path}")
                return sample

            output_dir = sample.get('export_path') + "/images"
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 解析坐标
            with open(coords_file, 'r') as file:
                coords = json.load(file)
            logger.info(f"读取到 {len(coords)} 个坐标区域")
            
            # 解析文本
            texts_json_data = json.loads(sample.get('text'))
            logger.info(f"读取到 {len(texts_json_data.get('generated_groups', []))} 条记录")
            
            # 准备字体路径列表
            font_paths = [self.font_path] if self.font_path else []
            
            # 生成图片
            logger.info("开始生成图片...")
            saved_files = compose_all(
                template_path,
                coords,
                texts_json_data,
                font_paths=font_paths,
                out_dir=output_dir
            )
            logger.info(f"已生成 {len(saved_files)} 张图片")
            
        except Exception as e:
            logger.error(f"ImageComposerOperator 执行失败: {e}")
        
        return sample
