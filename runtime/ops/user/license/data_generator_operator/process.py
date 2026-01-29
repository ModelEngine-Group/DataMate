# -*- coding: utf-8 -*-

"""
数据生成算子：DataGeneratorOperator
基于坐标文件生成随机的营业执照数据
"""
import json
import os
import random
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper


class DataGeneratorOperator(Mapper):
    """
    数据生成算子
    基于坐标文件生成随机的营业执照数据
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 metadata.yml 的参数获取配置
        self.num = int(kwargs.get('numParam', 5))
        self.seed = kwargs.get('seedParam', '42')
        
        # 设置随机种子
        if self.seed:
            try:
                random.seed(int(self.seed))
            except ValueError:
                logger.warning(f"无效的随机种子: {self.seed}，使用默认值")
                random.seed(42)
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据生成
        
        Args:
            sample: 输入的数据样本，包含 coords_file 等字段
        
        Returns:
            处理后的数据样本，包含生成的数据
        """
        try:
            # 获取坐标文件路径
            # 支持从 sample 中获取或使用默认路径
            file_path = sample.get('filePath')
            if not file_path.endswith('.jpg'):
                sample['text'] = ""
                return sample

            parent_path = Path(file_path).parent
            coords_files = list(Path(parent_path).glob("*.json"))

            if len(coords_files) == 0:
                sample['text'] = ""
                logger.error(f"坐标文件不存在: {coords_files}")
                return sample

            coords_file = coords_files[0]
            
            # 检查文件是否存在
            if not os.path.exists(coords_file):
                logger.error(f"坐标文件不存在: {coords_file}")
                return sample
            
            # 导入核心模块
            from .src.data_generator import generate_groups
            
            # 生成数据
            groups = generate_groups(coords_file, self.num)
            sample['text'] = json.dumps({'generated_groups': groups})
            logger.info(f"已生成 {len(groups)} 条记录")
            
        except Exception as e:
            logger.error(f"DataGeneratorOperator 执行失败: {e}")
        
        return sample
