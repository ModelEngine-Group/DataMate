# -*- coding: utf-8 -*-
"""结婚证模板贴图逻辑，从 MarriageCertificate/image_compositing 抽取。"""
import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

CSS_COLOR_NAMES = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'red': (255, 0, 0),
    'green': (0, 128, 0),
    'blue': (0, 0, 255),
}


def load_json(path: str) -> Any:
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_color(s: str) -> Tuple[int, int, int]:
    if not s:
        raise ValueError('empty color')
    s = s.strip()
    if s.startswith('#'):
        hexv = s[1:]
        if len(hexv) == 6:
            return (int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16))
        raise ValueError('unsupported hex color')
    m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    name = s.lower()
    if name in CSS_COLOR_NAMES:
        return CSS_COLOR_NAMES[name]
    raise ValueError(f'unknown color: {s}')


def find_font(font_name_or_path: Optional[str], fallback_dirs=None) -> Optional[str]:
    if not font_name_or_path:
        return None
    if os.path.exists(font_name_or_path):
        return font_name_or_path
    dirs = list(fallback_dirs) if fallback_dirs else []
    dirs.extend(["/usr/share/fonts", "/usr/local/share/fonts", "./fonts", "C:/Windows/Fonts"])
    for d in dirs:
        try:
            for fname in os.listdir(d):
                if fname.lower().startswith(font_name_or_path.lower()):
                    return os.path.join(d, fname)
        except Exception:
            continue
    try:
        ImageFont.truetype(font_name_or_path, 12)
        return font_name_or_path
    except Exception:
        return None


def _find_region_rects(coords_json: List, template_size: Tuple[int, int]) -> List[Dict]:
    regions = []
    tw, th = template_size
    for item in coords_json:
        annotations = item.get('annotations', [])
        for ann in annotations:
            for res in ann.get('result', []):
                val = res.get('value', {})
                lbls = val.get('rectanglelabels') or val.get('labels') or []
                label = lbls[0] if isinstance(lbls, list) and len(lbls) > 0 else None
                if label is None:
                    continue
                x_pct = float(val.get('x', 0))
                y_pct = float(val.get('y', 0))
                w_pct = float(val.get('width', 0))
                h_pct = float(val.get('height', 0))
                left = int((x_pct / 100.0) * tw)
                top = int((y_pct / 100.0) * th)
                w = (w_pct / 100.0) * tw
                h = (h_pct / 100.0) * th
                left = max(0, min(left, int(tw - max(1, w))))
                top = max(0, min(top, int(th - max(1, h))))
                region = {
                    'label': label,
                    'left': left,
                    'top': top,
                    'width': int(max(1, round(w))),
                    'height': int(max(1, round(h))),
                }
                for opt in ('font', 'font_size', 'color', 'align', 'valign'):
                    v = val.get(opt)
                    if v is not None:
                        region[opt] = v
                regions.append(region)
    return regions


def _measure_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
    except Exception:
        try:
            size = font.getsize(text)
            return size
        except Exception:
            return (len(text) * 6, 10)


def _render_text_into_region(
    image: Image.Image,
    region: Dict,
    text: str,
    font_path: Optional[str] = None,
    font_size: int = 36,
    color: Tuple[int, int, int] = (0, 0, 0),
) -> None:
    draw = ImageDraw.Draw(image)
    left = region['left']
    top = region['top']
    width = max(1, region['width'])
    height = max(1, region['height'])
    font = None
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    if font is None:
        chinese_fonts = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        for font_file in chinese_fonts:
            try:
                if os.path.exists(font_file):
                    font = ImageFont.truetype(font_file, font_size)
                    break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    text_w, text_h = _measure_text(draw, text, font)
    fs = font_size
    while text_w > width and fs > 6:
        fs -= 1
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, fs)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        text_w, text_h = _measure_text(draw, text, font)
    x = left + (width - text_w) / 2
    y = top + (height - text_h) / 2
    draw.text((x, y), text, font=font, fill=color)


def compose_all(
    template_path: str,
    coords_json: List,
    texts_json: Any,
    font_paths: Optional[List[str]] = None,
    out_dir: str = 'output',
) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(template_path):
        template = Image.open(template_path).convert('RGB')
    else:
        tw, th = 800, 600
        for item in coords_json:
            for ann in item.get('annotations', []):
                for res in ann.get('result', []):
                    ow = res.get('original_width')
                    oh = res.get('original_height')
                    if ow and oh:
                        tw, th = int(ow), int(oh)
                        break
        template = Image.new('RGB', (tw, th), color='white')
    tw, th = template.size
    regions = _find_region_rects(coords_json, (tw, th))
    label_map = {r['label']: r for r in regions}
    font_candidate = font_paths[0] if font_paths and len(font_paths) > 0 else None
    if font_candidate is None:
        for c in ['FangSong_GB2312.ttf', 'STFangsong.ttf', 'simsun.ttc', 'simhei.ttf']:
            tryp = find_font(c)
            if tryp:
                font_candidate = tryp
                break
    default_text_color = (64, 64, 64)
    groups = []
    if isinstance(texts_json, dict) and 'generated_groups' in texts_json:
        groups = texts_json['generated_groups']
    elif isinstance(texts_json, list):
        groups = texts_json
    elif isinstance(texts_json, dict):
        groups = [{'group_id': 1, 'contents': [{'label': k, 'text': v} for k, v in texts_json.items()]}]
    else:
        return []
    saved = []
    for idx, g in enumerate(groups, 1):
        img = template.copy()
        contents = g.get('contents', [])
        for c in contents:
            label = c.get('label')
            text = c.get('text', '')
            if text is None or (isinstance(text, str) and text.strip() == ''):
                continue
            region = label_map.get(label)
            if region is None:
                continue
            resolved_font = find_font(region.get('font')) or (region.get('font') if os.path.exists(str(region.get('font', ''))) else None) or font_candidate
            reg_fs = region.get('font_size')
            try:
                reg_fs = int(reg_fs) if reg_fs is not None else 36
            except Exception:
                reg_fs = 36
            color = default_text_color
            if region.get('color'):
                try:
                    color = parse_color(region['color'])
                except Exception:
                    pass
            _render_text_into_region(img, region, text, font_path=resolved_font, font_size=reg_fs, color=color)
        group_id = g.get('group_id') or idx
        gid_str = str(group_id) if group_id is not None else ''
        safe_gid = re.sub(r'[^A-Za-z0-9._-]', '_', gid_str).strip()
        fname = f'{safe_gid}.jpg' if safe_gid else f'group_{idx}.jpg'
        out_path = os.path.join(out_dir, fname)
        img.save(out_path)
        saved.append(out_path)
        img.close()
    return saved
