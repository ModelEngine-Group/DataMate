# -*- coding: utf-8 -*-
"""
结婚证模板贴图算子 - MarriageImageCompositing
将 random_content.json 中的文本渲染到模板图上，按 group_id 输出多张图片。
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper

from .src.compositor import compose_all, load_json


class MarriageImageCompositing(Mapper):
    """结婚证模板贴图：读取 random_content + 模板 + 坐标，输出多张 group_id.jpg。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_path = (kwargs.get('templatePath') or '').strip()
        self.coords_path = (kwargs.get('coordsPath') or '').strip()

    def _resolve_paths(self, sample: Dict[str, Any]) -> tuple:
        """解析模板、坐标、文本路径。export_path 为当前任务输出目录（内含 random_content.json）。"""
        export_path = sample.get('export_path') or sample.get('filePath') or ''
        export_path = str(Path(export_path).resolve())
        texts_path = os.path.join(export_path, 'random_content.json')

        template_path = self.template_path
        if not template_path or not os.path.exists(template_path):
            # 尝试 export_path 同级或上级的 template.jpg
            for base in [export_path, str(Path(export_path).parent)]:
                candidate = os.path.join(base, 'template.jpg')
                if os.path.exists(candidate):
                    template_path = candidate
                    break
            if not template_path or not os.path.exists(template_path):
                return '', '', '', export_path

        coords_path = self.coords_path
        if not coords_path or not os.path.exists(coords_path):
            for base in [export_path, str(Path(export_path).parent)]:
                candidate = os.path.join(base, 'coordinate_info.json')
                if os.path.exists(candidate):
                    coords_path = candidate
                    break
            if not coords_path or not os.path.exists(coords_path):
                return template_path, '', texts_path, export_path

        return template_path, coords_path, texts_path, export_path

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            template_path, coords_path, texts_path, out_dir = self._resolve_paths(sample)
            if not template_path or not os.path.exists(template_path):
                logger.warning("MarriageImageCompositing: 未找到模板图 template.jpg")
                return sample
            if not coords_path or not os.path.exists(coords_path):
                logger.warning("MarriageImageCompositing: 未找到坐标 coordinate_info.json")
                return sample
            if not os.path.exists(texts_path):
                logger.warning("MarriageImageCompositing: 未找到 random_content.json")
                return sample

            coords_data = load_json(coords_path)
            if not isinstance(coords_data, list):
                logger.warning("MarriageImageCompositing: 坐标 JSON 格式应为 list")
                return sample

            with open(texts_path, 'r', encoding='utf-8') as f:
                texts_json = json.load(f)

            os.makedirs(out_dir, exist_ok=True)
            saved = compose_all(
                template_path=template_path,
                coords_json=coords_data,
                texts_json=texts_json,
                font_paths=None,
                out_dir=out_dir,
            )
            for p in saved:
                logger.info(f"MarriageImageCompositing: 已保存 {p}")
        except Exception as e:
            logger.error(f"MarriageImageCompositing execute error: {e}")
            import traceback
            traceback.print_exc()
        return sample
