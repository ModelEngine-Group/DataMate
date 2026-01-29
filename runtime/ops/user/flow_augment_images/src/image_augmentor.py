"""
图像增强模块 - 用于将文档图像合成到真实背景中
"""

import os
import sys
import json
import random
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class ImageAugmentor:
    """图像增强器类"""

    def __init__(self, bg_dir: str, coord_cache_file: Optional[str] = None,
                 skip_detect: bool = True, allowed_scenes: List[str] = None):
        """
        初始化图像增强器

        Args:
            bg_dir: 背景图片目录
            coord_cache_file: 坐标缓存文件路径
            skip_detect: 是否跳过坐标检测
            allowed_scenes: 允许的场景列表
        """
        self.bg_dir = bg_dir
        self.skip_detect = skip_detect
        self.allowed_scenes = allowed_scenes or ['normal']
        self.coord_cache_file = coord_cache_file or os.path.join(bg_dir, "coordinates_cache.json")

        # 预加载背景图列表
        self.bg_files = self._load_background_files()

    def _load_background_files(self) -> List[Path]:
        """加载背景图文件列表"""
        bg_path = Path(self.bg_dir)
        all_bg_files = [f for f in bg_path.glob("*") 
                       if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        return all_bg_files

    def _determine_scene_mode(self, bg_filename: str) -> str:
        """根据背景图文件名确定场景模式"""
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

    def _cv_imread(self, file_path: str) -> Optional[np.ndarray]:
        """读取含中文路径的图片"""
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def _cv_imwrite(self, file_path: str, img: np.ndarray) -> bool:
        """保存含中文路径的图片"""
        is_success, im_buf = cv2.imencode(".jpg", img)
        if is_success:
            im_buf.tofile(file_path)
            return True
        return False

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """重排坐标点顺序：左上, 右上, 右下, 左下"""
        rect = np.zeros((4, 2), dtype="float32")

        # 坐标点求和
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # 坐标点差值
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _load_cached_coordinates(self, image_path: str) -> Optional[np.ndarray]:
        """从缓存文件加载坐标"""
        if not os.path.exists(self.coord_cache_file): 
            return None

        try:
            with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            key = os.path.basename(image_path)
            if key in data: 
                return np.array(data[key], dtype="float32")
        except: 
            pass

        return None

    def _save_cached_coordinates(self, image_path: str, coords: np.ndarray):
        """保存坐标到缓存文件"""
        data = {}
        if os.path.exists(self.coord_cache_file):
            try:
                with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except: 
                pass

        key = os.path.basename(image_path)
        data[key] = coords.tolist()

        try:
            with open(self.coord_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except: 
            pass

    def _detect_document_corners(self, image_path: str, debug: bool = False) -> Optional[np.ndarray]:
        """智能识别文档区域，支持坐标缓存"""
        # 检查缓存
        cached_pts = self._load_cached_coordinates(image_path)
        if cached_pts is not None:
            return self._order_points(cached_pts)

        image = self._cv_imread(image_path)
        if image is None:
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
            return self._order_points(detected_pts)
        else:
            return None

    def _auto_rotate_to_match_orientation(self, src: np.ndarray, 
                                      dst_corners: np.ndarray) -> np.ndarray:
        """检查源图与目标区域的方向是否一致，不一致则自动旋转源图90度"""
        # 计算目标区域的大致宽高
        (tl, tr, br, bl) = dst_corners
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        dst_w = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        dst_h = max(int(heightA), int(heightB))

        h_src, w_src = src.shape[:2]

        # 判断是否为横版
        src_is_landscape = w_src > h_src
        dst_is_landscape = dst_w > dst_h

        if src_is_landscape != dst_is_landscape:
            src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

        return src

    def _pad_src_to_match_ratio(self, src: np.ndarray, 
                              dst_corners: np.ndarray) -> np.ndarray:
        """为源图补白边，使其宽高比与目标区域一致"""
        # 计算目标区域的宽高
        (tl, tr, br, bl) = dst_corners
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst_ratio = maxWidth / float(maxHeight)

        h_src, w_src = src.shape[:2]
        src_ratio = w_src / float(h_src)

        # 如果比例差不多，就不动了
        if abs(src_ratio - dst_ratio) < 0.1:
            return src

        # 根据比例差异进行填充
        pad_h, pad_w = 0, 0

        if src_ratio > dst_ratio:
            # 源图比目标更"扁/胖"，需要上下补白
            new_h = int(w_src / dst_ratio)
            total_pad = new_h - h_src
            pad_top = total_pad // 2
            pad_bot = total_pad - pad_top
            src_padded = cv2.copyMakeBorder(src, pad_top, pad_bot, 0, 0, 
                                         cv2.BORDER_CONSTANT, value=(255, 255, 255))
        else:
            # 源图比目标更"瘦/高"，需要左右补白
            new_w = int(h_src * dst_ratio)
            total_pad = new_w - w_src
            pad_left = total_pad // 2
            pad_right = total_pad - pad_left
            src_padded = cv2.copyMakeBorder(src, 0, 0, pad_left, pad_right, 
                                         cv2.BORDER_CONSTANT, value=(255, 255, 255))

        return src_padded

    def _add_watermark_to_source(self, src: np.ndarray, 
                              text: str = "INTERNAL ONLY FOR TESTING PURPOSE") -> np.ndarray:
        """在源图上添加倾斜、半透明的水印"""
        h_src, w_src = src.shape[:2]
        max_dim = max(h_src, w_src)

        # 创建超大背景
        canvas_size = int(max_dim * 2.5)
        canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)

        # 参数设置
        thickness = 2
        scale = 1.0
        color = (230, 230, 230)
        font = cv2.FONT_HERSHEY_DUPLEX

        (t_w, t_h), _ = cv2.getTextSize(text, font, scale, thickness)

        # 稀疏平铺
        step_x = int(t_w * 1.8)
        step_y = int(t_h * 12.0)

        for y in range(-canvas_size, canvas_size * 2, step_y):
            offset_x = ((y // step_y) % 2) * (step_x // 2)

            for x in range(-canvas_size, canvas_size * 2, step_x):
                draw_x = x + offset_x
                draw_y = y

                if -t_w < draw_x < canvas_size + t_w and -t_h < draw_y < canvas_size + t_h:
                    cv2.putText(canvas, text, (draw_x, draw_y), font, scale, color, thickness)

        # 旋转画布
        center = (canvas_size // 2, canvas_size // 2)
        angle = 30
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_canvas = cv2.warpAffine(canvas, M, (canvas_size, canvas_size), 
                                     borderValue=(255, 255, 255))

        # 精准中心裁剪
        start_y = (canvas_size - h_src) // 2
        start_x = (canvas_size - w_src) // 2
        watermark_crop = rotated_canvas[start_y: start_y + h_src, 
                                   start_x: start_x + w_src]

        # 混合
        src_f = src.astype(float)
        wm_f = watermark_crop.astype(float) / 255.0
        out = src_f * wm_f
        return out.astype(np.uint8)

    def _base_synthesis_pipeline(self, src_path: str, dst_path: str, 
                              dst_corners: np.ndarray, output_path: str,
                              mode: str = "normal", enable_ratio_fix: bool = False,
                              enable_auto_rotate: bool = False, 
                              enable_watermark: bool = False) -> bool:
        """基础合成流水线"""
        # 1. 读取图像
        src = self._cv_imread(src_path)
        dst = self._cv_imread(dst_path)
        if src is None or dst is None:
            return False

        # 2. 自动旋转校正方向
        if enable_auto_rotate:
            src = self._auto_rotate_to_match_orientation(src, dst_corners)

        # 3. 比例自适应校正
        if enable_ratio_fix:
            src = self._pad_src_to_match_ratio(src, dst_corners)

        # 4. 添加水印
        if enable_watermark:
            src = self._add_watermark_to_source(src)

        # 5. 准备透视变换
        h_src, w_src = src.shape[:2]
        src_pts = np.array([[0, 0], [w_src - 1, 0], 
                          [w_src - 1, h_src - 1], [0, h_src - 1]], 
                         dtype="float32")
        dst_pts = np.array(dst_corners, dtype="float32")

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

        # 6. 创建掩模
        mask = np.zeros(dst.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

        # 7. 色彩空间匹配
        dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
        warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)

        dst_region_l = dst_lab[:, :, 0][mask > 0]
        if dst_region_l.size == 0:
            return False

        l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
        src_region_l = warped_lab[:, :, 0][mask > 0]
        l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

        # 针对不同模式，微调光照参数
        contrast_factor = 1.0
        if mode == "shadow":
            contrast_factor = 0.85
        elif mode == "tilted":
            contrast_factor = 0.95

        l_channel = warped_lab[:, :, 0].astype(float)
        l_channel = (l_channel - l_mean_src) * (l_std_dst / (l_std_src + 1e-5)) * contrast_factor + l_mean_dst
        warped_lab[:, :, 0] = np.clip(l_channel, 0, 255).astype(np.uint8)

        matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)

        # 8. 泊松融合
        center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
                  int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))

        try:
            final_output = cv2.seamlessClone(matched_src, dst, mask, center, cv2.NORMAL_CLONE)
        except:
            final_output = dst.copy()
            final_output[mask > 0] = matched_src[mask > 0]

        # 9. 保存
        return self._cv_imwrite(output_path, final_output)

    def process_normal_scene(self, src_path: str, dst_path: str, 
                         dst_corners: np.ndarray, output_path: str):
        """场景：正常拍摄（正对或微倾斜，光照均匀）"""
        return self._base_synthesis_pipeline(src_path, dst_path, dst_corners, 
                                       output_path, mode="normal", 
                                       enable_ratio_fix=True)

    def process_tilted_scene(self, src_path: str, dst_path: str, 
                           dst_corners: np.ndarray, output_path: str):
        """场景：斜拍（透视变形较大）"""
        return self._base_synthesis_pipeline(src_path, dst_path, dst_corners, 
                                       output_path, mode="tilted", 
                                       enable_ratio_fix=True,
                                       enable_auto_rotate=True)

    def process_shadow_scene(self, src_path: str, dst_path: str, 
                         dst_corners: np.ndarray, output_path: str):
        """场景：有阴影（光照不均匀，有投影）"""
        return self._base_synthesis_pipeline(src_path, dst_path, dst_corners, 
                                       output_path, mode="shadow", 
                                       enable_ratio_fix=True,
                                       enable_auto_rotate=True)

    def process_watermark_scene(self, src_path: str, dst_path: str, 
                            dst_corners: np.ndarray, output_path: str):
        """场景：有水印（桌面或背景有复杂纹理）"""
        return self._base_synthesis_pipeline(src_path, dst_path, dst_corners, 
                                       output_path, mode="watermark", 
                                       enable_ratio_fix=True,
                                       enable_auto_rotate=True, 
                                       enable_watermark=True)

    def process_incomplete_scene(self, src_path: str, dst_path: str, 
                            dst_corners: np.ndarray, output_path: str):
        """场景：拍摄不完整（凭证部分在画面外）"""
        return self._base_synthesis_pipeline(src_path, dst_path, dst_corners, 
                                       output_path, mode="incomplete", 
                                       enable_ratio_fix=True,
                                       enable_auto_rotate=True)

    def augment_batch(self, src_files: List[str], scenes: int = 2) -> List[str]:
        """
        批量增强图片

        Args:
            src_files: 源图片文件路径列表
            scenes: 每张图随机选择的场景数量

        Returns:
            生成的增强图片路径列表
        """
        output_files = []

        # 过滤背景图
        filtered_bg_files = []
        for bg_file in self.bg_files:
            bg_name = bg_file.name
            scene_mode = self._determine_scene_mode(bg_name)
            if scene_mode in self.allowed_scenes:
                filtered_bg_files.append(bg_file)

        use_random_selection = scenes is not None and scenes < len(filtered_bg_files)

        for src_file in src_files:
            src_name = Path(src_file).stem

            # 如果启用随机选择，从背景图中随机选择指定数量
            if use_random_selection:
                selected_bg_files = random.sample(filtered_bg_files, scenes)
            else:
                selected_bg_files = filtered_bg_files

            for bg_file in selected_bg_files:
                bg_name = bg_file.name
                scene_mode = self._determine_scene_mode(bg_name)

                # 输出文件名：源图名_背景图名.jpg
                output_filename = f"{src_name}_{bg_name.stem}.jpg"
                output_path = Path(src_file).parent / output_filename

                # 检测或加载坐标
                if self.skip_detect:
                    corners = self._load_cached_coordinates(bg_file.name)
                    if corners is None:
                        continue
                else:
                    corners = self._detect_document_corners(str(bg_file))
                    if corners is None:
                        continue

                    # 保存检测到的坐标到缓存
                    self._save_cached_coordinates(str(bg_file), corners)

                # 根据场景模式选择处理函数
                success = False
                if scene_mode == "normal":
                    success = self.process_normal_scene(src_file, str(bg_file), 
                                                  corners, str(output_path))
                elif scene_mode == "tilted":
                    success = self.process_tilted_scene(src_file, str(bg_file), 
                                                   corners, str(output_path))
                elif scene_mode == "shadow":
                    success = self.process_shadow_scene(src_file, str(bg_file), 
                                                  corners, str(output_path))
                elif scene_mode == "watermark":
                    success = self.process_watermark_scene(src_file, str(bg_file), 
                                                     corners, str(output_path))
                elif scene_mode == "incomplete":
                    success = self.process_incomplete_scene(src_file, str(bg_file), 
                                                     corners, str(output_path))

                if success:
                    output_files.append(str(output_path))

        return output_files
