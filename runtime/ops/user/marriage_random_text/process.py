# -*- coding: utf-8 -*-
"""
结婚证随机文本算子 - MarriageRandomText
从 coordinate_info.json 生成多组随机结婚证文本，输出 random_content.json。
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper

from .src.text_generator import process_coordinate_and_generate


class MarriageRandomText(Mapper):
    """结婚证随机文本生成算子：读取坐标 JSON，生成多组随机文本，写入 random_content.json。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        num_val = kwargs.get('numParam', 5)
        self.num_generate = int(num_val) if num_val is not None else 5

    def _resolve_input_file(self, sample: Dict[str, Any]) -> str:
        """输入仅使用 sample['filePath']，且必须为 .json 文件（源数据集当前被处理文件）。"""
        file_path = sample.get('filePath') or ''
        if not file_path:
            return ''
        file_path = os.path.abspath(file_path)
        if not os.path.isfile(file_path) or not file_path.lower().endswith('.json'):
            return ''
        return file_path

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            input_file = self._resolve_input_file(sample)
            if not input_file:
                logger.warning("MarriageRandomText: filePath 为空或非 .json 文件，跳过")
                return sample

            export_path = sample.get('export_path')
            if not export_path:
                logger.warning("MarriageRandomText: 缺少 export_path")
                return sample

            output_dir = str(Path(export_path).resolve())
            os.makedirs(output_dir, exist_ok=True)

            content_data = process_coordinate_and_generate(
                input_path=input_file,
                output_dir=output_dir,
                num_generate=self.num_generate,
            )
            if content_data is None:
                logger.warning(f"MarriageRandomText: 无法从 {input_file} 提取模板 values")
                return sample

            out_path = os.path.join(output_dir, 'random_content.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
            logger.info(f"MarriageRandomText: 已生成 {self.num_generate} 组数据 -> {out_path}")
        except Exception as e:
            logger.error(f"MarriageRandomText execute error: {e}")
            import traceback
            traceback.print_exc()
        return sample
