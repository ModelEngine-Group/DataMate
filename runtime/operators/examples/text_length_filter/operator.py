"""
文本长度过滤器算子
根据设定的最小和最大长度过滤文本数据
"""

import json
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

class TextLengthFilter:
    """文本长度过滤器算子"""
    
    def __init__(self):
        self.name = "text_length_filter"
        self.version = "1.0.0"
    
    def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行文本长度过滤"""
        
        logger.info(f"开始执行算子: {self.name}")
        
        # 获取参数
        parameters = config.get('parameters', {})
        min_length = parameters.get('min_length', 10)
        max_length = parameters.get('max_length', 1000)
        text_field = parameters.get('text_field', 'text')
        
        logger.info(f"过滤参数: min_length={min_length}, max_length={max_length}, text_field={text_field}")
        
        # 验证参数
        if min_length < 0:
            raise ValueError("min_length must be >= 0")
        if max_length < min_length:
            raise ValueError("max_length must be >= min_length")
        
        # 读取输入数据
        input_path = context['input_path']
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        if not isinstance(input_data, list):
            raise ValueError("输入数据必须是数组格式")
        
        logger.info(f"输入数据条数: {len(input_data)}")
        
        # 执行过滤
        filtered_data = []
        stats = {
            'total_input': len(input_data),
            'too_short': 0,
            'too_long': 0,
            'filtered_out': 0,
            'kept': 0
        }
        
        for i, item in enumerate(input_data):
            try:
                # 提取文本内容
                if isinstance(item, str):
                    text = item
                elif isinstance(item, dict) and text_field in item:
                    text = str(item[text_field])
                else:
                    logger.warning(f"跳过无法处理的数据项 {i}: {type(item)}")
                    stats['filtered_out'] += 1
                    continue
                
                # 检查长度
                text_length = len(text)
                
                if text_length < min_length:
                    stats['too_short'] += 1
                    stats['filtered_out'] += 1
                elif text_length > max_length:
                    stats['too_long'] += 1
                    stats['filtered_out'] += 1
                else:
                    filtered_data.append(item)
                    stats['kept'] += 1
                
                # 进度报告
                if (i + 1) % 1000 == 0:
                    progress = (i + 1) / len(input_data) * 100
                    logger.info(f"处理进度: {progress:.1f}% ({i + 1}/{len(input_data)})")
                    
            except Exception as e:
                logger.warning(f"处理数据项 {i} 时出错: {e}")
                stats['filtered_out'] += 1
                continue
        
        # 保存结果
        output_path = context['output_path']
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        # 准备返回结果
        result = {
            'status': 'success',
            'statistics': stats,
            'filter_rate': stats['filtered_out'] / stats['total_input'] * 100 if stats['total_input'] > 0 else 0,
            'output_path': output_path
        }
        
        logger.info(f"过滤完成: {stats}")
        logger.info(f"过滤率: {result['filter_rate']:.2f}%")
        
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置参数"""
        errors = []
        parameters = config.get('parameters', {})
        
        min_length = parameters.get('min_length')
        max_length = parameters.get('max_length')
        
        if min_length is not None and not isinstance(min_length, int):
            errors.append("min_length must be an integer")
        
        if max_length is not None and not isinstance(max_length, int):
            errors.append("max_length must be an integer")
        
        if min_length is not None and min_length < 0:
            errors.append("min_length must be >= 0")
        
        if min_length is not None and max_length is not None and max_length < min_length:
            errors.append("max_length must be >= min_length")
        
        return errors

def create_operator():
    """算子工厂函数"""
    return TextLengthFilter()
