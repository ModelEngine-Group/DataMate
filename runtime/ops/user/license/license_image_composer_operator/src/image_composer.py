"""
图像合成模块
提供营业执照文本渲染和图像合成功能
"""
import re
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
import os

# ============================================================================
# 文本渲染功能
# ============================================================================
CSS_COLOR_NAMES = {
    'black': (0,0,0),
    'white': (255,255,255),
    'red': (255,0,0),
    'green': (0,128,0),
    'blue': (0,0,255),
}

def parse_color(s: str):
    """解析颜色字符串为RGB元组"""
    if not s:
        raise ValueError('empty color')
    s = s.strip()
    if s.startswith('#'):
        hexv = s[1:]
        if len(hexv) == 6:
            r = int(hexv[0:2], 16)
            g = int(hexv[2:4], 16)
            b = int(hexv[4:6], 16)
            return (r,g,b)
        raise ValueError('unsupported hex color')
    m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    name = s.lower()
    if name in CSS_COLOR_NAMES:
        return CSS_COLOR_NAMES[name]
    raise ValueError(f'unknown color: {s}')

def find_font(font_name_or_path: Optional[str], fallback_dirs=None) -> Optional[str]:
    """Try to resolve a font path. If argument is a path and exists, return it.
    If it's a name, search common system folders and provided fallback_dirs.
    Returns None if not found.
    """
    if not font_name_or_path:
        return None
    if os.path.exists(font_name_or_path):
        return font_name_or_path
    # try as simple name in fallback dirs
    dirs = []
    if fallback_dirs:
        dirs.extend(fallback_dirs)
    # common places
    dirs.extend(["/usr/share/fonts", "/usr/local/share/fonts", "./fonts", "C:/Windows/Fonts"])
    for d in dirs:
        try:
            for fname in os.listdir(d):
                if fname.lower().startswith(font_name_or_path.lower()):
                    return os.path.join(d, fname)
        except Exception:
            continue
    # last resort: let PIL try by name (not guaranteed)
    try:
        ImageFont.truetype(font_name_or_path, 12)
        return font_name_or_path
    except Exception:
        return None


def measure_text(draw, text, font):
    """Measure text width and height in pixels, compatible across Pillow versions."""
    try:
        # ImageFont.getsize
        size = font.getsize(text)
        return size[0], size[1]
    except Exception:
        pass
    try:
        # ImageDraw.textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        # fallback approximate
        return (len(text) * 6, 10)


def render_text_into_region(image, region, text, font_path=None, font_size=36, color=(0,0,0)):
    """
    将文本渲染到指定区域
    Args:
        image: PIL图像对象
        region: 区域字典，包含left, top, width, height等键
        text: 要渲染的文本
        font_path: 字体文件路径
        font_size: 字体大小
        color: 文本颜色(RGB元组)
    """
    draw = ImageDraw.Draw(image)
    left = region['left']
    top = region['top']
    width = max(1, region['width'])
    height = max(1, region['height'])

    # load font: try Chinese fonts first
    font = None
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            pass

    # If no font_path or failed to load, try common Windows Chinese fonts
    if font is None:
        chinese_fonts = [
            'C:/Windows/Fonts/simsun.ttc',      # 宋体
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
            'C:/Windows/Fonts/msyhbd.ttc',      # 微软雅黑粗体
            'C:/Windows/Fonts/simkai.ttf',      # 楷体
            'arial.ttf'                         # fallback
        ]

        for font_file in chinese_fonts:
            try:
                font = ImageFont.truetype(font_file, font_size)
                break
            except Exception:
                continue

    # Final fallback to default
    if font is None:
        font = ImageFont.load_default()

    # measure text (no auto-scaling for consistent font size)
    text_w, text_h = measure_text(draw, text, font)
    # left-top alignment
    x = left
    y = top
    draw.text((x,y), text, font=font, fill=color)


# ============================================================================
# 图像合成功能
# ============================================================================

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def find_region_rects(coords_json, template_size):
    """Parse LabelStudio-like coords JSON and return a list of regions.
    Each region: dict with keys: label, x, y, width, height (in pixels, left-top origin)
    coords_json expected to be a list as in input/坐标信息.json
    template_size: (width, height) in pixels
    """
    regions = []
    if not isinstance(coords_json, list):
        raise ValueError("coords_json must be a list")
    for item in coords_json:
        annotations = item.get('annotations', [])
        for ann in annotations:
            for res in ann.get('result', []):
                val = res.get('value', {})
                # value contains x,y,width,height as percentages
                lbls = val.get('rectanglelabels') or val.get('labels') or []
                label = lbls[0] if isinstance(lbls, list) and len(lbls) > 0 else None
                if label is None:
                    continue
                # percentages (0-100)
                x_pct = float(val.get('x', 0))
                y_pct = float(val.get('y', 0))
                w_pct = float(val.get('width', 0))
                h_pct = float(val.get('height', 0))
                tw, th = template_size
                # interpret x,y as top-left percentages (not center)
                left = int(x_pct / 100.0 * tw)
                top = int(y_pct / 100.0 * th)
                w = w_pct / 100.0 * tw
                h = h_pct / 100.0 * th
                # clamp within template bounds
                left = max(0, min(left, int(tw - max(1, w))))
                top = max(0, min(top, int(th - max(1, h))))
                # collect optional styling fields if present
                region = {
                    'label': label,
                    'left': left,
                    'top': top,
                    'width': int(max(1, round(w))),
                    'height': int(max(1, round(h))),
                }
                # optional style keys from annotation value
                for opt in ('font', 'font_size', 'color', 'align', 'valign'):
                    v = val.get(opt)
                    if v is not None:
                        region[opt] = v
                regions.append(region)
    return regions


def compose_all(template_path, coords_json, texts_json, font_paths=None, out_dir='output'):
    """Compose multiple images based on coords and texts.
    - template_path: path to template image, if missing create a blank image
    - coords_json: parsed JSON from 坐标信息.json
    - texts_json: parsed JSON from 文本内容.json
    - font_paths: list of font file paths (not used in minimal impl)
    - out_dir: output directory
    Returns list of saved file paths
    """
    _ensure_dir(out_dir)
    # load template
    if os.path.exists(template_path):
        template = Image.open(template_path).convert('RGB')
    else:
        # create blank white template with reasonable default size based on coords original sizes
        # try to infer from coords_json
        tw, th = 800, 600
        try:
            # search for original_width and original_height in coords_json
            for item in coords_json:
                annotations = item.get('annotations', [])
                for ann in annotations:
                    for res in ann.get('result', []):
                        ow = res.get('original_width')
                        oh = res.get('original_height')
                        if ow and oh:
                            tw = int(ow)
                            th = int(oh)
                            raise StopIteration
        except StopIteration:
            pass
        template = Image.new('RGB', (tw, th), color='white')
    tw, th = template.size
    # parse regions
    regions = find_region_rects(coords_json, (tw, th))
    # build dictionary label->region (if multiple with same label, take first)
    label_map = {}
    for r in regions:
        if r['label'] not in label_map:
            label_map[r['label']] = r
    saved = []
    # pick first font path if provided (pass-through); otherwise None
    font_candidate = font_paths[0] if font_paths and len(font_paths) > 0 else None
    # default to a FangSong (仿宋) font when available to match traditional certificate style
    if font_candidate is None:
        fang_candidates = ['FangSong_GB2312.ttf', '仿ong.ttf', '仿宋_GB2312.ttf', 'FangSong.ttf', 'STFangsong.ttf', 'Fangsong.ttf', '仿宋.ttf']
        for c in fang_candidates:
            tryp = find_font(c)
            if tryp:
                font_candidate = tryp
                break
    # default text color: darker gray for better visibility
    default_text_color = (32, 32, 32)
    # parse texts_json: expected format like input/文本内容.json
    groups = []
    if isinstance(texts_json, dict) and 'generated_groups' in texts_json:
        groups = texts_json['generated_groups']
    elif isinstance(texts_json, list):
        groups = texts_json
    elif isinstance(texts_json, dict):
        groups = [ {'group_id': 1, 'contents': [ { 'label': k, 'text': v } for k,v in texts_json.items() ] } ]
    else:
        raise ValueError('Unsupported texts_json format')
    # for each group, render and save
    idx = 0
    for g in groups:
        idx +=1
        img = template.copy()
        # note: debug box drawing removed so main outputs contain only composed text
        # place each content
        contents = g.get('contents', [])
        for c in contents:
            label = c.get('label')
            text = c.get('text', '')
            # skip empty or whitespace-only text (do not render)
            if text is None:
                continue
            if isinstance(text, str) and text.strip() == '':
                continue
            region = label_map.get(label)
            if region is None:
                # skip if no region
                continue
            # determine font_path: region override -> global candidate
            reg_font = region.get('font')
            resolved_font = None
            if reg_font:
                # try as path or name
                resolved_font = find_font(reg_font)
                if resolved_font is None:
                    # if reg_font looks like a path and exists, use it
                    if os.path.exists(reg_font):
                        resolved_font = reg_font
            if resolved_font is None:
                resolved_font = font_candidate
            # determine font_size (doubled default for business license)
            reg_fs = region.get('font_size')
            try:
                reg_fs = int(reg_fs) if reg_fs is not None else 72
            except Exception:
                reg_fs = 72
            # determine color
            color = default_text_color
            reg_color = region.get('color')
            if reg_color:
                try:
                    color = parse_color(reg_color)
                except Exception:
                    color = default_text_color
            render_text_into_region(img, region, text, font_path=resolved_font, font_size=reg_fs, color=color)
        # save file
        group_id = g.get('group_id') or idx
        # 获取法定代表人姓名
        legal_rep_name = ''
        for c in contents:
            if c.get('label') == '法定代表人姓名':
                legal_rep_name = c.get('text', '')
                break
        # 生成7位数字ID（从0000001开始）
        id_str = f'{idx:07d}'
        # 按照格式命名："企业法人营业执照"-"ID"-"姓名".jpg
        fname = f'企业法人营业执照-{id_str}-{legal_rep_name}.jpg'
        out_path = os.path.join(out_dir, fname)
        img.save(out_path)
        saved.append(out_path)
        img.close()
    return saved
