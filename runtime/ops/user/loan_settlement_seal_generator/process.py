import os
import json
import math
import random
from pathlib import Path
from typing import Dict, Any, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from loguru import logger

from datamate.core.base_op import Mapper


# ============================================================================
# 原始逻辑移植：公章生成器类
# ============================================================================
class SealGenerator:
    """标准圆章生成器 (保留原始逻辑)"""

    def __init__(self, size=500, color='#DD3333'):
        self.size = size
        self.color = color
        self.center = size // 2
        self.outer_radius = int(size * 0.45)
        self.inner_radius = int(size * 0.42)

    def _get_font(self, size):
        """获取中文字体"""
        # 标准公章字体优先：仿宋 > 宋体 > 黑体 > 其他
        font_paths = [
            "C:/Windows/Fonts/simfang.ttf",  # 仿宋
            "C:/Windows/Fonts/simfs.ttf",  # 仿宋（备用名）
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
            "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
            "/usr/share/fonts/truetype/custom/FangSong_GB2312.ttf"  # Linux 常见备用
        ]

        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        # 如果系统没有上述字体，可能会导致中文显示框框，需确保运行环境有中文字体
        return ImageFont.load_default()

    def generate_seal(self, company_name, seal_type=None, opacity=230, random_effect=False):
        # 随机效果参数
        if random_effect:
            opacity = random.randint(200, 255)
            self.blur_radius = random.uniform(0.6, 1.0)
            self.noise_intensity = random.randint(10, 20)
            self.grain_intensity = random.randint(5, 12)
            self.feather_radius = random.randint(3, 7)
        else:
            self.blur_radius = 0.8
            self.noise_intensity = 15
            self.grain_intensity = 8
            self.feather_radius = 5

        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        self._draw_circle_ring(draw)
        main_img = draw._image
        self._draw_star(draw)
        self._draw_text_arc(company_name, main_img)

        if seal_type:
            self._draw_horizontal_text_on(main_img, seal_type)

        if opacity < 255:
            alpha = img.split()[3]
            alpha = alpha.point(lambda x: min(x, opacity))
            img.putalpha(alpha)

        img = self._apply_physical_effects(img)
        return img

    def _draw_circle_ring(self, draw):
        x0 = self.center - self.outer_radius
        y0 = self.center - self.outer_radius
        x1 = self.center + self.outer_radius
        y1 = self.center + self.outer_radius
        draw.ellipse([x0, y0, x1, y1], outline=self.color, width=8)

    def _draw_text_arc(self, text, main_img):
        font_size = int(self.size * 0.13)
        font = self._get_font(font_size)
        chars = list(text)
        char_count = len(chars)
        if char_count == 0: return

        if char_count <= 6:
            total_arc = 150
        elif char_count <= 10:
            total_arc = 210
        elif char_count <= 14:
            total_arc = 250
        else:
            total_arc = 280

        half_arc = total_arc / 2
        start_angle = -90 - half_arc
        text_radius = self.outer_radius * 0.78
        angle_step = total_arc / (char_count - 1) if char_count > 1 else 0

        for i, char in enumerate(chars):
            char_angle = start_angle + angle_step * i
            rad = math.radians(char_angle)
            char_x = self.center + text_radius * math.cos(rad)
            char_y = self.center + text_radius * math.sin(rad)
            bbox = font.getbbox(char)
            char_w = bbox[2] - bbox[0]
            char_h = bbox[3] - bbox[1]

            padding = 25
            char_img = Image.new('RGBA', (int(char_w + padding * 2), int(char_h + padding * 2)), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)

            for dx in range(4):
                for dy in range(4):
                    char_draw.text((padding + dx, padding + dy), char, font=font, fill=self.color)

            rotation = char_angle + 90
            char_img = char_img.rotate(-rotation, expand=True, resample=Image.BICUBIC)
            paste_x = int(char_x - char_img.width / 2)
            paste_y = int(char_y - char_img.height / 2)
            main_img.paste(char_img, (paste_x, paste_y), char_img)

    def _draw_star(self, draw):
        star_radius = self.size * 0.15
        points = []
        for i in range(10):
            r = star_radius if i % 2 == 0 else star_radius * 0.4
            angle = math.pi / 5 * i - math.pi / 2
            x = self.center + r * math.cos(angle)
            y = self.center + r * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=self.color)

    def _draw_horizontal_text_on(self, main_img, text):
        font_size = int(self.size * 0.08)
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(main_img)
        y_offset = 90
        draw.text((self.center, self.center + y_offset), text, font=font, fill=self.color, anchor="mm")

    def _apply_physical_effects(self, img):
        img = img.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
        img = self._add_ink_texture(img, intensity=self.noise_intensity)
        img = self._feather_edges_pressure(img, radius=self.feather_radius)
        img = self._add_grain_noise(img, intensity=self.grain_intensity)
        return img

    def _add_ink_texture(self, img, intensity=15):
        np_img = np.array(img)
        h, w = np_img.shape[:2]
        texture = np.random.randn(h, w) * intensity
        for c in range(3):
            np_img[:, :, c] = np.clip(np_img[:, :, c].astype(np.float32) + texture, 0, 255).astype(np.uint8)
        return Image.fromarray(np_img)

    def _feather_edges_pressure(self, img, radius=3):
        alpha = img.split()[3]
        cx, cy = img.size[0] // 2, img.size[1] // 2
        max_dist = min(img.size) // 2 * 0.92
        gradient = Image.new('L', img.size, 255)
        pixels = gradient.load()
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist > max_dist:
                    fade_factor = max(0, 1 - (dist - max_dist) / radius)
                    pixels[x, y] = int(255 * fade_factor)
        alpha_gradient = np.array(alpha, dtype=np.float32) * np.array(gradient, dtype=np.float32) / 255.0
        img.putalpha(Image.fromarray(alpha_gradient.astype(np.uint8)))
        return img

    def _add_grain_noise(self, img, intensity=3):
        np_img = np.array(img)
        noise = np.random.randn(*np_img.shape[:2]) * intensity
        for c in range(3):
            np_img[:, :, c] = np.clip(np_img[:, :, c].astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(np_img)


# ============================================================================
# 原始逻辑移植：辅助功能函数
# ============================================================================

def stamp_to_document(doc_img, seal_img, seal_position):
    """(保留原始逻辑) 将公章盖到凭证上（正片叠底混合）"""
    doc_w, doc_h = doc_img.size
    seal_x, seal_y = seal_position
    seal_w, seal_h = seal_img.size

    x1 = max(0, seal_x - seal_w // 2)
    y1 = max(0, seal_y - seal_h // 2)
    x2 = min(doc_w, x1 + seal_w)
    y2 = min(doc_h, y1 + seal_h)

    seal_x_offset = max(0, -(seal_x - seal_w // 2))
    seal_y_offset = max(0, -(seal_y - seal_h // 2))

    seal_np = np.array(seal_img)
    seal_crop = seal_np[seal_y_offset:seal_y_offset + (y2 - y1), seal_x_offset:seal_x_offset + (x2 - x1)]

    doc_np = np.array(doc_img).astype(np.float32) / 255.0
    seal_crop_np = seal_crop.astype(np.float32) / 255.0

    alpha = seal_crop_np[:, :, 3:4]
    seal_rgb = seal_crop_np[:, :, :3]

    blended = doc_np[y1:y2, x1:x2] * (1 - alpha) + (doc_np[y1:y2, x1:x2] * seal_rgb) * alpha
    result = np.array(doc_img).astype(np.float32) / 255.0
    result[y1:y2, x1:x2] = blended

    return Image.fromarray((np.clip(result, 0, 1) * 255).astype(np.uint8))


def stamp_to_document_with_variation(doc_img, seal_img, seal_position, angle_offset=0, pos_offset=(0, 0)):
    """(保留原始逻辑) 带变化的盖章"""
    if angle_offset != 0:
        seal_img = seal_img.rotate(-angle_offset, expand=False, resample=Image.BICUBIC)
    seal_x, seal_y = seal_position
    x_offset, y_offset = pos_offset
    final_position = (seal_x + x_offset, seal_y + y_offset)
    return stamp_to_document(doc_img, seal_img, final_position)


def find_footer_y_by_gap_detection(image_path):
    """(保留原始逻辑) 检测落款区域Y坐标"""
    # 注意：算子环境中可能需要处理路径或直接处理Image对象，这里为了兼容原始代码，我们尽量支持路径读取
    try:
        img = Image.open(image_path)
    except:
        return None  # 无法读取路径时

    img_array = np.array(img)
    h, w = img_array.shape[:2]
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    row_densities = []
    for y in range(h):
        row = binary[y, :]
        density = np.sum(row > 0) / w
        row_densities.append(density)

    threshold = 0.02
    footer_start_y = None
    for y in range(h - 1, h // 2, -1):
        if row_densities[y] > threshold:
            footer_start_y = y
            break
    if footer_start_y is None:
        return int(h * 0.5)

    footer_end_y = footer_start_y
    for y in range(footer_start_y, min(footer_start_y + 200, h)):
        if row_densities[y] < threshold * 0.5:
            break
        footer_end_y = y
    return (footer_start_y + footer_end_y) // 2


def find_footer_x_by_projection(image_path, footer_y):
    """(保留原始逻辑) 检测落款区域X坐标"""
    try:
        img = Image.open(image_path)
    except:
        return None

    img_array = np.array(img)
    h, w = img_array.shape[:2]
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    y_start = max(0, footer_y - 100)
    y_end = min(h, footer_y + 100)
    footer_region = binary[y_start:y_end, :]
    x_projection = np.sum(footer_region > 0, axis=0)
    total_pixels = np.sum(x_projection)

    if total_pixels > 0:
        x_coords = np.arange(len(x_projection))
        footer_x = int(np.sum(x_coords * x_projection) / total_pixels)
    else:
        footer_x = int(w * 0.70)
    return footer_x


def find_footer_position(image_path: str) -> Tuple[int, int]:
    """(保留原始逻辑)"""
    footer_y = find_footer_y_by_gap_detection(image_path)
    if footer_y is None: return (0, 0)  # Error handling
    footer_x = find_footer_x_by_projection(image_path, footer_y)
    return (footer_x, footer_y)


# ============================================================================
# 算子主体 Mapper
# ============================================================================

class LoanSettlementSealGeneratorMapper(Mapper):
    """
    公章生成算子
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.default_company = kwargs.get("inputParam", "XX银行股份有限公司").strip()
        self.seal_inner_text = kwargs.get("inputParam2", "测试专用章").strip()
        self.opacity = int(kwargs.get("sliderParam", 230))
        self.use_random_effect = kwargs.get("switchParam", True)
        # 默认印章颜色，暂未开放UI配置，使用代码默认值
        self.seal_color = '#DD3333'

    def add_seal_to_image(self, img: Image.Image, bank_name: str,
                          src_file_path: str = None) -> Image.Image:
        """
        给图片加盖公章（新版本：自动定位 + 真实感效果 + 随机变化）

        Args:
            img: PIL Image对象
            bank_name: 银行名称
            src_file_path: 源图片路径（用于自动定位）

        Returns:
            加盖公章后的图片
        """
        import random

        # 转换为RGB模式（新版本盖章函数需要RGB输入）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_w, img_h = img.size

        # 方法1：自动定位（需要源图片路径）
        if src_file_path:
            try:
                seal_x, seal_y = find_footer_position(src_file_path)
                logger.info(f"    自动定位位置: ({seal_x}, {seal_y})")
            except Exception as e:
                logger.info(f"    自动定位失败，使用固定比例: {e}")
                # Fallback: 固定比例
                seal_x = int(img_w * 0.671)
                seal_y = int(img_h * 0.520)
        else:
            # 方法2：固定比例（无源图片路径时）
            seal_x = int(img_w * 0.671)
            seal_y = int(img_h * 0.520)

        # 生成公章（基于文档宽度计算大小）
        seal_size = int(img_w * 0.18)
        gen = SealGenerator(size=seal_size, color='#DD3333')
        seal = gen.generate_seal(
            company_name=bank_name,
            seal_type="测试专用章",  # 内圈文字
            opacity=230,
            random_effect=True  # 启用随机效果
        )

        # 随机位置偏移和旋转角度
        x_offset = random.randint(-60, 60)
        y_offset = random.randint(-60, 60)
        angle_offset = random.uniform(-15, 15)

        logger.info(f"    随机偏移: ({x_offset}, {y_offset}), 角度: {angle_offset:.1f}°")

        # 盖章（带随机变化）
        result = stamp_to_document_with_variation(
            img, seal, (seal_x, seal_y),
            angle_offset=angle_offset,
            pos_offset=(x_offset, y_offset)
        )

        return result

    def load_records_map(self, records: str) -> Dict[str, Dict[str, Any]]:
        """加载Step 1生成的数据记录，返回文件名到记录的映射"""

        # 创建文件名到记录的映射
        # 文件名格式：loan_clearance_001, loan_clearance_002等
        # records按顺序排列，通过索引匹配
        records_map = {}
        for idx, record in enumerate(records, start=1):
            # 生成对应的文件名
            file_name = f"loan_clearance_{idx:03d}"
            records_map[file_name] = record

        return records_map

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑：读取图片 -> 确定公司名 -> 定位 -> 生成印章 -> 盖章 -> 保存
        """
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            output_dir = Path(sample.get('export_path') + "/images")
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info("=" * 60)
            logger.info("步骤 3.5：公章加盖（单文件版本）")
            logger.info("  - 自动定位盖章位置")
            logger.info("  - 真实感公章效果")
            logger.info("=" * 60)
            logger.info("=" * 60)

            # 加载数据记录
            logger.info(f"records: {json.loads(sample['text'])}")
            records_map = self.load_records_map(json.loads(sample['text']))
            logger.info(f"records: {records_map}")
            if records_map:
                logger.info(f"  已加载 {len(records_map)} 条数据记录")
            else:
                logger.info("  警告: 无法加载数据记录，将不加盖公章")

            # 获取源图片
            input_path = output_dir
            src_files = list(input_path.glob("*.png"))


            logger.info(f"\n找到 {len(src_files)} 张源图片")

            # 处理每张图片
            success_count = 0

            for i, src_file in enumerate(src_files, 1):
                # 提取基础文件名（去掉扩展名）
                base_name = src_file.stem  # 例如: loan_clearance_001

                logger.info(f"\n[{i}/{len(src_files)}] {src_file.name}")

                # 获取对应的证明出具单位（用于盖章）
                issuer = None
                if base_name in records_map:
                    record = records_map[base_name]
                    # 使用证明出具单位（包含完整名称，含"股份有限公司"）
                    issuer = record.get('证明出具单位', None)

                if not issuer:
                    logger.info(f"  跳过: 无法找到对应的证明出具单位")
                    continue

                logger.info(f"  证明出具单位: {issuer}")

                try:
                    # 读取图片
                    img = Image.open(str(src_file))

                    # 加盖公章（传入源图片路径用于自动定位）
                    img_sealed = self.add_seal_to_image(img, issuer, str(src_file))

                    # 保存
                    output_path = output_dir / src_file.name
                    img_sealed.save(str(output_path), 'PNG', optimize=True)

                    success_count += 1
                    logger.info(f"  成功: {output_path.name}")

                except Exception as e:
                    logger.info(f"  失败: {e}")

        except Exception as e:
            # 异常处理：打印错误但不中断流程，返回原 sample
            logger.info(f"Error processing : {e}")
            pass

        return sample