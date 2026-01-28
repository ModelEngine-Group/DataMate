"""
图像增强器 - 不动产权证
将电子凭证图像合成到真实拍摄场景中
"""
import cv2
import numpy as np
import json
import os
from pathlib import Path
from typing import Optional, List
from loguru import logger


class ImageAugmenter:
    """图像增强器 - 不动产权证"""

    def __init__(self, coord_cache_file: str = "coordinates_cache.json", bg_dir: str = "backgrounds"):
        """
        初始化图像增强器

        Args:
            coord_cache_file: 坐标缓存文件路径
            bg_dir: 背景图目录
        """
        self.coord_cache_file = coord_cache_file
        self.bg_dir = Path(bg_dir)
        if not self.bg_dir.exists():
            self.bg_dir.mkdir(parents=True, exist_ok=True)

    def cv_imread(self, file_path: str) -> Optional[np.ndarray]:
        """读取含中文路径的图片"""
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def cv_imwrite(self, file_path: str, img: np.ndarray) -> bool:
        """写入含中文路径的图片"""
        is_success, im_buf = cv2.imencode(".jpg", img)
        if is_success:
            im_buf.tofile(file_path)
            return True
        return False

    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        重排坐标点顺序：左上, 右上, 右下, 左下
        """
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def load_cached_coordinates(self, image_path: str) -> Optional[np.ndarray]:
        """从缓存文件加载坐标"""
        if not os.path.exists(self.coord_cache_file):
            return None
        try:
            with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = str(image_path).replace("\\", "/")
            if key in data:
                return np.array(data[key], dtype="float32")
        except Exception as e:
            logger.error(f"读取缓存文件失败: {e}")
        return None

    def save_cached_coordinates(self, image_path: str, coords: np.ndarray):
        """保存坐标到缓存文件"""
        data = {}
        if os.path.exists(self.coord_cache_file):
            try:
                with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        key = str(image_path).replace("\\", "/")
        data[key] = coords.tolist()
        try:
            with open(self.coord_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")

    def detect_document_corners(self, image_path: str, debug: bool = False) -> Optional[np.ndarray]:
        """
        智能识别文档区域

        Args:
            image_path: 图像路径
            debug: 是否生成调试图像

        Returns:
            文档区域的四个角点坐标
        """
        # 检查缓存
        cached_pts = self.load_cached_coordinates(image_path)
        if cached_pts is not None:
            return self.order_points(cached_pts)

        image = self.cv_imread(image_path)
        if image is None:
            logger.warning(f"无法读取图片: {image_path}")
            return None

        # 降采样加速处理
        ratio = image.shape[0] / 800.0
        orig = image.copy()
        processed_img = cv2.resize(image, (int(image.shape[1] / ratio), 800))

        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)

        # 双边滤波 + CLAHE
        gray = cv2.bilateralFilter(gray, 11, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Canny 边缘检测
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
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                screenCnt = np.int64(box)
                break

        if screenCnt is not None:
            detected_pts = (screenCnt * ratio).astype(np.float32)
            return self.order_points(detected_pts)
        return None

    def determine_scene_mode(self, bg_filename: str) -> str:
        """
        根据背景文件名确定场景模式

        Args:
            bg_filename: 背景图文件名

        Returns:
            场景模式字符串
        """
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

    def augment_images(self, src_files: List[str], scenes: List[str] = None,
                    skip_detect: bool = False, output_dir: str = "images_output") -> List[str]:
        """
        批量增强图像

        Args:
            src_files: 源图像文件列表
            scenes: 允许的场景列表
            skip_detect: 是否跳过检测，仅使用缓存坐标
            output_dir: 输出目录

        Returns:
            生成的图像路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 获取背景图列表
        all_bg_files = list(self.bg_dir.glob("*"))
        bg_files = [f for f in all_bg_files 
                   if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]

        # 过滤背景图
        filtered_bg_files = []
        for bg_file in bg_files:
            bg_name = bg_file.name
            scene_mode = self.determine_scene_mode(bg_name)
            if scenes is None or scene_mode in scenes:
                filtered_bg_files.append(bg_file)

        if not filtered_bg_files:
            logger.warning("没有可用的背景图")
            return []

        output_files = []

        for src_file in src_files:
            src_name = Path(src_file).stem
            logger.info(f"处理源图: {src_name}")

            for bg_file in filtered_bg_files:
                bg_name = bg_file.stem
                scene_mode = self.determine_scene_mode(bg_file.name)

                # 输出文件名
                output_filename = f"{src_name}_{bg_name}.jpg"
                output_file_path = output_path / output_filename

                # 获取坐标
                if skip_detect:
                    corners = self.load_cached_coordinates(bg_file.name)
                    if corners is None:
                        logger.info(f"跳过: {bg_file.name} (无缓存坐标)")
                        continue
                else:
                    corners = self.detect_document_corners(str(bg_file))
                    if corners is None:
                        logger.info(f"跳过: {bg_file.name} (无法检测到文档区域)")
                        continue
                    self.save_cached_coordinates(str(bg_file), corners)

                # 执行合成
                enable_ratio_fix = scene_mode in ["normal", "tilted", "watermark", "incomplete"]
                enable_auto_rotate = scene_mode in ["tilted", "watermark", "incomplete"]

                # 简化合成逻辑
                src = self.cv_imread(src_file)
                dst = self.cv_imread(str(bg_file))
                if src is None or dst is None:
                    logger.error(f"无法读取图片")
                    continue

                # 透视变换
                h_src, w_src = src.shape[:2]
                src_pts = np.array([[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]], dtype="float32")
                dst_pts = np.array(corners, dtype="float32")

                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

                # 创建掩模
                mask = np.zeros(dst.shape[:2], dtype=np.uint8)
                cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

                # 简单融合
                try:
                    center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
                              int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))
                    final_output = cv2.seamlessClone(warped_src, dst, mask, center, cv2.NORMAL_CLONE)
                except Exception as e:
                    logger.warning(f"融合失败: {e}")
                    final_output = dst.copy()
                    final_output[mask > 0] = warped_src[mask > 0]

                if self.cv_imwrite(str(output_file_path), final_output):
                    logger.info(f"成功: {output_filename}")
                    output_files.append(str(output_file_path))
                else:
                    logger.error(f"失败: {output_filename}")

        return output_files
