"""
真实世界模拟算子
功能：将电子凭证图片合成到真实场景背景中
"""

import os
import json
import base64
import tempfile
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper


class RealWorldSimulatorHelper:
    """真实世界模拟辅助类"""

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        background_dir: str = "backgrounds",
    ):
        """
        初始化真实世界模拟器

        Args:
            source_dir: 源图片目录（电子凭证）
            background_dir: 背景图片目录
            output_dir: 输出目录
        """
        self.source_dir = source_dir
        self.background_dir = background_dir
        self.output_dir = output_dir

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"真实世界模拟器初始化完成，源目录: {source_dir}, 输出目录: {output_dir}")

    def _order_points(self, pts):
        """
        重排坐标点顺序：左上, 右上, 右下, 左下

        Args:
            pts: 坐标点数组

        Returns:
            重排后的坐标点
        """
        rect = [[0, 0], [0, 0], [0, 0], [0, 0]]

        # 坐标点求和
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # 坐标点差值 (y - x)
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _auto_rotate_to_match_orientation(self, src, dst_corners):
        """
        检查源图与目标区域的方向（横版/竖版）是否一致，如果不一致则自动旋转源图90度。

        Args:
            src: 源图
            dst_corners: 目标区域的四个顶点

        Returns:
            旋转后的源图
        """
        import numpy as np

        # 计算目标区域的大致宽高
        (tl, tr, br, bl) = dst_corners
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        dst_w = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - bl[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tr[1] - bl[1]) ** 2))
        dst_h = max(int(heightA), int(heightB))

        h_src, w_src = src.shape[:2]

        # 判断是否为横版 (Width > Height)
        src_is_landscape = w_src > h_src
        dst_is_landscape = dst_w > dst_h

        if src_is_landscape != dst_is_landscape:
            logger.info(f"方向不匹配 (Src横版={src_is_landscape}, Dst横版={dst_is_landscape})，执行旋转...")
            import cv2
            src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

        return src

    def _pad_src_to_match_ratio(self, src, dst_corners):
        """
        为了防止电子凭证被拉伸/挤压变形，需要先给源图补白边，
        使其宽高比与目标区域的透视宽高比大致一致。

        Args:
            src: 源图
            dst_corners: 目标区域的四个顶点

        Returns:
            补白边后的源图
        """
        import numpy as np

        # 计算目标区域目前的"物理"宽高近似值
        (tl, tr, br, bl) = dst_corners
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tr[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst_ratio = maxWidth / float(maxHeight)

        h_src, w_src = src.shape[:2]
        src_ratio = w_src / float(h_src)

        logger.info(f"比例校正 - Src比例: {src_ratio:.2f}, Dst区域比例: {dst_ratio:.2f}")

        # 如果比例差不多，就不动了
        if abs(src_ratio - dst_ratio) < 0.1:
            return src

        if src_ratio > dst_ratio:
            # 源图比目标更"扁/胖"，目标比较"瘦/高"
            # 这种情况下，源图需要上下补白，变高一点，才能塞进去不变形
            new_h = int(w_src / dst_ratio)
            total_pad = new_h - h_src
            pad_top = total_pad // 2
            pad_bot = total_pad - pad_top

            import cv2
            src_padded = cv2.copyMakeBorder(
                src, pad_top, pad_bot, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
            logger.info(f"比例校正 - 为源图上下补白: {total_pad}px")
            return src_padded
        else:
            # 源图比目标更"瘦/高"，目标比较"扁/胖"
            # 这种情况下，源图需要左右补白，变宽一点
            new_w = int(h_src * dst_ratio)
            total_pad = new_w - w_src
            pad_left = total_pad // 2
            pad_right = total_pad - pad_left

            import cv2
            src_padded = cv2.copyMakeBorder(
                src, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
            logger.info(f"比例校正 - 为源图左右补白: {total_pad}px")
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
    ):
        """
        基础合成流水线。

        Args:
            src_path: 图片1 (电子凭证)
            dst_path: 图片2 (实拍背景)
            dst_corners: 目标区域的四个顶点 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            output_path: 输出图片路径
            mode: 场景模式
            enable_ratio_fix: 是否启用比例校正
            enable_auto_rotate: 是否启用自动旋转
        """
        import cv2
        import numpy as np

        # 1. 读取图像
        src = cv2.imdecode(np.fromfile(src_path), cv2.IMREAD_COLOR)
        dst = cv2.imdecode(np.fromfile(dst_path), cv2.IMREAD_COLOR)

        if src is None or dst is None:
            logger.error(f"无法读取图片 - Src: {src_path}, Dst: {dst_path}")
            return

        # 2. 准备透视变换
        h_src, w_src = src.shape[:2]
        src_pts = np.array(
            [[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]],
            dtype="float32",
        )

        dst_pts = np.array(dst_corners, dtype="float32")

        # 3. 自动旋转校正方向
        if enable_auto_rotate:
            src = self._auto_rotate_to_match_orientation(src, dst_corners)

        # 4. 比例自适应校正
        if enable_ratio_fix:
            src = self._pad_src_to_match_ratio(src, dst_corners)

        # 5. 透视变换
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
            logger.warning("目标区域掩模为空")
            return

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

        # 8. 泊松融合
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

        # 9. 保存
        is_success, im_buf = cv2.imencode(".jpg", final_output)
        if is_success:
            im_buf.tofile(output_path)
            logger.info(f"成功！合成图已保存至: {output_path}")
        else:
            logger.error("保存失败")

    def process_normal_scene(self, src_path, dst_path, dst_corners, output_path):
        """场景：正常拍摄（正对或微倾斜，光照均匀）"""
        logger.info("[处理逻辑] 使用【正常场景】合成算法")
        self._base_synthesis_pipeline(
            src_path,
            dst_path,
            dst_corners,
            output_path,
            mode="normal",
            enable_ratio_fix=True,
            enable_auto_rotate=True,
        )

    def process_tilted_scene(self, src_path, dst_path, dst_corners, output_path):
        """场景：斜拍（透视变形较大）"""
        logger.info("[处理逻辑] 使用【斜拍场景】合成算法")
        self._base_synthesis_pipeline(
            src_path,
            dst_path,
            dst_corners,
            output_path,
            mode="tilted",
            enable_ratio_fix=True,
            enable_auto_rotate=True,
        )

    def process_shadow_scene(self, src_path, dst_path, dst_corners, output_path):
        """场景：有阴影（光照不均匀，有投影）"""
        logger.info("[处理逻辑] 使用【阴影场景】合成算法")
        self._base_synthesis_pipeline(
            src_path,
            dst_path,
            dst_corners,
            output_path,
            mode="shadow",
        )

    def process_watermark_scene(self, src_path, dst_path, dst_corners, output_path):
        """场景：有水印（桌面或背景有复杂纹理）"""
        logger.info("[处理逻辑] 使用【水印场景】合成算法")
        self._base_synthesis_pipeline(
            src_path,
            dst_path,
            dst_corners,
            output_path,
            mode="watermark",
            enable_ratio_fix=True,
            enable_auto_rotate=True,
        )

    def process_incomplete_scene(self, src_path, dst_path, dst_corners, output_path):
        """场景：拍摄不完整（凭证部分在画面外）"""
        logger.info("[处理逻辑] 使用【不完整场景】合成算法")
        self._base_synthesis_pipeline(
            src_path,
            dst_path,
            dst_corners,
            output_path,
            mode="incomplete",
            enable_ratio_fix=True,
            enable_auto_rotate=True,
        )

    def batch_simulate(self, source_files: List[str], bg_files: List[str]) -> List[str]:
        """
        批量进行真实世界模拟

        Args:
            source_files: 源图片文件列表
            bg_files: 背景图片文件列表

        Returns:
            生成的模拟图片路径列表
        """
        logger.info(f"开始批量模拟 - 源图片: {len(source_files)}, 背景图片: {len(bg_files)}")

        simulated_images = []

        for src_file in source_files:
            src_img_path = os.path.join(self.source_dir, src_file)
            src_base_name = os.path.splitext(src_file)[0]

            logger.info(f"处理源图片: {src_file}")

            # 遍历每张背景图片
            for bg_file in bg_files:
                dst_img_path = os.path.join(self.background_dir, bg_file)
                logger.info(f"使用背景图片: {bg_file}")
                logger.info(f"源图路径: {src_img_path}, 背景图路径: {self.background_dir}")
                bg_base_name = os.path.splitext(bg_file)[0]

                # 输出文件名格式: 源图名_背景图名.jpg
                output_img_path = os.path.join(
                    self.output_dir, f"{src_base_name}_{bg_base_name}.jpg"
                )

                # 根据文件名关键词，分发到不同的处理函数
                try:
                    if "3-" in bg_file or "斜拍" in bg_file:
                        self.process_tilted_scene(
                            src_img_path,
                            dst_img_path,
                            None,  # 自动检测
                            output_img_path,
                        )
                    elif "4-" in bg_file or "阴影" in bg_file:
                        self.process_shadow_scene(
                            src_img_path,
                            dst_img_path,
                            None,  # 自动检测
                            output_img_path,
                        )
                    elif "5-" in bg_file or "水印" in bg_file:
                        self.process_watermark_scene(
                            src_img_path,
                            dst_img_path,
                            None,  # 自动检测
                            output_img_path,
                        )
                    elif "6-" in bg_file or "不完整" in bg_file:
                        self.process_incomplete_scene(
                            src_img_path,
                            dst_img_path,
                            None,  # 自动检测
                            output_img_path,
                        )
                    else:
                        # 默认正常场景
                        self.process_normal_scene(
                            src_img_path,
                            dst_img_path,
                            None,  # 自动检测
                            output_img_path,
                        )
                    simulated_images.append(output_img_path)
                except Exception as e:
                    logger.error(f"处理 {src_file} -> {bg_file} 失败: {str(e)}")
                    continue

        logger.info(f"真实世界模拟完成，共生成 {len(simulated_images)} 张图片")
        return simulated_images


class RealWorldSimulator(Mapper):
    """
    真实世界模拟算子
    类名建议使用驼峰命名法定义，例如 RealWorldSimulator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从UI参数获取配置
        self.scene_mode = kwargs.get("sceneMode", "auto")
        self.enable_ratio_fix = kwargs.get("enableRatioFix", True)
        self.enable_auto_rotate = kwargs.get("enableAutoRotate", True)
        self.output_format = kwargs.get("outputFormat", "path")

        # 创建临时输出目录
        self.temp_output_dir = tempfile.mkdtemp(prefix="real_world_simulator_")

        self.simulator = None


    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """
        try:

            # 创建模拟器实例
            self.simulator = RealWorldSimulatorHelper(
                source_dir=sample["export_path"] + "/images",
                background_dir=os.path.join(os.path.dirname(__file__), "backgrounds"),
                output_dir=sample["export_path"] + "/images",
            )
            # 获取源图片目录
            source_dir = sample["export_path"] + "/images"

            # 获取背景图片目录
            background_dir = os.path.join(os.path.dirname(__file__), "backgrounds")

            # 检查源目录是否存在
            if not os.path.exists(source_dir):
                logger.warning(f"源图片目录不存在: {source_dir}")
                return sample

            # 检查背景目录是否存在
            if not os.path.exists(background_dir):
                logger.warning(f"背景图片目录不存在: {background_dir}")
                return sample

            # 获取源图片列表
            source_files = sample["generated_images"]
            logger.info(f"找到 {len(source_files)} 张源图片待处理")

            # 获取背景图片列表
            bg_files = [f for f in os.listdir(background_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            logger.info(f"找到 {len(bg_files)} 张背景图")
            # 批量模拟
            simulated_images = self.simulator.batch_simulate(source_files, bg_files)

            # 根据输出格式返回结果
            sample["generated_images"] = simulated_images
            logger.info(f"成功完成真实世界模拟，共{len(simulated_images)}张图片")
            return sample

        except Exception as e:
            logger.error(f"真实世界模拟时发生错误: {str(e)}")
            raise
