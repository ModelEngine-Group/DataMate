# -*- coding: utf-8 -*-
"""
结婚证盖章算子 - MarriageAddSeal
在结婚证图片上添加结婚登记专用章，登记机关名从 random_content.json 按 group_id 读取。
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper

from .src.seal_marriage import (
    create_round_seal,
    add_seal_to_voucher,
    apply_paper_texture,
    scale_seal_to_fit,
    anchor_to_pixel,
    clamp_center_for_seal,
    load_voucher,
)


class MarriageAddSeal(Mapper):
    """结婚证盖章：读取 export_path 下图片与 random_content.json，按 group_id 取登记机关，添加印章。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seal_size = int(kwargs.get('sealSizeParam', 280))
        self.default_agency = (kwargs.get('agencyNameParam') or '深圳市民政局南山区').strip()

    def _load_groupid_to_agency(self, export_path: str) -> Dict[str, str]:
        json_path = os.path.join(export_path, 'random_content.json')
        if not os.path.exists(json_path):
            return {}
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            out = {}
            for g in data.get('generated_groups', []):
                gid = g.get('group_id')
                if not gid:
                    continue
                for item in g.get('contents', []):
                    if item.get('label') == '登记机关':
                        out[str(gid)] = item.get('text') or self.default_agency
                        break
            return out
        except Exception as e:
            logger.warning(f"MarriageAddSeal: 读取 random_content.json 失败: {e}")
            return {}

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            export_path = sample.get('export_path')
            if not export_path or not os.path.exists(export_path):
                logger.warning("MarriageAddSeal: 未找到 export_path")
                return sample

            export_path = str(Path(export_path).resolve())
            groupid_to_agency = self._load_groupid_to_agency(export_path)

            img_files = []
            for ext in ('*.jpg', '*.jpeg', '*.png'):
                img_files.extend(Path(export_path).glob(ext))
            if not img_files:
                logger.warning("MarriageAddSeal: 未找到图片文件")
                return sample

            for img_path in img_files:
                try:
                    stem = img_path.stem
                    company_name = groupid_to_agency.get(stem) or self.default_agency
                    seal = create_round_seal(
                        company_name,
                        seal_type="结婚登记专用章",
                        size=self.seal_size,
                    )
                    voucher = load_voucher(str(img_path))
                    voucher_size = voucher.size
                    pos = anchor_to_pixel(voucher_size, 'bottom-right', margin=(450, 350))
                    max_w = int(voucher_size[0] * 0.25)
                    max_h = int(voucher_size[1] * 0.35)
                    seal = scale_seal_to_fit(seal, max_w, max_h)
                    pos = clamp_center_for_seal(pos, voucher_size, seal.size)
                    result = add_seal_to_voucher(
                        voucher.convert('RGBA'),
                        seal,
                        position=pos,
                        gradient_direction=None,
                        wear_intensity=0.2,
                        rotation=0,
                    )
                    result = apply_paper_texture(result, intensity=0.03)
                    out_path = img_path
                    if result.mode == 'RGBA':
                        result = result.convert('RGB')
                    result.save(str(out_path), quality=95)
                    logger.info(f"MarriageAddSeal: 已盖章 {img_path.name}")
                except Exception as e:
                    logger.error(f"MarriageAddSeal: 处理 {img_path} 失败: {e}")
        except Exception as e:
            logger.error(f"MarriageAddSeal execute error: {e}")
            import traceback
            traceback.print_exc()
        return sample
