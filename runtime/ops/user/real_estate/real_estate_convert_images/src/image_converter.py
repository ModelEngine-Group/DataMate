"""
图像转换器 - 不动产权证
将JSON数据渲染到模板图像上
"""
import os
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Optional
from loguru import logger

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
TEMPLATE_NAMES = ['template.jpg', 'template.jpeg', 'template.png', 'blank.jpg', 'bg.jpg']


class ImageConverter:
    """图像转换器 - 不动产权证"""

    def __init__(self, output_dir: str = ".", input_dir: str = ".", dpi: int = 200, instance_id: str = "001"):
        """
        初始化图像转换器

        Args:
            output_dir: 输出目录
            dpi: 图像DPI
            instance_id: 实例ID
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.instance_id = instance_id
        self.input_dir = input_dir

    def is_output_image(self, filename: str) -> bool:
        """判断是否为输出文件"""
        return '_filled_' in filename

    # 与 scripts/images/runtime/Dockerfile 中安装的字体一致，参考 loan/convert_images 的字体逻辑
    _CUSTOM_ZH_FONT = "/usr/share/fonts/truetype/custom/FangSong_GB2312.ttf"

    def _get_font_for_fallback(self, size: int) -> ImageFont.FreeTypeFont:
        """获取可用于中文的字体（优先 Dockerfile 安装的 FangSong_GB2312，与 loan 一致）"""
        paths = [
            self._CUSTOM_ZH_FONT,
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def get_simsun_font(self, size: int = 32) -> ImageFont.FreeTypeFont:
        """获取正文字体（宋体风格），与 loan 一致优先使用环境中文字体"""
        return self._get_font_for_fallback(size)

    def get_fangsong_font(self, size: int = 32) -> ImageFont.FreeTypeFont:
        """获取仿宋字体，与 loan 一致优先使用环境中文字体"""
        return self._get_font_for_fallback(size)

    def find_clean_template_image(self, directory: str) -> Optional[str]:
        """
        查找干净的原始模板图

        Args:
            directory: 搜索目录

        Returns:
            模板图像路径或None
        """
        # 优先检查预设模板名
        for name in TEMPLATE_NAMES:
            path = os.path.join(directory, name)
            logger.info(f"检查预设模板图: {path}")
            if os.path.exists(path):
                logger.info(f"找到预设模板图: {name}")
                return path

        # 遍历所有图像，跳过输出图
        candidates = []
        for filename in os.listdir(directory):
            if filename.lower().endswith(IMAGE_EXTENSIONS) and not self.is_output_image(filename):
                candidates.append(filename)

        if candidates:
            chosen = sorted(candidates)[0]
            logger.info(f"未找到预设模板，选用首个非输出图: {chosen}")
            return os.path.join(directory, chosen)

        return None

    def draw_text_in_bbox(self, image: np.ndarray, bbox: List[int], text: str,
                        is_first_four: bool = False) -> np.ndarray:
        """
        在指定bbox中绘制文本

        Args:
            image: 输入图像
            bbox: 边界框坐标 [x1, y1, x2, y2]
            text: 要绘制的文本
            is_first_four: 是否为前4个字段（使用仿宋字体）

        Returns:
            绘制后的图像
        """
        if image is None:
            return image

        h, w = image.shape[:2]
        x1 = int(int(bbox[0]) / 1000 * w)
        y1 = int(int(bbox[1]) / 1000 * h)
        x2 = int(int(bbox[2]) / 1000 * w)
        y2 = int(int(bbox[3]) / 1000 * h)

        x1, x2 = max(0, min(w, x1)), max(0, min(w, x2))
        y1, y2 = max(0, min(h, y1)), max(0, min(h, y2))
        if x1 >= x2 or y1 >= y2:
            return image

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)

        bbox_width = x2 - x1
        bbox_height = y2 - y1

        base_font_size = max(8, min(60, int(bbox_height * 1.1)))

        final_font = None
        text_w = 0
        found = False

        for size in range(base_font_size, 7, -1):
            candidate_font = self.get_fangsong_font(size) if is_first_four else self.get_simsun_font(size)
            try:
                l, t, r, b = draw.textbbox((0, 0), text, font=candidate_font)
                text_w = r - l
            except Exception:
                text_w, _ = draw.textsize(text, font=candidate_font)

            if text_w <= bbox_width - 4:
                final_font = candidate_font
                found = True
                break

        if not found:
            final_font = self.get_fangsong_font(8) if is_first_four else self.get_simsun_font(8)
            try:
                l, t, r, b = draw.textbbox((0, 0), text, font=final_font)
                text_w = r - l
            except Exception:
                text_w, _ = draw.textsize(text, font=final_font)

        try:
            _, top, _, bottom = draw.textbbox((0, 0), text, font=final_font)
            text_h = bottom - top
        except Exception:
            _, text_h = draw.textsize(text, font=final_font)

        if is_first_four:
            text_x = x1 + (bbox_width - text_w) // 2
            text_y = y1 + (bbox_height - text_h) // 2
        else:
            padding_left = 2
            text_x = x1 + padding_left
            text_y = y1 + (bbox_height - text_h) // 2

        text_x = max(0, min(text_x, w - 2))
        text_y = max(0, min(text_y, h - 2))

        draw_kwargs = {
            "xy": (text_x, text_y),
            "text": text,
            "fill": (0, 0, 0),
            "font": final_font,
        }

        if is_first_four:
            draw_kwargs["stroke_width"] = 1
            draw_kwargs["stroke_fill"] = (0, 0, 0)

        try:
            draw.text(**draw_kwargs)
        except TypeError:
            draw.text((text_x, text_y), text, fill=(0, 0, 0), font=final_font)

        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def process_json_file(self, json_path: str, template_image_path: str) -> List[str]:
        """
        处理JSON文件，生成填充后的图像

        Args:
            json_path: JSON文件路径
            template_image_path: 模板图像路径

        Returns:
            生成的图像路径列表
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"无法读取 JSON 文件 {json_path}: {e}")
            return []

        batches = []

        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, list):
                batches = data
            elif isinstance(first_item, dict):
                valid_items = []
                for item in data:
                    if not (isinstance(item, dict) and 'type' in item and 'bbox' in item):
                        continue
                    if not (isinstance(item['bbox'], list) and len(item['bbox']) == 4):
                        continue
                    try:
                        [int(x) for x in item['bbox']]
                        valid_items.append(item)
                    except (ValueError, TypeError):
                        continue
                for i in range(0, len(valid_items), 13):
                    batches.append(valid_items[i:i + 13])
            else:
                logger.warning(f"JSON 首元素类型不支持: {type(first_item)}")
                return []
        elif isinstance(data, dict):
            if 'type' in data and 'bbox' in data:
                batches = [[data]]
            else:
                logger.warning(f"JSON 文件 {json_path} 不是有效标注格式。")
                return []
        else:
            logger.warning(f"JSON 根类型不支持: {type(data)}")
            return []

        if not batches:
            logger.warning(f"{json_path} 中未解析出任何批次，跳过。")
            return []

        # 获取原始模板图像的扩展名
        _, ext = os.path.splitext(template_image_path)
        output_files = []

        for batch_idx, batch in enumerate(batches):
            valid_batch = []
            for item in batch:
                if not (isinstance(item, dict) and 'type' in item and 'bbox' in item):
                    continue
                if not (isinstance(item['bbox'], list) and len(item['bbox']) == 4):
                    continue
                try:
                    [int(x) for x in item['bbox']]
                    valid_batch.append(item)
                except (ValueError, TypeError):
                    continue

            if not valid_batch:
                logger.warning(f"批次 {batch_idx + 1} 无有效标注项，跳过。")
                continue

            # 从原始模板文件重新读取
            original_image = cv2.imread(template_image_path)
            if original_image is None:
                logger.error(f"无法加载模板图: {template_image_path}")
                continue

            # 在 fresh copy 上绘制
            image_to_draw = original_image.copy()

            for local_idx, item in enumerate(valid_batch):
                text = str(item['type'])
                bbox = item['bbox']
                is_first_four = (local_idx < 4)
                image_to_draw = self.draw_text_in_bbox(image_to_draw, bbox, text, is_first_four=is_first_four)

            json_base = os.path.splitext(os.path.basename(json_path))[0]
            output_path = self.output_dir / f"{json_base}_filled_{batch_idx + 1:02d}{ext}"

            success = cv2.imwrite(str(output_path), image_to_draw)
            if success:
                logger.info(f"已保存: {output_path.name}")
                output_files.append(str(output_path))
            else:
                logger.error(f"保存失败: {output_path.name}")

        return output_files

    def convert_batch(self, json_files: List[str]) -> List[str]:
        """
        批量转换JSON文件为图像

        Args:
            json_files: JSON文件路径列表

        Returns:
            生成的图像路径列表
        """
        all_output_files = []

        # 查找模板图像
        template_path = self.find_clean_template_image(str(self.input_dir))
        if not template_path:
            logger.error("未找到可用的原始模板图！")
            return all_output_files

        logger.info(f"使用模板图: {os.path.basename(template_path)}")

        for json_file in json_files:
            logger.info(f"正在处理: {os.path.basename(json_file)}")
            output_files = self.process_json_file(json_file, template_path)
            all_output_files.extend(output_files)

        return all_output_files
