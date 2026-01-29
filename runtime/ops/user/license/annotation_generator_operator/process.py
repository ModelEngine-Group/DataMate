# -*- coding: utf-8 -*-

"""
标注生成算子：AnnotationGeneratorOperator
为图片生成问答对标注数据
"""

import json
import os
import random
from typing import Dict, Any, List

from loguru import logger
from datamate.core.base_op import Mapper


class AnnotationGeneratorOperator(Mapper):
    """
    标注生成算子
    为图片生成问答对标注数据
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 metadata.yml 的参数获取配置
        self.qa_count = int(kwargs.get('qaCountParam', 3))
        self.train_ratio = float(kwargs.get('trainRatioParam', 0.8))
        
        # 设置随机种子
        seed = kwargs.get('seedParam', None)
        if seed:
            try:
                random.seed(int(seed))
            except ValueError:
                logger.warning(f"无效的随机种子: {seed}，使用默认值")
                random.seed(42)

    def generate_conversations(self, dataset: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成conversations.json"""
        conversations = []
        conv_id = 0

        for split in ['train', 'validation', 'test']:
            for item in dataset[split]:
                image_path = item['images'][0]
                # 遍历消息对
                msg_list = item['messages']
                for i in range(0, len(msg_list), 2):
                    if i + 1 < len(msg_list):
                        user_msg = msg_list[i]
                        assistant_msg = msg_list[i + 1]
                        if user_msg['role'] == 'user' and assistant_msg['role'] == 'assistant':
                            conversations.append({
                                "id": f"{conv_id}",
                                "images": item['images'],
                                "question": user_msg['content'],
                                "answer": assistant_msg['content']
                            })
                            conv_id += 1

        return conversations

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行标注生成
        
        Args:
            sample: 输入的数据样本，包含 images_dir, texts_json, export_path 等字段
        
        Returns:
            处理后的数据样本，包含生成的标注数据
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.jpg'):
                sample['text'] = ""
                return sample

            # 获取输入路径
            texts_json_data = json.loads(sample.get('text'))
            output_dir = sample.get('export_path')
            images_dir = output_dir + "/images"
            
            # 检查文件是否存在
            if not os.path.exists(images_dir):
                logger.error(f"图片目录不存在: {images_dir}")
                return sample
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 导入核心模块
            logger.info(f"读取到 {len(texts_json_data.get('generated_groups', []))} 条记录")

            from .src.annotation_builder import generate_dataset

            generate_dataset(texts_json_data.get('generated_groups', []), images_dir=images_dir, output_dir=output_dir)

            sample['text'] = ""

        except Exception as e:
            logger.error(f"AnnotationGeneratorOperator 执行失败: {e}")
            raise e
        
        return sample
