# -*- coding: utf-8 -*-
"""
不动产盖章算子
功能：给不动产查询结果图片添加逼真印章，支持旋转、透明度、磨损、模糊、渐变等效果
"""
import glob
from typing import Dict, Any, List
import os
import json
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datamate.core.base_op import Mapper

from loguru import logger


# 中文字体路径
CHINESE_FONT_PATHS = [
    "/usr/share/fonts/truetype/custom/FangSong_GB2312.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "C:/Windows/Fonts/simsun.ttc",  # 宋体
    "C:/Windows/Fonts/simkai.ttf",  # 楷体
]


def get_chinese_font():
    """获取默认中文字体（优先黑体）"""
    for path in CHINESE_FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


def get_font_by_name(font_name: str = None):
    """
    根据字体名称获取字体路径

    参数:
        font_name: 字体名称，可选值: 'simhei'(黑体), 'simsun'(宋体), 'simkai'(楷体)
                  如果为None，则使用默认字体

    返回:
        字体文件路径
    """
    if font_name is None:
        return get_chinese_font()

    font_map = {
        "simhei": "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "simsun": "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "simkai": "C:/Windows/Fonts/simkai.ttf",  # 楷体
    }

    font_path = font_map.get(font_name.lower())
    if font_path and os.path.exists(font_path):
        return font_path

    # 如果指定的字体不存在，回退到默认字体
    logger.warning(f"字体 {font_name} 不存在，使用默认字体")
    return get_chinese_font()


CHINESE_FONT = get_chinese_font()


class PropertySealMapper(Mapper):
    """
    不动产盖章算子
    类名必须与 metadata.yml 中的 raw_id 一致
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子

        Args:
            kwargs: UI 传入的参数
        """
        super().__init__(*args, **kwargs)

        # 获取印章效果参数
        self.output_dir = None
        self.size = 420
        self.color = (190, 0, 0)
        self.text_margin = 45
        self.circle_width = 8
        self.star_radius_ratio = 9
        self.font_size_ratio = 9
        self.char_spacing = 1.2
        self.font_name = None
        self.font_bold = True

        # 旋转范围
        self.rotation_min = -5
        self.rotation_max = 5

        # 效果参数
        self.opacity = 1.0
        self.wear_intensity = 0.05
        self.add_blur = False
        self.gradient_direction = None

    def _create_property_seal(self, province: str) -> Image.Image:
        """
        创建不动产登记中心印章（无底部文字）

        参数:
            province: 省份名称（如"河北省"）

        返回:
            PIL Image (RGBA模式)
        """
        img = Image.new("RGBA", (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        center = self.size // 2
        radius = self.size // 2 - 10

        # 外圆 - 单线（最底层）
        draw.ellipse(
            [10, 10, self.size - 10, self.size - 10],
            outline=self.color,
            width=self.circle_width,
        )

        # 绘制五角星（中间层）
        star_radius = self.size // self.star_radius_ratio
        star_points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = star_radius if i % 2 == 0 else star_radius // 2.5
            x = center + int(r * math.cos(angle))
            y = center + int(r * math.sin(angle))
            star_points.append((x, y))
        draw.polygon(star_points, fill=self.color)

        # 上部环绕文字（最顶层）
        font_path = get_font_by_name(self.font_name)
        font = ImageFont.truetype(font_path, self.size // self.font_size_ratio)
        company_name = f"{province}不动产登记中心"
        chars = list(company_name)
        n = len(chars)

        total_span = math.pi
        # 计算实际的总跨度（考虑字间距）
        actual_span = total_span * self.char_spacing
        # 调整起始角度：字间距越大，起始角度越大（往左移）
        start_angle = math.pi - (total_span - actual_span) / 2
        angle_step = -actual_span / max(n - 1, 1)
        text_radius = radius - self.text_margin

        for i, char in enumerate(chars):
            angle = start_angle + i * angle_step
            x = center + int(text_radius * math.cos(angle))
            y = center - int(text_radius * math.sin(angle))

            # 创建字符图像（加粗时需要更大的画布）
            canvas_size = 50 if not self.font_bold else 60
            char_img = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)

            # 绘制字符（加粗时多次绘制并偏移）
            if self.font_bold:
                # 加粗效果：在周围8个方向各绘制一次
                offsets = [
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1),
                ]
                base_x = 8 if not self.font_bold else 5
                base_y = 8 if not self.font_bold else 5
                for ox, oy in offsets:
                    char_draw.text(
                        (base_x + ox, base_y + oy), char, fill=self.color, font=font
                    )
                # 最后在中心绘制一次
                char_draw.text((base_x, base_y), char, fill=self.color, font=font)
            else:
                char_draw.text((5, 5), char, fill=self.color, font=font)

        rotation_angle = math.degrees(angle) - 90
        rotated_char = char_img.rotate(
            rotation_angle, expand=True, resample=Image.BICUBIC
        )

        paste_x = x - rotated_char.width // 2
        paste_y = y - rotated_char.height // 2
        img.paste(rotated_char, (paste_x, paste_y), rotated_char)

        return img

    def _apply_seal_effects(self, seal_img: Image.Image) -> Image.Image:
        """
        应用印章效果（透明度、磨损、模糊、渐变）

        参数:
            seal_img: 印章图片

        返回:
            应用效果后的印章图片
        """
        seal = seal_img.copy()

        # 应用透明度
        seal_data = np.array(seal)
        seal_data[..., 3] = (seal_data[..., 3] * self.opacity).astype(np.uint8)

        # 应用磨损和渐变
        h, w = seal_data.shape[:2]

        # 创建方向性渐变（深浅变化）
        if self.gradient_direction:
            # 创建坐标网格
            y_coords, x_coords = np.mgrid[0:h, 0:w]

            if self.gradient_direction == "left":
                # 左侧深，右侧浅：从左到右渐变
                gradient = 1 - (x_coords / w) * 0.5  # 左边1.0，右边0.5
            elif self.gradient_direction == "right":
                # 右侧深，左侧浅：从右到左渐变
                gradient = 0.5 + (x_coords / w) * 0.5  # 左边0.5，右边1.0
            elif self.gradient_direction == "top":
                # 上侧深，下侧浅：从上到下渐变
                gradient = 1 - (y_coords / h) * 0.5  # 上边1.0，下边0.5
            elif self.gradient_direction == "bottom":
                # 下侧深，上侧浅：从下到上渐变
                gradient = 0.5 + (y_coords / h) * 0.5  # 上边0.5，下边1.0
            else:
                gradient = np.ones((h, w))
        else:
            gradient = np.ones((h, w))

        # 创建平滑噪点
        small_size = max(h, w) // 10
        small_noise = np.random.random((small_size, small_size))

        noise_img = Image.fromarray((small_noise * 255).astype(np.uint8), mode="L")
        noise_img = noise_img.resize((w, h), resample=Image.BICUBIC)
        smooth_noise = np.array(noise_img) / 255.0

        # 添加细粒度噪点
        fine_noise = np.random.random((h, w)) * 0.15
        combined_noise = smooth_noise * 0.7 + fine_noise

        # 归一化
        combined_noise = (combined_noise - combined_noise.min()) / (
            combined_noise.max() - combined_noise.min() + 1e-8
        )

        # 结合渐变和噪点
        mask = seal_data[..., 3] > 0
        wear_factor = gradient * (1 - combined_noise * self.wear_intensity)
        seal_data[..., 3][mask] = (seal_data[..., 3][mask] * wear_factor[mask]).astype(
            np.uint8
        )

        seal = Image.fromarray(seal_data, "RGBA")

        # 应用模糊
        if self.add_blur:
            seal = seal.filter(ImageFilter.GaussianBlur(radius=0.5))

        return seal

    def _stamp_single_image(self, image_path: str, province: str) -> str:
        """
        对单张图片进行盖章处理

        参数:
            image_path: 图片文件路径
            province: 省份名称

        返回:
            盖章后的图片文件名
        """
        try:
            # 读取图片
            img = Image.open(image_path).convert("RGBA")

            # 创建印章
            seal = self._create_property_seal(province=province)

            # 随机生成效果参数
            random_opacity = random.uniform(
                self.opacity * 0.95, min(1.0, self.opacity * 1.05)
            )
            random_wear_intensity = random.uniform(
                self.wear_intensity * 0.8, self.wear_intensity * 1.2
            )
            random_add_blur = self.add_blur or random.random() < 0.3  # 30%概率添加模糊
            random_gradient_options = [None, "left", "right", "top", "bottom"]
            random_gradient = (
                self.gradient_direction
                if self.gradient_direction
                else (
                    random.choice(random_gradient_options)
                    if random.random() < 0.5
                    else None
                )
            )

            # 应用效果
            seal = self._apply_seal_effects(
                seal
            )

            # 旋转印章
            rotation = random.uniform(self.rotation_min, self.rotation_max)
            rotated_seal = seal.rotate(rotation, expand=True, resample=Image.BICUBIC)

            # 计算盖章位置（中下部区域）
            img_width, img_height = img.size
            seal_width, seal_height = rotated_seal.size

            # X轴：45%-55%
            x = int(img_width * random.uniform(0.45, 0.55))
            # Y轴：65%-75%
            y = int(img_height * random.uniform(0.65, 0.75))

            # 调整位置使印章中心对齐
            x -= seal_width // 2
            y -= seal_height // 2

            # 粘贴印章
            img.paste(rotated_seal, (x, y), rotated_seal)

            # 生成输出文件名
            filename = os.path.basename(image_path)

            # 保存图片到临时目录
            output_path = os.path.join(self.output_dir, filename)
            img.convert("RGB").save(output_path, quality=95)

            return output_path

        except Exception as e:
            logger.error(f"盖章失败 {image_path}: {str(e)}")
            raise

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑 - 给图片添加印章

        Args:
            sample: 输入的数据样本
                filePath: 图片路径列表
                text: JSON 数据（用于获取省份信息）

        Returns:
            处理后的数据样本，filePath 字段包含盖章后的图片路径列表
        """
        file_path = sample.get("filePath")
        if not file_path.endswith(".docx") or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            # 获取图片路径列表
            images_dir = os.path.join(sample['export_path'], "images")
            image_paths = glob.glob(os.path.join(glob.escape(images_dir), "*.jpg"))
            self.output_dir = os.path.join(sample['export_path'], "stamped_images")
            os.makedirs(self.output_dir, exist_ok=True)

            if not image_paths:
                logger.warning("输入图片路径为空，跳过处理")
                return sample

            # 读取 JSON 数据获取省份信息
            text_data = sample.get("text", "")
            province_data_map = {}

            if text_data:
                try:
                    data_list = json.loads(text_data)
                    for data in data_list:
                        province = data.get("province", "")
                        if province and province not in province_data_map:
                            province_data_map[province] = data
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {str(e)}")

            logger.info(f"[不动产盖章] 开始处理{len(image_paths)}张图片")

            # 处理每张图片
            output_paths = []
            for image_path in image_paths:
                try:
                    # 从文件名提取序号
                    import re

                    match = re.search(
                        r"不动产查询表_(\d+)(?:-(\d+))?", os.path.basename(image_path)
                    )
                    if not match:
                        logger.warning(f"无法解析文件名: {image_path}，跳过")
                        continue

                    doc_number = int(match.group(1))
                    page_number = int(match.group(2)) if match.group(2) else 1

                    # 获取对应的数据
                    if doc_number - 1 < 0 or doc_number - 1 >= len(data_list):
                        logger.warning(
                            f"图片{image_path}对应的数据索引{doc_number - 1}超出范围，使用默认省份"
                        )
                        province = "河北省"  # 默认省份
                    else:
                        data = data_list[doc_number - 1]
                        province = data.get("province", "河北省")  # 默认省份

                    # 盖章处理
                    output_path = self._stamp_single_image(image_path, province)
                    output_paths.append(output_path)

                except Exception as e:
                    logger.error(f"处理图片失败 {image_path}: {str(e)}")
                    continue

            logger.info(f"[不动产盖章] 成功处理{len(output_paths)}张图片")

            return sample

        except Exception as e:
            logger.error(f"不动产盖章算子执行失败: {str(e)}")
            raise
