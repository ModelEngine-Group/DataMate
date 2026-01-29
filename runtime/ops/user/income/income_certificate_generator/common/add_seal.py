#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给凭证添加逼真印章的Python工具（修复版）
修复了圆形印章文字环绕方向的问题
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import random
import math
import os

from loguru import logger

# 中文字体路径
CHINESE_FONT_PATHS = [
    "/usr/share/fonts/truetype/custom/FangSong_GB2312.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]

def get_chinese_font():
    for path in CHINESE_FONT_PATHS:
        if os.path.exists(path):
            return path
    return None

CHINESE_FONT = get_chinese_font()


def create_round_seal(company_name, seal_type="财务专用章", size=300, color=(200, 30, 30), text_margin=28):
    """
    创建圆形印章（财务专用章样式）- 修复版
    修复了文字环绕方向的问题

    参数:
        company_name: 公司名称（环绕文字）
        seal_type: 章类型（底部文字，如"财务专用章"）
        size: 印章大小
        color: 印章颜色 (R, G, B)
        text_margin: 文字离内圈的距离（像素），默认28

    返回:
        PIL Image (RGBA模式)
    """
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    radius = size // 2 - 10
    
    # 外圆 - 双线
    draw.ellipse([10, 10, size-10, size-10], outline=color, width=3)
    draw.ellipse([16, 16, size-16, size-16], outline=color, width=2)
    
    # 绘制五角星（正中心）
    star_radius = size // 12
    star_points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = star_radius if i % 2 == 0 else star_radius // 2.5
        x = center + int(r * math.cos(angle))
        y = center + int(r * math.sin(angle))
        star_points.append((x, y))
    draw.polygon(star_points, fill=color)
    
    # 上部环绕文字 - 修复版
    font = ImageFont.truetype(CHINESE_FONT, size//11)
    chars = list(company_name)
    n = len(chars)

    # 文字均匀分布在180°的上半圆弧（从180°左侧顺时针向上到0°右侧）
    # 第一个字在180°位置（9点钟），最后一个字在0°位置（3点钟）
    start_angle = math.pi  # 180°，起始位置（左侧）
    total_span = math.pi   # 180°，总跨度
    angle_step = -total_span / max(n - 1, 1)  # 负数：角度递减（顺时针向上）
    text_radius = radius - text_margin  # 文字半径 = 外圆半径 - 边距

    for i, char in enumerate(chars):
        angle = start_angle + i * angle_step  # 当前字的角度（弧度）

        # 计算字符位置（使用标准极坐标转换）
        x = center + int(text_radius * math.cos(angle))
        y = center - int(text_radius * math.sin(angle))  # PIL坐标系y轴向下，需用减号

        # 创建字符图像
        char_img = Image.new('RGBA', (50, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 5), char, fill=color, font=font)

        # 旋转角度：让文字底部朝向圆心
        # angle是位置角度（弧度），转换为角度后减去90度
        # 例如：angle=180°(9点)时，文字应旋转90°使底部朝向圆心
        rotation_angle = math.degrees(angle) - 90
        rotated_char = char_img.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)
        
        paste_x = x - rotated_char.width // 2
        paste_y = y - rotated_char.height // 2
        img.paste(rotated_char, (paste_x, paste_y), rotated_char)
    
    # 底部文字
    bottom_font = ImageFont.truetype(CHINESE_FONT, size//10)
    bbox = draw.textbbox((0, 0), seal_type, font=bottom_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((center - text_w//2, center + radius//2 - text_h - 8), seal_type, fill=color, font=bottom_font)
    
    return img


def create_square_seal(name, size=150, color=(200, 30, 30)):
    """创建方形人名章"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 边框
    draw.rectangle([5, 5, size-5, size-5], outline=color, width=4)
    
    # 文字 - 竖排
    font = ImageFont.truetype(CHINESE_FONT, size//3)
    chars = list(name)
    
    # 竖排文字，从右到左
    col_count = 2
    row_count = (len(chars) + 1) // 2
    char_size = size // (max(row_count, 2) + 1)
    
    for i, char in enumerate(chars):
        col = i // row_count
        row = i % row_count
        
        x = size - (col + 1) * (size // (col_count + 1)) - char_size//4
        y = (row + 1) * (size // (row_count + 1)) - char_size//2
        
        bbox = draw.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((x - text_w//2, y - text_h//2), char, fill=color, font=font)
    
    return img


def create_oval_seal(text, sub_text="", size=(400, 200), color=(200, 30, 30)):
    """创建椭圆形印章"""
    img = Image.new('RGBA', (size[0], size[1]), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 外椭圆
    draw.ellipse([5, 5, size[0]-5, size[1]-5], outline=color, width=4)
    draw.ellipse([15, 15, size[0]-15, size[1]-15], outline=color, width=2)
    
    # 中间小圆
    center_x, center_y = size[0]//2 - size[0]//6, size[1]//2
    small_radius = size[1] // 6
    draw.ellipse([center_x-small_radius, center_y-small_radius, 
                  center_x+small_radius, center_y+small_radius], 
                 outline=color, width=2)
    
    # 中间小圆内的图案
    inner_font = ImageFont.truetype(CHINESE_FONT, small_radius//2)
    bbox = draw.textbbox((0, 0), "行", font=inner_font)
    text_w = bbox[2] - bbox[0]
    draw.text((center_x - text_w//2, center_y - small_radius//3), "行", fill=color, font=inner_font)
    
    # 主文字
    font = ImageFont.truetype(CHINESE_FONT, size[1]//5)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text((center_x + size[0]//8 - text_w//2, center_y - size[1]//8), text, fill=color, font=font)
    
    # 副文字
    if sub_text:
        sub_font = ImageFont.truetype(CHINESE_FONT, size[1]//8)
        bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
        text_w = bbox[2] - bbox[0]
        draw.text((center_x + size[0]//8 - text_w//2, center_y + size[1]//10), sub_text, fill=color, font=sub_font)
    
    return img


def add_seal_to_voucher(voucher_img, seal_img, position, rotation=0, opacity=0.85,
                        add_wear=True, add_blur=True, wear_intensity=0.15, gradient_direction=None):
    """
    将印章添加到凭证上

    参数:
        voucher_img: 凭证图片
        seal_img: 印章图片
        position: (x, y) 印章中心位置
        rotation: 旋转角度（0=随机-8到8度）
        opacity: 透明度 (0-1)
        add_wear: 是否添加磨损效果
        add_blur: 是否添加轻微模糊
        wear_intensity: 磨损强度 (0-0.5)，越大磨损越明显
        gradient_direction: 渐变方向，None=无渐变，'left'左深右浅，'right'右深左浅，
                          'top'上深下浅，'bottom'下深上浅
    """
    result = voucher_img.copy().convert('RGBA')
    seal = seal_img.copy()

    if rotation == 0:
        rotation = random.uniform(-8, 8)
    seal = seal.rotate(rotation, expand=True, resample=Image.BICUBIC)

    seal_data = np.array(seal)
    seal_data[..., 3] = (seal_data[..., 3] * opacity).astype(np.uint8)

    if add_wear:
        h, w = seal_data.shape[:2]

        # 创建方向性渐变（深浅变化）
        if gradient_direction:
            # 创建坐标网格
            y_coords, x_coords = np.mgrid[0:h, 0:w]

            if gradient_direction == 'left':
                # 左侧深，右侧浅：从左到右渐变
                gradient = 1 - (x_coords / w) * 0.5  # 左边1.0，右边0.5
            elif gradient_direction == 'right':
                # 右侧深，左侧浅：从右到左渐变
                gradient = 0.5 + (x_coords / w) * 0.5  # 左边0.5，右边1.0
            elif gradient_direction == 'top':
                # 上侧深，下侧浅：从上到下渐变
                gradient = 1 - (y_coords / h) * 0.5  # 上边1.0，下边0.5
            elif gradient_direction == 'bottom':
                # 下侧深，上侧浅：从下到上渐变
                gradient = 0.5 + (y_coords / h) * 0.5  # 上边0.5，下边1.0
            else:
                gradient = np.ones((h, w))
        else:
            gradient = np.ones((h, w))

        # 创建平滑噪点
        small_size = max(h, w) // 10
        small_noise = np.random.random((small_size, small_size))

        from PIL import Image as PILImage
        noise_img = PILImage.fromarray((small_noise * 255).astype(np.uint8), mode='L')
        noise_img = noise_img.resize((w, h), resample=PILImage.BICUBIC)
        smooth_noise = np.array(noise_img) / 255.0

        # 添加细粒度噪点
        fine_noise = np.random.random((h, w)) * 0.15
        combined_noise = smooth_noise * 0.7 + fine_noise

        # 归一化
        combined_noise = (combined_noise - combined_noise.min()) / (combined_noise.max() - combined_noise.min() + 1e-8)

        # 结合渐变和噪点
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


def apply_paper_texture(img, intensity=0.05):
    """添加纸张纹理效果"""
    arr = np.array(img).astype(float)
    noise = np.random.normal(0, intensity * 255, arr.shape[:2])
    noise = np.stack([noise] * 3, axis=2)
    arr[..., :3] = np.clip(arr[..., :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def load_voucher(image_path):
    """加载凭证图片"""
    return Image.open(image_path).convert('RGBA')


def save_result(img, output_path, quality=95):
    """保存结果图片"""
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(output_path, quality=quality)
    logger.info(f"结果已保存到: {output_path}")


def create_sample_voucher():
    """创建模拟凭证背景"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), (250, 250, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle([20, 20, width-20, height-20], outline=(180, 180, 170), width=2)
    draw.rectangle([25, 25, width-25, height-25], outline=(200, 200, 190), width=1)

    title_font = ImageFont.truetype(CHINESE_FONT, 32)
    label_font = ImageFont.truetype(CHINESE_FONT, 18)

    draw.text((width//2 - 100, 40), "银行承兑汇票", fill=(50, 50, 50), font=title_font)

    table_top = 100
    row_height = 50

    draw.rectangle([50, table_top, width-50, table_top + row_height*6],
                   outline=(150, 150, 140), width=2)

    for i in range(1, 6):
        y = table_top + i * row_height
        draw.line([(50, y), (width-50, y)], fill=(180, 180, 170), width=1)

    col_width = 250
    draw.line([(50 + col_width, table_top), (50 + col_width, table_top + row_height*6)],
              fill=(180, 180, 170), width=1)
    draw.line([(width//2, table_top), (width//2, table_top + row_height*3)],
              fill=(180, 180, 170), width=1)

    labels = [
        (60, table_top + 10, "出票人全称:"),
        (60, table_top + row_height + 10, "出票人账号:"),
        (60, table_top + row_height*2 + 10, "付款行全称:"),
        (width//2 + 10, table_top + 10, "收款人全称:"),
        (width//2 + 10, table_top + row_height + 10, "收款人账号:"),
        (width//2 + 10, table_top + row_height*2 + 10, "开户银行:"),
        (60, table_top + row_height*3 + 10, "出票金额:"),
        (60, table_top + row_height*4 + 10, "汇票到期日:"),
        (60, table_top + row_height*5 + 10, "承兑协议编号:"),
    ]

    for x, y, text in labels:
        draw.text((x, y), text, fill=(80, 80, 80), font=label_font)

    return img


def add_seal_to_image(input_path=None, output_path=None, seal_type="finance",
                     image_path=None, seal_size_ratio=0.22, position_ratio=None,
                     **seal_params):
    """
    给图片添加印章的主函数

    参数:
        input_path: 输入图片路径（与image_path二选一）
        output_path: 输出图片路径
        seal_type: 印章类型，可选值:
            - "finance": 财务专用章（圆形）
            - "name": 人名章（方形）
            - "bank": 银行章（椭圆）
            - "multiple": 多个印章组合
        image_path: 输入图片路径（兼容参数，与input_path二选一）
        seal_size_ratio: 印章大小相对于图片的比例（默认0.22，即印章直径为图片宽度的22%）
        position_ratio: 盖章位置比例 (x_ratio, y_ratio)，例如(0.7, 0.8)表示图片右侧70%、下方80%的位置
                       None表示自动计算（默认右下角）
        **seal_params: 印章参数，根据印章类型不同而不同:
            财务章(finance):
                - company_name: 公司名称（必填）
                - seal_type_text: 底部文字（默认"财务专用章"）
                - size: 印章大小（默认根据seal_size_ratio自动计算）
                - position: 盖章位置 (x, y)，默认根据position_ratio自动计算
                - opacity: 透明度（默认0.85）
                - gradient_direction: 渐变方向（默认'left'）
                - wear_intensity: 磨损强度（默认0.15）

            人名章(name):
                - name: 姓名（必填）
                - size: 印章大小（默认根据seal_size_ratio自动计算）
                - position: 盖章位置 (x, y)，默认根据position_ratio自动计算
                - opacity: 透明度（默认0.85）

            银行章(bank):
                - text: 主文字（必填）
                - sub_text: 副文字（默认""）
                - size: 印章大小 (宽, 高)，默认根据seal_size_ratio自动计算
                - position: 盖章位置 (x, y)，默认根据position_ratio自动计算
                - opacity: 透明度（默认0.85）

            多个印章(multiple):
                - finance_company: 公司名称（用于财务章）
                - name_text: 姓名（用于人名章）
                - bank_text: 银行文字（用于银行章）
                - bank_sub_text: 银行副文字
                - positions: 字典，指定各印章位置 {'finance': (x, y), 'name': (x, y), 'bank': (x, y)}

    返回:
        str: 成功时返回输出文件路径，失败时返回None
    """
    # 兼容参数：支持 input_path 和 image_path
    if image_path is not None:
        input_path = image_path

    # 检查必填参数
    if input_path is None:
        raise ValueError("必须提供 input_path 或 image_path 参数")
    if output_path is None:
        raise ValueError("必须提供 output_path 参数")

    # 加载图片
    voucher = load_voucher(input_path)
    img_width, img_height = voucher.size

    # 计算默认盖章位置
    def get_default_position(seal_size):
        """
        计算默认盖章位置
        策略：从下往上、从右往左扫描，找到有文字的地方作为盖章位置
        """
        if isinstance(seal_size, tuple):
            seal_w, seal_h = seal_size
        else:
            seal_w = seal_h = seal_size

        # 如果提供了 position_ratio，使用比例计算位置
        if position_ratio is not None:
            x_ratio, y_ratio = position_ratio
            x = int(img_width * x_ratio)
            y = int(img_height * y_ratio)
            return (x, y)

        # 智能定位：从下往上、从右往左找到有文字的地方，并让印章覆盖大部分文字
        try:
            # 转换为numpy数组进行处理
            img_array = np.array(voucher)

            # 如果是RGBA，取RGB通道
            if img_array.shape[2] == 4:
                img_rgb = img_array[:, :, :3]
            else:
                img_rgb = img_array

            # 转为灰度图
            img_gray = np.mean(img_rgb, axis=2).astype(np.uint8)

            # 使用简单的边缘检测：寻找非背景像素
            # 假设背景较亮，文字较暗
            threshold = 200  # 灰度阈值，低于此值认为是文字
            text_mask = img_gray < threshold

            # 定义搜索区域（右下60%的区域，避免扫描整个图片）
            search_left = int(img_width * 0.4)
            search_top = int(img_height * 0.4)
            search_mask = text_mask[search_top:, search_left:]

            # 从下往上、从右往左扫描找到第一个文字像素
            mask_height, mask_width = search_mask.shape

            first_text_pixel = None
            for y in range(mask_height - 1, -1, -1):  # 从下往上
                for x in range(mask_width - 1, -1, -1):  # 从右往左
                    if search_mask[y, x]:
                        first_text_pixel = (search_left + x, search_top + y)
                        break
                if first_text_pixel:
                    break

            if first_text_pixel:
                # 找到第一个文字像素后，在印章大小的区域内计算文字密度
                # 找到文字密度最高的位置作为印章中心
                start_x = max(0, first_text_pixel[0] - seal_w)
                end_x = min(img_width, first_text_pixel[0] + seal_w)
                start_y = max(0, first_text_pixel[1] - seal_h)
                end_y = min(img_height, first_text_pixel[1] + seal_h)

                # 在这个区域内滑动窗口，寻找文字密度最高的位置
                best_position = None
                max_density = 0

                step = 10  # 步长，提高搜索效率
                for cy in range(start_y + seal_h // 2, end_y - seal_h // 2 + 1, step):
                    for cx in range(start_x + seal_w // 2, end_x - seal_w // 2 + 1, step):
                        # 计算以(cx, cy)为中心的印章区域内的文字像素数量
                        x1 = max(0, cx - seal_w // 2)
                        x2 = min(img_width, cx + seal_w // 2)
                        y1 = max(0, cy - seal_h // 2)
                        y2 = min(img_height, cy + seal_h // 2)

                        region_mask = text_mask[y1:y2, x1:x2]
                        text_density = np.sum(region_mask) / region_mask.size

                        if text_density > max_density:
                            max_density = text_density
                            best_position = (cx, cy)

                # 如果找到了高密度区域，返回该位置
                if best_position:
                    return best_position
                else:
                    # 回退方案：使用第一个文字像素的位置，印章向左上偏移以覆盖文字
                    target_x = first_text_pixel[0] - seal_w // 3
                    target_y = first_text_pixel[1] - seal_h // 3

                    # 确保不超出图片边界
                    target_x = min(max(target_x, seal_w // 2), img_width - seal_w // 2)
                    target_y = min(max(target_y, seal_h // 2), img_height - seal_h // 2)

                    return (target_x, target_y)

        except Exception as e:
            # 如果智能定位失败，回退到默认位置
            logger.info(f"警告：智能定位失败，使用默认位置 ({e})")

        # 回退方案：使用右下角位置
        x = img_width - seal_w // 2 - 100
        y = img_height - seal_h // 2 - 100
        return (max(x, seal_w), max(y, seal_h))

    # 根据图片尺寸和 seal_size_ratio 计算默认印章大小
    def get_default_seal_size(is_oval=False):
        """根据图片比例计算印章大小"""
        base_size = int(img_width * seal_size_ratio)
        if is_oval:
            # 椭圆印章：宽是base_size的2倍，高是base_size
            return (base_size * 2, base_size)
        return base_size

    result = voucher

    if seal_type == "finance":
        # 财务专用章
        company_name = seal_params.get("company_name", "某某科技有限公司")
        seal_type_text = seal_params.get("seal_type_text", "财务专用章")

        # 如果没有指定size，根据图片比例自动计算
        if "size" not in seal_params:
            size = get_default_seal_size(is_oval=False)
        else:
            size = seal_params.get("size", get_default_seal_size(is_oval=False))

        position = seal_params.get("position", get_default_position(size))
        opacity = seal_params.get("opacity", 0.85)
        gradient_direction = seal_params.get("gradient_direction", "left")
        wear_intensity = seal_params.get("wear_intensity", 0.15)

        seal = create_round_seal(company_name, seal_type_text, size=size)
        result = add_seal_to_voucher(
            voucher, seal, position=position,
            opacity=opacity,
            gradient_direction=gradient_direction,
            wear_intensity=wear_intensity
        )

    elif seal_type == "name":
        # 人名章
        name = seal_params.get("name", "张三")

        # 如果没有指定size，根据图片比例自动计算（稍小一些）
        if "size" not in seal_params:
            size = int(get_default_seal_size(is_oval=False) * 0.5)
        else:
            size = seal_params.get("size", int(get_default_seal_size(is_oval=False) * 0.5))

        position = seal_params.get("position", get_default_position(size))
        opacity = seal_params.get("opacity", 0.85)

        seal = create_square_seal(name, size=size)
        result = add_seal_to_voucher(
            voucher, seal, position=position,
            opacity=opacity
        )

    elif seal_type == "bank":
        # 银行章
        text = seal_params.get("text", "银行承兑")
        sub_text = seal_params.get("sub_text", "")

        # 如果没有指定size，根据图片比例自动计算
        if "size" not in seal_params:
            size = get_default_seal_size(is_oval=True)
        else:
            size = seal_params.get("size", get_default_seal_size(is_oval=True))

        position = seal_params.get("position", get_default_position(size))
        opacity = seal_params.get("opacity", 0.85)

        seal = create_oval_seal(text, sub_text, size=size)
        result = add_seal_to_voucher(
            voucher, seal, position=position,
            opacity=opacity
        )

    elif seal_type == "multiple":
        # 多个印章组合
        finance_company = seal_params.get("finance_company", "某某科技有限公司")
        name_text = seal_params.get("name_text", "张三")
        bank_text = seal_params.get("bank_text", "银行承兑")
        bank_sub_text = seal_params.get("bank_sub_text", "")
        positions = seal_params.get("positions", {})

        # 计算默认印章大小
        finance_size = get_default_seal_size(is_oval=False)
        name_size = int(finance_size * 0.5)
        bank_size = get_default_seal_size(is_oval=True)

        # 创建印章
        finance_seal = create_round_seal(finance_company, "财务专用章", size=finance_size)
        name_seal = create_square_seal(name_text, size=name_size)
        bank_seal = create_oval_seal(bank_text, bank_sub_text, size=bank_size)

        # 获取或计算位置
        finance_pos = positions.get("finance", get_default_position(finance_size))
        name_pos = positions.get("name", get_default_position(name_size))
        bank_pos = positions.get("bank", get_default_position(bank_size))

        # 如果没有指定位置且没有position_ratio，自动分散排列
        if not positions and position_ratio is None:
            finance_pos = (int(img_width * 0.75), int(img_height * 0.8))
            name_pos = (int(img_width * 0.85), int(img_height * 0.75))
            bank_pos = (int(img_width * 0.7), int(img_height * 0.65))

        # 依次盖章
        result = add_seal_to_voucher(
            voucher, finance_seal, position=finance_pos,
            opacity=0.8, gradient_direction='left', wear_intensity=0.2
        )
        result = add_seal_to_voucher(
            result, name_seal, position=name_pos,
            opacity=0.85, gradient_direction='left', wear_intensity=0.15
        )
        result = add_seal_to_voucher(
            result, bank_seal, position=bank_pos,
            opacity=0.75, gradient_direction='left', wear_intensity=0.15
        )

    else:
        raise ValueError(f"不支持的印章类型: {seal_type}。可选值: 'finance', 'name', 'bank', 'multiple'")

    # 添加纸张纹理
    result = apply_paper_texture(result, intensity=0.03)

    # 保存结果
    save_result(result, output_path)

    # 返回输出文件路径
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='给图片添加逼真印章')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--type', dest='seal_type',
                       choices=['finance', 'name', 'bank', 'multiple'],
                       default='finance',
                       help='印章类型: finance(财务章), name(人名章), bank(银行章), multiple(多章组合)')

    # 财务章参数
    parser.add_argument('--company', help='公司名称（财务章）')
    parser.add_argument('--seal-text', default='财务专用章', help='财务章底部文字（默认:财务专用章）')

    # 人名章参数
    parser.add_argument('--person-name', help='人名（人名章）')

    # 银行章参数
    parser.add_argument('--bank-text', help='银行文字（银行章）')
    parser.add_argument('--bank-sub-text', default='', help='银行副文字（银行章）')

    # 通用参数
    parser.add_argument('--position', nargs=2, type=int, metavar=('X', 'Y'),
                       help='盖章位置坐标（自动计算如果不指定）')
    parser.add_argument('--opacity', type=float, default=0.85,
                       help='透明度 0-1（默认:0.85）')

    args = parser.parse_args()

    # 构建参数字典
    seal_params = {'opacity': args.opacity}

    if args.seal_type == 'finance':
        if not args.company:
            raise ValueError('财务章需要提供 --company 参数')
        seal_params['company_name'] = args.company
        seal_params['seal_type_text'] = args.seal_text

    elif args.seal_type == 'name':
        if not args.person_name:
            raise ValueError('人名章需要提供 --person-name 参数')
        seal_params['name'] = args.person_name

    elif args.seal_type == 'bank':
        if not args.bank_text:
            raise ValueError('银行章需要提供 --bank-text 参数')
        seal_params['text'] = args.bank_text
        seal_params['sub_text'] = args.bank_sub_text

    elif args.seal_type == 'multiple':
        if args.company:
            seal_params['finance_company'] = args.company
        if args.person_name:
            seal_params['name_text'] = args.person_name
        if args.bank_text:
            seal_params['bank_text'] = args.bank_text
        if args.bank_sub_text:
            seal_params['bank_sub_text'] = args.bank_sub_text

    # 添加位置参数
    if args.position:
        seal_params['position'] = tuple(args.position)

    # 执行盖章
    logger.info(f"正在处理: {args.input}")
    logger.info(f"印章类型: {args.seal_type}")

    add_seal_to_image(
        input_path=args.input,
        output_path=args.output,
        seal_type=args.seal_type,
        **seal_params
    )

    logger.info(f"✓ 完成！结果已保存到: {args.output}")