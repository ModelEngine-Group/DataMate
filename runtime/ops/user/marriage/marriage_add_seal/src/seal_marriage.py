# -*- coding: utf-8 -*-
"""结婚证盖章逻辑，从 MarriageCertificate/add_seal 抽取。"""
import os
import random
import math
from typing import Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CHINESE_FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def _get_chinese_font() -> Optional[str]:
    for path in CHINESE_FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


CHINESE_FONT = _get_chinese_font()

try:
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_BICUBIC = getattr(Image, 'BICUBIC', 3)
    RESAMPLE_LANCZOS = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))


def create_round_seal(
    company_name: str,
    seal_type: str = "结婚登记专用章",
    size: int = 280,
    color: Tuple[int, int, int] = (200, 30, 30),
    text_margin: int = 28,
) -> Image.Image:
    """创建圆形结婚登记专用章。"""
    if not CHINESE_FONT:
        raise RuntimeError("未找到中文字体，无法生成印章")
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    radius = size // 2 - 10
    draw.ellipse([10, 10, size - 10, size - 10], outline=color, width=3)
    draw.ellipse([16, 16, size - 16, size - 16], outline=color, width=2)
    star_radius = size // 12
    star_points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = star_radius if i % 2 == 0 else star_radius // 2.5
        x = center + int(r * math.cos(angle))
        y = center + int(r * math.sin(angle))
        star_points.append((x, y))
    draw.polygon(star_points, fill=color)
    font = ImageFont.truetype(CHINESE_FONT, size // 8)
    chars = list(company_name)
    n = len(chars)
    start_angle = math.pi
    total_span = math.pi
    angle_step = -total_span / max(n - 1, 1)
    text_radius = radius - text_margin
    for i, char in enumerate(chars):
        angle = start_angle + i * angle_step
        x = center + int(text_radius * math.cos(angle))
        y = center - int(text_radius * math.sin(angle))
        char_img = Image.new('RGBA', (50, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 5), char, fill=color, font=font)
        rotation_angle = math.degrees(angle) - 90
        rotated_char = char_img.rotate(rotation_angle, expand=True, resample=RESAMPLE_BICUBIC)
        paste_x = x - rotated_char.width // 2
        paste_y = y - rotated_char.height // 2
        img.paste(rotated_char, (paste_x, paste_y), rotated_char)
    bottom_font = ImageFont.truetype(CHINESE_FONT, size // 10)
    bbox = draw.textbbox((0, 0), seal_type, font=bottom_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((center - text_w // 2, center + radius // 2 - text_h - 8), seal_type, fill=color, font=bottom_font)
    return img


def add_seal_to_voucher(
    voucher_img: Image.Image,
    seal_img: Image.Image,
    position: Tuple[int, int],
    rotation: float = 0,
    opacity: float = 0.85,
    add_wear: bool = True,
    add_blur: bool = True,
    wear_intensity: float = 0.15,
    gradient_direction: Optional[str] = None,
) -> Image.Image:
    """将印章添加到凭证上。"""
    result = voucher_img.copy().convert('RGBA')
    seal = seal_img.copy()
    if rotation == 0:
        rotation = random.uniform(-8, 8)
    seal = seal.rotate(rotation, expand=True, resample=RESAMPLE_BICUBIC)
    seal_data = np.array(seal)
    seal_data[..., 3] = (seal_data[..., 3] * opacity).astype(np.uint8)
    if add_wear:
        h, w = seal_data.shape[:2]
        if gradient_direction:
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            if gradient_direction == 'left':
                gradient = 1 - (x_coords / w) * 0.5
            elif gradient_direction == 'right':
                gradient = 0.5 + (x_coords / w) * 0.5
            elif gradient_direction == 'top':
                gradient = 1 - (y_coords / h) * 0.5
            elif gradient_direction == 'bottom':
                gradient = 0.5 + (y_coords / h) * 0.5
            else:
                gradient = np.ones((h, w))
        else:
            gradient = np.ones((h, w))
        small_size = max(h, w) // 10
        small_noise = np.random.random((small_size, small_size))
        noise_img = Image.fromarray((small_noise * 255).astype(np.uint8), mode='L')
        noise_img = noise_img.resize((w, h), resample=RESAMPLE_BICUBIC)
        smooth_noise = np.array(noise_img) / 255.0
        fine_noise = np.random.random((h, w)) * 0.15
        combined_noise = smooth_noise * 0.7 + fine_noise
        combined_noise = (combined_noise - combined_noise.min()) / (combined_noise.max() - combined_noise.min() + 1e-8)
        mask = seal_data[..., 3] > 0
        wear_factor = gradient * (1 - combined_noise * wear_intensity)
        seal_data[..., 3][mask] = (seal_data[..., 3][mask] * wear_factor[mask]).astype(np.uint8)
        seal = Image.fromarray(seal_data, 'RGBA')
    if add_blur:
        seal = seal.filter(ImageFilter.GaussianBlur(radius=0.5))
    x, y = position
    paste_x = x - seal.width // 2
    paste_y = y - seal.height // 2
    result.paste(seal, (paste_x, paste_y), seal)
    return result


def apply_paper_texture(img: Image.Image, intensity: float = 0.05) -> Image.Image:
    arr = np.array(img).astype(float)
    noise = np.random.normal(0, intensity * 255, arr.shape[:2])
    noise = np.stack([noise] * 3, axis=2)
    arr[..., :3] = np.clip(arr[..., :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def load_voucher(image_path: str) -> Image.Image:
    return Image.open(image_path).convert('RGBA')


def anchor_to_pixel(
    voucher_size: Tuple[int, int],
    anchor: str = 'bottom-right',
    margin: Tuple[int, int] = (450, 350),
) -> Tuple[int, int]:
    w, h = voucher_size
    mx, my = margin
    anchors = {
        'top-left': (mx, my),
        'top-right': (w - mx, my),
        'bottom-left': (mx, h - my),
        'bottom-right': (w - mx, h - my),
        'center': (w // 2, h // 2),
        'middle-left': (mx, h // 2),
        'middle-right': (w - mx, h // 2),
        'top-center': (w // 2, my),
        'bottom-center': (w // 2, h - my),
    }
    return anchors.get(anchor, (w // 2, h // 2))


def clamp_center_for_seal(
    center: Tuple[int, int],
    voucher_size: Tuple[int, int],
    seal_size: Tuple[int, int],
) -> Tuple[int, int]:
    cx, cy = center
    w, h = voucher_size
    sw, sh = seal_size
    half_w = sw // 2
    half_h = sh // 2
    cx = max(half_w, min(w - half_w, cx))
    cy = max(half_h, min(h - half_h, cy))
    return cx, cy


def scale_seal_to_fit(
    seal_img: Image.Image,
    max_width: int,
    max_height: int,
) -> Image.Image:
    sw, sh = seal_img.size
    scale = min(max_width / sw, max_height / sh, 1.0)
    if scale < 1.0:
        new_size = (int(sw * scale), int(sh * scale))
        return seal_img.resize(new_size, resample=RESAMPLE_LANCZOS)
    return seal_img
