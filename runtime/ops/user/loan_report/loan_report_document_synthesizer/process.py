# -*- coding: utf-8 -*-

"""
Description:
    文档合成器 - 将电子文档与实拍背景合成，生成仿真图片
Create: 2025/01/28
"""

import json
import os
from typing import Dict, Any

import cv2
import numpy as np
from loguru import logger

from datamate.core.base_op import Mapper


class LoanReportDocumentSynthesizer(Mapper):
    """文档合成器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._background_dir = os.path.join(os.path.dirname(__file__), "backgrounds")
        self._output_dir = None
        self._enable_watermark = bool(kwargs.get("enable_watermark", False))
        self._enable_shadow = bool(kwargs.get("enable_shadow", False))
        self._scene_mode = kwargs.get("scene_mode", "auto")

        # 坐标缓存文件
        self._coord_file = os.path.join(os.path.dirname(__file__), "coordinates.json")

    def _cv_imread(self, file_path: str):
        """读取含中文路径的图片"""
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def _cv_imwrite(self, file_path: str, img):
        """保存含中文路径的图片"""
        return cv2.imencode(".jpg", img)[1].tofile(file_path)

    def _load_cached_coordinates(self, image_path: str):
        """尝试从JSON文件加载缓存的坐标"""
        if not os.path.exists(self._coord_file):
            return None

        try:
            with open(self._coord_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            key = image_path.replace("\\", "/")
            if key in data:
                logger.info(f"从缓存加载坐标: {os.path.basename(image_path)}")
                return np.array(data[key], dtype="float32")
        except Exception as e:
            logger.warning(f"读取缓存坐标失败: {e}")

        return None

    def _save_cached_coordinates(self, image_path: str, coords):
        """将坐标保存到JSON文件"""
        data = {}
        if os.path.exists(self._coord_file):
            try:
                with open(self._coord_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass

        key = image_path.replace("\\", "/")
        data[key] = coords.tolist()

        try:
            with open(self._coord_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"坐标已保存至缓存")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """重排坐标点顺序：左上, 右上, 右下, 左下"""
        rect = np.zeros((4, 2), dtype="float32")

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _detect_document_corners(self, image_path: str):
        """智能识别文档四个角点"""
        # 检查缓存
        cached_pts = self._load_cached_coordinates(image_path)
        if cached_pts is not None:
            return self._order_points(cached_pts)

        image = self._cv_imread(image_path)
        if image is None:
            logger.error(f"无法读取图片: {image_path}")
            return None

        # 预处理
        ratio = image.shape[0] / 800.0
        processed_img = cv2.resize(image, (int(image.shape[1] / ratio), 800))

        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 75, 75)

        # CLAHE增强
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Canny边缘检测
        v = np.median(gray)
        sigma = 0.33
        lower_thresh = int(max(0, (1.0 - sigma) * v))
        upper_thresh = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(gray, lower_thresh, upper_thresh)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edged = cv2.dilate(edged, kernel, iterations=1)

        # 轮廓提取
        cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        screenCnt = None
        logger.info("正在自动识别文档角点...")

        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                screenCnt = np.int64(box)
                logger.info(f"-> 锁定候选轮廓，面积: {cv2.contourArea(c)}")
                break

        if screenCnt is not None:
            detected_pts = (screenCnt * ratio).astype(np.float32)
            ordered_pts = self._order_points(detected_pts)
            logger.info("自动识别成功")
            return ordered_pts
        else:
            logger.warning("自动识别失败，文档可能不在画面中")
            return None

    def _add_watermark_to_source(self, src: np.ndarray, text: str = "INTERNAL ONLY") -> np.ndarray:
        """在源图上添加水印"""
        h_src, w_src = src.shape[:2]
        max_dim = max(h_src, w_src)
        canvas_size = int(max_dim * 2.5)

        canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)
        thickness = 2
        scale = 1.0
        color = (230, 230, 230)
        font = cv2.FONT_HERSHEY_DUPLEX

        (t_w, t_h), _ = cv2.getTextSize(text, font, scale, thickness)
        step_x = int(t_w * 1.8)
        step_y = int(t_h * 12.0)

        for y in range(-canvas_size, canvas_size * 2, step_y):
            offset_x = ((y // step_y) % 2) * (step_x // 2)
            for x in range(-canvas_size, canvas_size * 2, step_x):
                draw_x = x + offset_x
                draw_y = y
                if -t_w < draw_x < canvas_size + t_w and -t_h < draw_y < canvas_size + t_h:
                    cv2.putText(canvas, text, (draw_x, draw_y), font, scale, color, thickness)

        # 旋转
        center = (canvas_size // 2, canvas_size // 2)
        M = cv2.getRotationMatrix2D(center, 30, 1.0)
        rotated_canvas = cv2.warpAffine(canvas, M, (canvas_size, canvas_size), borderValue=(255, 255, 255))

        # 裁剪
        start_y = (canvas_size - h_src) // 2
        start_x = (canvas_size - w_src) // 2
        watermark_crop = rotated_canvas[start_y: start_y + h_src, start_x: start_x + w_src]

        if watermark_crop.shape[:2] != (h_src, w_src):
            watermark_crop = cv2.resize(watermark_crop, (w_src, h_src))

        # 混合
        src_f = src.astype(float)
        wm_f = watermark_crop.astype(float) / 255.0
        out = src_f * wm_f

        return out.astype(np.uint8)

    def _synthesize_images(self, src_path: str, dst_path: str, dst_corners: np.ndarray, output_path: str):
        """合成主函数"""
        src = self._cv_imread(src_path)
        dst = self._cv_imread(dst_path)

        if src is None or dst is None:
            logger.error(f"无法读取图片")
            return False

        # 准备透视变换
        h_src, w_src = src.shape[:2]
        src_pts = np.array([[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]], dtype="float32")
        dst_pts = np.array(dst_corners, dtype="float32")

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

        # 创建掩模
        mask = np.zeros(dst.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

        # 色彩空间匹配
        dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
        warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)

        dst_region_l = dst_lab[:, :, 0][mask > 0]
        if dst_region_l.size == 0:
            logger.warning("目标区域掩模为空")
            return False

        l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
        src_region_l = warped_lab[:, :, 0][mask > 0]
        l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

        # 调整光照
        contrast_factor = 0.95 if self._enable_shadow else 1.0
        l_channel = warped_lab[:, :, 0].astype(float)
        l_channel = (l_channel - l_mean_src) * (l_std_dst / (l_std_src + 1e-5)) * contrast_factor + l_mean_dst
        l_channel = np.clip(l_channel, 0, 255).astype(np.uint8)
        warped_lab[:, :, 0] = l_channel

        matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)

        # 泊松融合
        center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
                  int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))

        try:
            final_output = cv2.seamlessClone(matched_src, dst, mask, center, cv2.NORMAL_CLONE)
        except Exception as e:
            logger.warning(f"融合失败，降级为直接覆盖: {e}")
            final_output = dst.copy()
            final_output[mask > 0] = matched_src[mask > 0]

        # 保存结果
        self._cv_imwrite(output_path, final_output)
        logger.info(f"合成图已保存至: {output_path}")
        return True

    def _get_scene_mode(self, bg_filename: str) -> str:
        """根据文件名确定场景模式"""
        if self._scene_mode != "auto":
            return self._scene_mode

        if "3-" in bg_filename or "斜拍" in bg_filename:
            return "tilted"
        elif "4-" in bg_filename or "阴影" in bg_filename:
            return "shadow"
        elif "5-" in bg_filename or "水印" in bg_filename:
            return "watermark"
        elif "6-" in bg_filename or "不完整" in bg_filename:
            return "incomplete"
        else:
            return "normal"

    def _process_single_pair(self, src_file: str, bg_file: str) -> bool:
        """处理单个源图和背景图配对"""
        src_base_name = os.path.splitext(os.path.basename(src_file))[0]
        bg_base_name = os.path.splitext(os.path.basename(bg_file))[0]

        output_filename = f"{src_base_name}_{bg_base_name}.jpg"
        output_path = os.path.join(self._output_dir, output_filename)

        # 获取背景图坐标
        detected_corners = self._detect_document_corners(bg_file)
        if detected_corners is None:
            logger.warning(f"跳过: {bg_file} (无法识别坐标)")
            return False

        scene = self._get_scene_mode(bg_file)
        logger.info(f"处理背景: {bg_file} (场景: {scene})")

        return self._synthesize_images(src_file, bg_file, detected_corners, output_path)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行文档合成"""
        self._output_dir = sample['export_path'] + "/images"

        # 获取源图目录
        src_dir = self._output_dir
        if not os.path.exists(src_dir):
            logger.error(f"源图目录不存在: {src_dir}")
            return sample

        # 获取背景图目录
        if not os.path.exists(self._background_dir):
            logger.error(f"背景图目录不存在: {self._background_dir}")
            return sample

        # 获取源图文件列表
        src_files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        src_files = [os.path.join(src_dir, f) for f in src_files]
        src_files.sort()

        if not src_files:
            logger.warning(f"源图目录中没有图片文件")
            return sample

        # 获取背景图文件列表
        bg_files = [f for f in os.listdir(self._background_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        bg_files = [f for f in bg_files if "debug" not in f]
        bg_files.sort()

        if not bg_files:
            logger.warning(f"背景图目录中没有图片文件")
            return sample

        logger.info(f"找到 {len(src_files)} 张源图, {len(bg_files)} 张背景图")

        # 遍历处理
        success_count = 0
        total_tasks = len(src_files) * len(bg_files)
        task_count = 0

        for src_file in src_files:
            logger.info(f"\n处理源图: {os.path.basename(src_file)}")

            for bg_file in bg_files:
                bg_file_path = os.path.join(self._background_dir, bg_file)
                task_count += 1

                if self._process_single_pair(src_file, bg_file_path):
                    success_count += 1

        logger.info(f"\n处理完成: 成功 {success_count}/{total_tasks}")

        return sample
