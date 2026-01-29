# -*- coding: utf-8 -*-
"""
结婚证 QA 对生成算子 - MarriageFormQA
从 export_path 下递归收集图片与 random_content.json，生成 llama 格式 QA 对并写入 jsonl。
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper

from .src.qa_builder import build_qa_pairs_from_directory


class MarriageFormQA(Mapper):
    """结婚证 QA 对生成：读取 export_path 下图片与 random_content.json，输出 output_qa_pairs.jsonl。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        preview_val = kwargs.get('previewCountParam', 5)
        try:
            self.preview_count = int(preview_val) if preview_val is not None else 5
        except (TypeError, ValueError):
            self.preview_count = 5

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            export_path = sample.get('export_path')
            if not export_path or not os.path.exists(export_path):
                logger.warning("MarriageFormQA: 未找到 export_path")
                return sample

            export_path = str(Path(export_path).resolve())
            result = build_qa_pairs_from_directory(
                base_path=export_path,
                json_path=None,
                preview_count=self.preview_count,
            )

            if not result:
                logger.warning("MarriageFormQA: 未生成任何 QA 对")
                return sample

            out_path = os.path.join(export_path, 'output_qa_pairs.jsonl')
            with open(out_path, 'w', encoding='utf-8') as f:
                for item in result:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            logger.info(f"MarriageFormQA: 已生成 {len(result)} 条 QA 对 -> {out_path}")

            preview_path = os.path.join(export_path, 'output_qa_pairs_preview.json')
            with open(preview_path, 'w', encoding='utf-8') as f:
                json.dump(result[: self.preview_count], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"MarriageFormQA execute error: {e}")
            import traceback
            traceback.print_exc()
        return sample
