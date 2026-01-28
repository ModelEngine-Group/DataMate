import os
import sys
import json
import random
import cv2
from loguru import logger
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datamate.core.base_op import Mapper

class ImgAugOperator(Mapper):
    """
    图像增强合成算子：ImgAugOperator
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 处理场景参数 (checkbox 返回的是 list 或 逗号分隔字符串，需兼容)
        self.scenes = int(kwargs.get('scenes', 2))
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = scenes_val.split(',')
        else:
            self.allowed_scenes = scenes_val if scenes_val else ['normal']
            
        self.skip_detect = kwargs.get('skipDetectParam', True)

            
        # 3. 预加载背景图列表
        self.bg_dir = os.path.join(os.path.dirname(__file__), "backgrounds")
        
        # 4. 坐标缓存文件路径 (存放在算子目录下)
        self.coord_cache_file = os.path.join(os.path.dirname(__file__), "coordinates_cache.json")

    def _determine_scene_mode(self, bg_filename: str) -> str:
        if "3-" in bg_filename or "斜拍" in bg_filename: return "tilted"
        elif "4-" in bg_filename or "阴影" in bg_filename: return "shadow"
        elif "5-" in bg_filename or "水印" in bg_filename: return "watermark"
        elif "6-" in bg_filename or "不完整" in bg_filename: return "incomplete"
        else: return "normal"

    # --- 以下为核心 CV 处理函数 (源自原始脚本) ---

    def _cv_imread(self, file_path: str) -> Optional[np.ndarray]:
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def _cv_imwrite(self, file_path: str, img: np.ndarray) -> bool:
        is_success, im_buf = cv2.imencode(".jpg", img)
        if is_success:
            im_buf.tofile(file_path)
            return True
        return False

    def _load_cached_coordinates(self, image_path: str) -> Optional[np.ndarray]:
        if not os.path.exists(self.coord_cache_file): return None
        try:
            with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = str(image_path).replace("\\", "/")
            if key in data: return np.array(data[key], dtype="float32")
        except: pass
        return None

    def _save_cached_coordinates(self, image_path: str, coords: np.ndarray):
        data = {}
        if os.path.exists(self.coord_cache_file):
            try:
                with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except: pass
        key = str(image_path).replace("\\", "/")
        data[key] = coords.tolist()
        try:
            with open(self.coord_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except: pass

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def _detect_document_corners(self, image_path: str) -> Optional[np.ndarray]:
        """智能识别文档区域，支持坐标缓存"""
        # 检查缓存
        cached_pts = self._load_cached_coordinates(image_path)
        if cached_pts is not None:
            return self._order_points(cached_pts)

        image = self._cv_imread(image_path)
        if image is None:
            logger.warning(f"  无法读取图片: {image_path}")
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

    def _base_synthesis_pipeline(self, src_path, dst_path, dst_corners, output_path, mode):
        src = self._cv_imread(src_path)
        dst = self._cv_imread(dst_path)
        if src is None or dst is None: return False

        # 自动旋转与补白逻辑简化版
        (tl, tr, br, bl) = dst_corners
        dst_w = max(int(np.linalg.norm(br-bl)), int(np.linalg.norm(tr-tl)))
        dst_h = max(int(np.linalg.norm(tr-br)), int(np.linalg.norm(tl-bl)))
        h_src, w_src = src.shape[:2]
        if (w_src > h_src) != (dst_w > dst_h): src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)
        
        # 透视变换
        h_s, w_s = src.shape[:2]
        src_pts = np.array([[0,0], [w_s-1,0], [w_s-1,h_s-1], [0,h_s-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(src_pts, dst_corners)
        warped = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))
        
        mask = np.zeros(dst.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, dst_corners.astype(int), 255)
        
        # 简单色彩融合
        try:
            center = (int(np.mean(dst_corners[:,0])), int(np.mean(dst_corners[:,1])))
            final = cv2.seamlessClone(warped, dst, mask, center, cv2.NORMAL_CLONE)
        except:
            final = dst.copy()
            final[mask>0] = warped[mask>0]
            
        return self._cv_imwrite(output_path, final)

    # --- 执行逻辑 ---

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 1. 获取输入
            input_path = str(sample.get('export_path')) + "/images"
            output_dir = Path(input_path)
            if not input_path or not os.path.exists(input_path):
                return sample
            
            input_path = Path(input_path)
            src_files = list(input_path.glob("*.png"))

            bg_path = Path(self.bg_dir)
            all_bg_files = [f for f in bg_path.glob("*") if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            logger.info(f"bg files: {all_bg_files}")

            filtered_bg_files = []

            for bg_file in all_bg_files:
                bg_name = bg_file.name
                scene_mode = self._determine_scene_mode(bg_name)
                if scene_mode in self.allowed_scenes:
                    filtered_bg_files.append(bg_file)

            use_random_selection = self.scenes is not None and self.scenes < len(filtered_bg_files)

            for i, src_file in enumerate(src_files, 1):
                src_name = src_file.stem
                logger.info(f"\n[处理源图 {i}/{len(src_files)}] {src_file.name}")

                # 如果启用随机选择，从背景图中随机选择指定数量
                if use_random_selection:
                    selected_bg_files = random.sample(filtered_bg_files, self.scenes)
                    logger.info(f"  随机选择了 {len(selected_bg_files)} 个场景")
                else:
                    selected_bg_files = filtered_bg_files

                for bg_file in selected_bg_files:
                    bg_name = bg_file.stem

                    # 确定场景模式
                    scene_mode = self._determine_scene_mode(bg_file.name)

                    # 输出文件名：源图名_背景图名.jpg
                    output_filename = f"{src_name}_{bg_name}.jpg"
                    output_path = output_dir / output_filename

                    logger.info(f"  -> 背景图: {bg_file.name} ({scene_mode})")

                    # 检测或加载坐标
                    if self.skip_detect:
                        corners = self._load_cached_coordinates(bg_file.name)
                        if corners is None:
                            logger.info(f"    跳过：无缓存坐标")
                            continue
                    else:
                        corners = self._detect_document_corners(str(bg_file))
                        if corners is None:
                            logger.info(f"    跳过：无法检测到文档区域")
                            # 保存到缓存以便下次手动标注
                            continue

                        # 保存检测到的坐标到缓存
                        self._save_cached_coordinates(str(bg_file), corners)

                    # 执行合成
                    if self._base_synthesis_pipeline(str(src_file), str(bg_file), corners, str(output_path), scene_mode):
                        logger.info(f"    成功: {output_filename}")
                    else:
                        logger.error(f"    失败: {output_filename}")

        except Exception as e:
            logger.error(f"Error in ImgAugOperator: {e}")
            
        return sample