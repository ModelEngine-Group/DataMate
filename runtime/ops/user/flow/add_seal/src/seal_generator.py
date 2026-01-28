"""
印章生成模块 - 用于生成银行印章并添加到文档或图片
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import os
import cv2
from typing import Optional, Tuple


class SealGenerator:
    """印章生成器类"""

    def __init__(self, seal_size: int = 200, font_size: int = 20):
        """
        初始化印章生成器

        Args:
            seal_size: 印章直径（像素）
            font_size: 基础字体大小
        """
        self.seal_size = seal_size
        self.font_size = font_size
        self.center = seal_size // 2
        self.radius = seal_size // 2 - 10  # 留出边距

    def create_circular_seal(self, top_text: str, bottom_text: str, 
                          bank_name: str) -> Image.Image:
        """
        创建圆形印章

        Args:
            top_text: 顶部文字（如"北京兴业银行信贷部"）
            bottom_text: 底部文字（如"业务专用"）
            bank_name: 银行名称（用于字体调整）

        Returns:
            PIL Image对象
        """
        # 创建透明背景的图像
        img = Image.new('RGBA', (self.seal_size, self.seal_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # 绘制外圆（红色）
        draw.ellipse(
            [(self.center - self.radius, self.center - self.radius),
             (self.center + self.radius, self.center + self.radius)],
            outline=(200, 0, 0, 255),
            width=2
        )

        # 绘制内圆（红色，稍细）
        inner_radius = self.radius - 5
        draw.ellipse(
            [(self.center - inner_radius, self.center - inner_radius),
             (self.center + inner_radius, self.center + inner_radius)],
            outline=(200, 0, 0, 255),
            width=1
        )

        # 绘制五角星
        self._draw_star(draw, self.center, self.center, self.radius * 0.5)

        # 绘制顶部文字（顺时针方向）
        self._draw_arc_text(draw, img, top_text, self.center, self.center,
                          self.radius - 15, -150, -30, clockwise=True)

        # 绘制底部文字（横向）
        self._draw_bottom_text(draw, bottom_text, self.center, self.center + self.radius * 0.5)

        return img

    def _draw_star(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: float):
        """绘制五角星"""
        # 五角星的5个顶点
        points = []
        for i in range(5):
            # 外点角度（从顶部开始，顺时针）
            angle = math.pi / 2 - i * 2 * math.pi / 5
            # 外点坐标
            x_outer = cx + radius * math.cos(angle)
            y_outer = cy - radius * math.sin(angle)
            points.append((x_outer, y_outer))

            # 内点角度（在外点之间）
            angle_inner = angle - math.pi / 5
            # 内点半径为外点半径的0.382倍（黄金比例）
            x_inner = cx + radius * 0.382 * math.cos(angle_inner)
            y_inner = cy - radius * 0.382 * math.sin(angle_inner)
            points.append((x_inner, y_inner))

        # 绘制五角星，使用红色填充
        draw.polygon(points, fill=(200, 0, 0, 255))

    def _draw_arc_text(self, draw: ImageDraw.ImageDraw, img: Image.Image, 
                     text: str, cx: int, cy: int, radius: float, 
                     start_angle: float, end_angle: float, clockwise: bool = True):
        """绘制弧形文字"""
        if not text:
            return

        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("simhei.ttf", self.font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                font = ImageFont.load_default()

        # 计算每个字符的角度
        char_count = len(text)
        angle_step = (end_angle - start_angle) / (char_count - 1) if char_count > 1 else 0

        for i, char in enumerate(text):
            angle = start_angle + i * angle_step
            angle_rad = math.radians(angle)

            # 计算字符位置
            x = cx + radius * math.cos(angle_rad)
            y = cy + radius * math.sin(angle_rad)

            # 计算字符旋转角度
            if clockwise:
                rotation = angle + 90
            else:
                rotation = angle - 90

            # 创建旋转的字符
            char_img = Image.new('RGBA', (self.font_size * 2, self.font_size * 2), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)

            # 计算字符位置（居中）
            bbox = char_draw.textbbox((0, 0), char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            char_draw.text(
                ((self.font_size * 2 - text_width) // 2,
                 (self.font_size * 2 - text_height) // 2),
                char,
                font=font,
                fill=(200, 0, 0, 255)
            )

            # 旋转字符
            rotated_char = char_img.rotate(-rotation, expand=True)

            # 将字符粘贴到主图像
            paste_x = x - rotated_char.width // 2
            paste_y = y - rotated_char.height // 2
            img.paste(rotated_char, (int(paste_x), int(paste_y)), rotated_char)

    def _draw_bottom_text(self, draw: ImageDraw.ImageDraw, text: str, x: int, y: int):
        """绘制底部横向文字"""
        if not text:
            return

        try:
            font = ImageFont.truetype("simhei.ttf", int(self.font_size * 0.8))
        except:
            font = ImageFont.load_default()

        # 计算文本宽度
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # 居中绘制
        draw.text(
            (x - text_width // 2, y),
            text,
            font=font,
            fill=(200, 0, 0, 255)
        )

    def find_text_positions_in_image(self, image_path: str) -> list:
        """
        使用OpenCV识别图片中左下角有文字的区域

        Args:
            image_path: 图片路径

        Returns:
            文字位置列表 [(x, y, w, h), ...]
        """
        # 读取图片
        img = cv2.imread(image_path)

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 二值化 - 降低阈值以捕获更多文字
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_regions = []

        # 图片尺寸
        img_height, img_width = gray.shape

        # 遍历所有轮廓，查找文字区域
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # 跳过太小的区域
            if w < 10 or h < 5:
                continue

            # 扩大搜索范围，保留左下角的文字区域
            if x < img_width * 0.6 and y > img_height * 0.6:
                text_regions.append((x, y, w, h))

        # 按y坐标排序，找到最下方的文字区域
        text_regions.sort(key=lambda r: r[1], reverse=True)

        # 只保留最下方的3个文字区域
        text_regions = text_regions[:3]

        return text_regions

    def composite_seal_to_image(self, background_path: str, seal_img: Image.Image, 
                            output_path: str, position: Optional[Tuple[int, int]] = None, 
                            scale: float = 0.3, auto_detect: bool = True):
        """
        将印章合成到背景图片上

        Args:
            background_path: 背景图片路径
            seal_img: 印章图像
            output_path: 输出图片路径
            position: 印章位置 (x, y)，None表示自动识别
            scale: 印章缩放比例
            auto_detect: 是否自动检测位置
        """
        # 打开背景图片
        background = Image.open(background_path).convert('RGBA')

        # 缩放印章，缩小印章面积0.7倍
        seal_size = int(min(background.size) * scale * 0.7)
        seal_resized = seal_img.resize((seal_size, seal_size), Image.LANCZOS)

        # 确定印章位置
        if position is None and auto_detect:
            # 尝试识别左下角有文字的区域
            text_regions = self.find_text_positions_in_image(background_path)

            if text_regions:
                # 使用第一个（最下方）文字区域的位置
                x, y, w, h = text_regions[0]
                # 印章盖在文字上，调整到中间靠左的位置
                x = x + w // 2 - seal_size // 2 - 40 - 200  # 向左偏移40像素，再往左移动200像素
                y = y + h // 2 - seal_size // 2 - 300  # 向上偏移300像素（100+200）
            else:
                # 未找到文字，使用默认位置（中间靠左）
                x = background.width // 2 - seal_size // 2 - 50 - 200
                y = background.height - background.height // 3 - seal_size // 2 - 300
        elif position is not None:
            x, y = position
        else:
            # 使用默认位置
            x = background.width // 2 - seal_size // 2 - 50 - 200
            y = background.height - background.height // 3 - seal_size // 2 - 300

        # 合成印章
        background.paste(seal_resized, (x, y), seal_resized)

        # 保存结果
        background.convert('RGB').save(output_path, 'PNG')
