"""
真实世界模拟算子 - process.py
将电子凭证图片合成到真实场景中，模拟各种拍摄效果
"""

import os
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper


class PropertyRealWorldSimulatorMapper(Mapper):
    """
    真实世界模拟算子：RealWorldSimulatorMapper
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取算子参数
        self.skip_simulation = kwargs.get("skipSimulationParam", False)
        self.skip_detect = kwargs.get("skipDetectParam", True)

        # 背景图目录和坐标缓存文件路径
        self.bg_dir = None
        self.coord_cache_file = None

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

    def _cv_imread(self, file_path: str):
        """读取含中文路径的图片"""
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def _order_points(self, pts):
        """
        重排坐标点顺序：左上, 右上, 右下, 左下
        """
        rect = np.zeros((4, 2), dtype="float32")

        # 坐标点求和:
        # 左上角 sum 最小
        # 右下角 sum 最大
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # 坐标点差值 (y - x):
        # 右上角 diff 最小
        # 左下角 diff 最大
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _load_cached_coordinates(self, image_path: str):
        """尝试从JSON文件中加载缓存的坐标"""
        if not self.coord_cache_file or not os.path.exists(self.coord_cache_file):
            return None

        try:
            with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 统一使用正斜杠路径作为key
            key = os.path.basename(image_path)
            if key in data:
                logger.info(f"检测到缓存坐标，已从 {self.coord_cache_file} 加载。")
                return np.array(data[key], dtype="float32")
        except Exception as e:
            logger.warning(f"读取缓存文件失败: {e}")

        return None

    def _save_cached_coordinates(self, image_path: str, coords):
        """将坐标保存到JSON文件"""
        if not self.coord_cache_file:
            return

        data = {}
        # 如果文件存在，先读取原有数据
        if os.path.exists(self.coord_cache_file):
            try:
                with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass  # 如果文件损坏，就覆盖它

        # 转换 numpy 数组为 list 以便 JSON 序列化
        key = image_path.replace("\\", "/")
        data[key] = coords.tolist()

        try:
            with open(self.coord_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"已将坐标保存至 {self.coord_cache_file}，下次运行将自动加载。")
        except Exception as e:
            logger.warning(f"保存缓存文件失败: {e}")

    def _detect_document_corners(self, image_path: str):
        """
        智能识别方案：
        1. 优先检查本地 JSON 是否有缓存坐标
        2. 局部对比度增强 + 双边滤波 (针对同色系背景)
        3. Canny边缘检测
        4. 轮廓筛选 + 最小外接矩形
        """
        # 步骤 0: 检查缓存
        cached_pts = self._load_cached_coordinates(image_path)
        if cached_pts is not None:
            return self._order_points(cached_pts)

        image = self._cv_imread(image_path)
        if image is None:
            logger.warning(f"无法读取图片: {image_path}")
            return None

        # 1. 图像增强预处理
        ratio = image.shape[0] / 800.0
        orig = image.copy()
        processed_img = cv2.resize(image, (int(image.shape[1] / ratio), 800))

        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)

        # 双边滤波：能极好地去除桌面的纹理噪点，同时保留纸张边缘
        gray = cv2.bilateralFilter(gray, 11, 75, 75)

        # CLAHE：自适应直方图均衡化，增强局部对比度
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # 2. 边缘检测
        # 自动计算 Canny 阈值
        v = np.median(gray)
        sigma = 0.33
        lower_thresh = int(max(0, (1.0 - sigma) * v))
        upper_thresh = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(gray, lower_thresh, upper_thresh)

        # 膨胀处理，连接断开的边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edged = cv2.dilate(edged, kernel, iterations=1)

        # 3. 轮廓提取
        cnts, _ = cv2.findContours(
            edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        screenCnt = None

        logger.info("正在尝试自动识别...")
        for c in cnts:
            peri = cv2.arcLength(c, True)
            # 近似多边形
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            # 只要顶点数在4到6之间，且面积够大，就认为是候选纸张
            if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
                # 使用最小外接矩形来规整化（解决5、6个点的问题）
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                screenCnt = np.int64(box)
                logger.info(f"-> 锁定候选轮廓，面积: {cv2.contourArea(c)}")
                break

        # 4. 结果处理
        if screenCnt is not None:
            # 还原到原始尺寸
            detected_pts = (screenCnt * ratio).astype(np.float32)
            ordered_pts = self._order_points(detected_pts)
            return ordered_pts

        return None

    def _auto_rotate_to_match_orientation(self, src, dst_corners):
        """
        检查源图与目标区域的方向（横版/竖版）是否一致，如果不一致则自动旋转源图90度。
        """
        # 计算目标区域的大致宽高
        (tl, tr, br, bl) = dst_corners
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        dst_w = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        dst_h = max(int(heightA), int(heightB))

        h_src, w_src = src.shape[:2]

        # 判断是否为横版 (Width > Height)
        src_is_landscape = w_src > h_src
        dst_is_landscape = dst_w > dst_h

        if src_is_landscape != dst_is_landscape:
            logger.info(
                f"   [自动旋转] 方向不匹配 (Src横版={src_is_landscape}, Dst横版={dst_is_landscape})，执行旋转..."
            )
            src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

        return src

    def _pad_src_to_match_ratio(self, src, dst_corners):
        """
        为了防止电子凭证被拉伸/挤压变形，我们需要先给源图补白边(Padding)，
        使其宽高比(Aspect Ratio)与目标区域的透视宽高比大致一致。
        """
        # 1. 计算目标区域目前的"物理"宽高近似值
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

        logger.info(
            f"   [比例校正] Src比例: {src_ratio:.2f}, Dst区域比例: {dst_ratio:.2f}"
        )

        # 2. 根据比例差异进行填充
        pad_h, pad_w = 0, 0

        if abs(src_ratio - dst_ratio) < 0.1:
            # 如果比例差不多，就不动了
            return src

        if src_ratio > dst_ratio:
            # 源图比目标更"扁/胖"，目标比较"瘦/高"
            new_h = int(w_src / dst_ratio)
            total_pad = new_h - h_src
            pad_top = total_pad // 2
            pad_bot = total_pad - pad_top

            # 使用白色填充 (255, 255, 255)
            src_padded = cv2.copyMakeBorder(
                src, pad_top, pad_bot, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
            logger.info(f"   [比例校正] 为源图上下补白: {total_pad}px")
        else:
            # 源图比目标更"瘦/高"，目标比较"扁/胖"
            new_w = int(h_src * dst_ratio)
            total_pad = new_w - w_src
            pad_left = total_pad // 2
            pad_right = total_pad - pad_left

            src_padded = cv2.copyMakeBorder(
                src,
                0,
                0,
                pad_left,
                pad_right,
                cv2.BORDER_CONSTANT,
                value=(255, 255, 255),
            )
            logger.info(f"   [比例校正] 为源图左右补白: {total_pad}px")

        return src_padded

    def _base_synthesis_pipeline(
        self,
        src_path: str,
        dst_path: str,
        dst_corners,
        output_path: str,
        mode: str = "normal",
        enable_ratio_fix: bool = False,
        enable_auto_rotate: bool = False,
        enable_watermark: bool = False,
    ):
        """
        基础合成流水线
        """
        # 1. 读取图像
        src = self._cv_imread(src_path)
        dst = self._cv_imread(dst_path)
        if src is None or dst is None:
            logger.warning(f"错误：无法读取图片。\nSrc: {src_path}\nDst: {dst_path}")
            return False

        # [新增] 自动旋转校正方向
        if enable_auto_rotate:
            src = self._auto_rotate_to_match_orientation(src, dst_corners)

        # [新增] 比例自适应校正
        if enable_ratio_fix:
            src = self._pad_src_to_match_ratio(src, dst_corners)

        # 2. 准备透视变换
        h_src, w_src = src.shape[:2]
        src_pts = np.array(
            [[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]],
            dtype="float32",
        )
        dst_pts = np.array(dst_corners, dtype="float32")

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

        # 3. 创建掩模
        mask = np.zeros(dst.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

        # 4. 色彩空间匹配
        dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
        warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)

        dst_region_l = dst_lab[:, :, 0][mask > 0]
        if dst_region_l.size == 0:
            logger.warning("警告：目标区域掩模为空")
            return False

        l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
        src_region_l = warped_lab[:, :, 0][mask > 0]
        l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

        # 针对不同模式，微调光照参数
        contrast_factor = 1.0
        if mode == "shadow":
            contrast_factor = 0.85  # 阴影下对比度低一点可能更自然
        elif mode == "tilted":
            contrast_factor = 0.95

        l_channel = warped_lab[:, :, 0].astype(float)
        l_channel = (l_channel - l_mean_src) * (
            l_std_dst / (l_std_src + 1e-5)
        ) * contrast_factor + l_mean_dst
        warped_lab[:, :, 0] = np.clip(l_channel, 0, 255).astype(np.uint8)

        matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)

        # 5. 泊松融合
        center = (
            int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
            int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2),
        )

        clone_mode = cv2.NORMAL_CLONE

        try:
            final_output = cv2.seamlessClone(matched_src, dst, mask, center, clone_mode)
        except Exception as e:
            logger.warning(f"融合失败，降级为直接覆盖: {e}")
            final_output = dst.copy()
            final_output[mask > 0] = matched_src[mask > 0]

        # 6. 保存
        is_success, im_buf = cv2.imencode(".jpg", final_output)
        if is_success:
            im_buf.tofile(output_path)
            return True
        else:
            logger.warning("保存失败")
            return False

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        file_path = sample.get("filePath")
        if not file_path.endswith(".docx") or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            parent_path = Path(file_path).parent
            self.bg_dir = parent_path / "backgrounds"
            self.coord_cache_file = parent_path / "coordinates_cache.json"

            # 获取输入路径
            input_path = sample.get("export_path")
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input directory not found: {input_path}")
                return sample

            # 获取输出路径
            export_path = sample.get("export_path")
            if not export_path:
                export_path = input_path

            # 构建输入和输出目录
            input_dir = Path(input_path) / "stamped_images"
            output_dir = Path(input_path) / "simulated_images"
            output_dir.mkdir(parents=True, exist_ok=True)

            # 获取源图文件
            src_files = list(input_dir.glob("*.jpg"))
            if not src_files:
                logger.warning(f"No source images found in {input_dir}")
                return sample

            # 获取背景图文件
            bg_path = Path(self.bg_dir)
            all_bg_files = [
                f
                for f in bg_path.glob("*")
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
            ]

            # 过滤掉电子凭证和debug图片
            bg_files = [
                f
                for f in all_bg_files
                if "1-电子凭证" not in f.name and "debug" not in f.name
            ]

            if not bg_files:
                logger.warning(f"No background images found in {self.bg_dir}")
                return sample

            # 处理每张源图
            simulated_count = 0
            for i, src_file in enumerate(src_files, 1):
                src_name = src_file.stem
                logger.info(f"\n[处理源图 {i}/{len(src_files)}] {src_file.name}")

                # 对每个背景图进行合成
                for bg_file in bg_files:
                    bg_name = bg_file.stem
                    scene_mode = self._determine_scene_mode(bg_name)

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
                            continue

                        # 保存检测到的坐标到缓存
                        self._save_cached_coordinates(str(bg_file), corners)

                    # 根据场景模式选择处理方式
                    enable_ratio_fix = True
                    enable_auto_rotate = scene_mode in [
                        "tilted",
                        "shadow",
                        "watermark",
                        "incomplete",
                    ]
                    enable_watermark = scene_mode == "watermark"

                    # 执行合成
                    success = self._base_synthesis_pipeline(
                        src_path=str(src_file),
                        dst_path=str(bg_file),
                        dst_corners=corners,
                        output_path=str(output_path),
                        mode=scene_mode,
                        enable_ratio_fix=enable_ratio_fix,
                        enable_auto_rotate=enable_auto_rotate,
                        enable_watermark=enable_watermark,
                    )

                    if success:
                        logger.info(f"    成功: {output_filename}")
                        simulated_count += 1
                    else:
                        logger.warning(f"    失败: {output_filename}")

            logger.info(
                f"\n[步骤5-真实模拟] 真实世界模拟完成，共生成 {simulated_count} 张图片"
            )

        except Exception as e:
            logger.error(f"Error in RealWorldSimulatorMapper: {e}")
            import traceback

            traceback.print_exc()

        return sample
