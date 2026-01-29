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
        """辅助文件（模板、坐标）从源数据集 source_dir 解析；random_content 仅从 export_path 读；输出仅写 export_path。"""
        export_path = sample.get('export_path') or ''
        export_path = str(Path(export_path).resolve()) if export_path else ''
        texts_path = os.path.join(export_path, 'random_content.json') if export_path else ''

        file_path = sample.get('filePath') or ''
        source_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else ''

        # 辅助文件（源数据集）：模板、坐标
        template_path = self.template_path if (self.template_path and os.path.exists(self.template_path)) else ''
        if not template_path and source_dir:
            candidate = os.path.join(source_dir, 'template.jpg')
            if os.path.exists(candidate):
                template_path = candidate
        if not template_path:
            return '', '', texts_path, export_path

        coords_path = self.coords_path if (self.coords_path and os.path.exists(self.coords_path)) else ''
        if not coords_path:
            if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.json'):
                coords_path = file_path
            elif source_dir:
                candidate = os.path.join(source_dir, 'coordinate_info.json')
                if os.path.exists(candidate):
                    coords_path = candidate
        if not coords_path:
            return template_path, '', texts_path, export_path

        return template_path, coords_path, texts_path, export_path

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            export_path = sample.get('export_path')
            if not export_path:
                logger.warning("MarriageImageCompositing: 缺少 export_path")
                return sample
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
