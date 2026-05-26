# -*- coding: utf-8 -*-
"""
WSIEnhance 全幻灯片成像处理算子
支持 WSI 组织检测、patch 提取、数据增强、染色归一化
"""

from typing import Dict, Any, List, Tuple, Optional
import json
import os

from datamate.core.base_op import Mapper


class WSIEnhanceMapper(Mapper):
    """
    WSI 全幻灯片成像处理算子

    功能：
    1. 组织检测：基于 HSV 颜色空间的组织区域识别
    2. 笔迹/伪影检测：黑色/蓝色墨水笔迹、组织折叠、近纯白空洞识别
    3. Patch 提取：基于组织 mask 映射回原图坐标，自动过滤白背景 patch
    4. 数据增强：旋转、翻转、颜色抖动、噪声、模糊、弹性形变
    5. 染色归一化：Macenko/Reinhard/Vahadane 方法
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子参数
        """
        super().__init__(*args, **kwargs)

        # ===== 组织检测配置 =====
        self.sat_thresh = int(kwargs.get('sat_thresh', 8))
        self.val_max = int(kwargs.get('val_max', 225))
        self.tissue_min_area = int(kwargs.get('tissue_min_area', 1000))
        self.tissue_close_kernel = int(kwargs.get('tissue_close_kernel', 51))
        self.tissue_open_kernel = int(kwargs.get('tissue_open_kernel', 3))
        self.bridge_kernel = int(kwargs.get('bridge_kernel', 9))
        self.tissue_merge_dilate = int(kwargs.get('tissue_merge_dilate', 17))
        self.tissue_final_close_kernel = int(kwargs.get('tissue_final_close_kernel', 61))

        # ===== 笔迹检测配置 =====
        self.note_val_max = int(kwargs.get('note_val_max', 30))
        self.note_sat_max = int(kwargs.get('note_sat_max', 80))
        self.note_dark_val_max = int(kwargs.get('note_dark_val_max', 58))
        self.note_min_area = int(kwargs.get('note_min_area', 25))

        # ===== 伪影检测配置 =====
        self.enable_artifact = kwargs.get('enable_artifact', True)
        self.artifact_lab_dev_thresh = float(kwargs.get('artifact_lab_dev_thresh', 42.0))
        self.artifact_min_area = int(kwargs.get('artifact_min_area', 2000))
        self.artifact_bg_v_min = int(kwargs.get('artifact_bg_v_min', 235))
        self.artifact_bg_s_max = int(kwargs.get('artifact_bg_s_max', 12))
        self.enable_folding = kwargs.get('enable_folding', True)
        self.treat_folding_as_tissue = kwargs.get('treat_folding_as_tissue', True)
        self.folding_L_max = int(kwargs.get('folding_L_max', 70))
        self.folding_a_min = int(kwargs.get('folding_a_min', 120))

        # ===== Patch 提取配置 =====
        self.patch_size = int(kwargs.get('patch_size', 256))
        self.patch_bg_thresh = int(kwargs.get('patch_bg_thresh', 210))
        self.patch_max_bg_ratio = float(kwargs.get('patch_max_bg_ratio', 0.85))
        self.thumbnail_size = int(kwargs.get('thumbnail_size', 3072))

        # ===== 数据增强配置 =====
        self.augment = kwargs.get('augment', False)
        self.aug_factor = int(kwargs.get('aug_factor', 1))
        self.aug_rotate = kwargs.get('aug_rotate', True)
        self.aug_flip = kwargs.get('aug_flip', True)
        self.aug_color_jitter = kwargs.get('aug_color_jitter', True)
        self.aug_noise = kwargs.get('aug_noise', False)
        self.aug_blur = kwargs.get('aug_blur', False)
        self.aug_elastic = kwargs.get('aug_elastic', False)

        # ===== 染色归一化配置 =====
        self.stain_norm = kwargs.get('stain_norm', False)
        self.stain_method = kwargs.get('stain_method', 'macenko')
        self.stain_target = kwargs.get('stain_target', None)

        # 延迟初始化组件
        self._wsi_reader = None
        self._processor = None
        self._augmenter = None
        self._normalizer = None
        self._initialized = False

    def _init_components(self):
        """
        延迟初始化所有组件
        """
        if self._initialized:
            return

        try:
            # 导入 WSI 相关模块
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            project_root = os.path.dirname(parent_dir)
            wsi_enhance_dir = os.path.join(project_root, "WSIEnhance")

            # 添加 WSIEnhance 到路径
            import sys
            if wsi_enhance_dir not in sys.path:
                sys.path.insert(0, wsi_enhance_dir)

            from wsi_reader.wsi_reader import WSIReader
            from wsi_processor.wsi_processor import WSIProcessor, ProcessorConfig
            from augmentations.augmentations import Augmenter, AugmentationConfig
            from stain_normalization.stain_normalization import StainNormalizer, StainNormalizationConfig, StainMethod

            # 1. 初始化 Processor 配置
            proc_cfg = ProcessorConfig(
                sat_thresh=self.sat_thresh,
                val_max=self.val_max,
                note_val_max=self.note_val_max,
                note_sat_max=self.note_sat_max,
                note_dark_val_max=self.note_dark_val_max,
                note_min_area=self.note_min_area,
                tissue_min_area=self.tissue_min_area,
                tissue_close_kernel=self.tissue_close_kernel,
                tissue_open_kernel=self.tissue_open_kernel,
                bridge_kernel=self.bridge_kernel,
                tissue_merge_dilate=self.tissue_merge_dilate,
                tissue_final_close_kernel=self.tissue_final_close_kernel,
                enable_artifact=self.enable_artifact,
                artifact_lab_dev_thresh=self.artifact_lab_dev_thresh,
                artifact_min_area=self.artifact_min_area,
                artifact_bg_v_min=self.artifact_bg_v_min,
                artifact_bg_s_max=self.artifact_bg_s_max,
                enable_folding_artifact=self.enable_folding,
                treat_folding_as_tissue=self.treat_folding_as_tissue,
                folding_L_max=self.folding_L_max,
                folding_a_min=self.folding_a_min,
            )

            # 2. 初始化 WSIProcessor
            self._processor = WSIProcessor(proc_cfg)

            # 3. 初始化数据增强器（如果启用）
            if self.augment:
                aug_cfg = AugmentationConfig(
                    enable_rotate=self.aug_rotate,
                    enable_flip=self.aug_flip,
                    enable_color_jitter=self.aug_color_jitter,
                    enable_noise=self.aug_noise,
                    enable_blur=self.aug_blur,
                    enable_elastic=self.aug_elastic,
                )
                self._augmenter = Augmenter(aug_cfg)

            # 4. 初始化染色归一化器（如果启用）
            if self.stain_norm:
                stain_method = StainMethod.MACENKO if self.stain_method == "macenko" else \
                               StainMethod.REINHARD if self.stain_method == "reinhard" else \
                               StainMethod.VAHADANE
                stain_cfg = StainNormalizationConfig(method=stain_method)
                self._normalizer = StainNormalizer(stain_cfg)

                # 加载目标模板（如果指定）
                if self.stain_target and os.path.exists(self.stain_target):
                    try:
                        import cv2
                        target_img = cv2.imread(self.stain_target)
                        if target_img is not None:
                            target_img = cv2.cvtColor(target_img, cv2.COLOR_BGR2RGB)
                            self._normalizer.set_target_image(target_img)
                    except Exception as e:
                        pass  # 使用标准模板

            self._initialized = True

        except ImportError as e:
            raise RuntimeError(f"导入 WSI 组件失败：{e}")
        except Exception as e:
            raise RuntimeError(f"初始化 WSI 组件失败：{e}")

    def _contours_to_coords(self, contours) -> List[List[Tuple[int, int]]]:
        """将 OpenCV 轮廓转换为坐标列表"""
        out: List[List[Tuple[int, int]]] = []
        for c in contours:
            pts = c.squeeze(axis=1) if getattr(c, "ndim", 0) == 3 else c
            out.append([(int(x), int(y)) for x, y in pts])
        return out

    def _mask_to_patch_coords(
        self,
        tissue_mask: Any,
        wsi_w: int,
        wsi_h: int,
        patch_size: int
    ) -> List[Tuple[int, int]]:
        """将组织 mask 映射回原图坐标"""
        import numpy as np
        import cv2

        mh, mw = tissue_mask.shape[:2]
        scale_x = wsi_w / mw
        scale_y = wsi_h / mh
        coords: List[Tuple[int, int]] = []

        ys, xs = np.where(tissue_mask > 0)
        if len(xs) == 0:
            return coords

        x_min, x_max = xs.min(), xs.max()
        y_min, y_max = ys.min(), ys.max()

        x0 = int(x_min * scale_x)
        x1 = int((x_max + 1) * scale_x)
        y0 = int(y_min * scale_y)
        y1 = int((y_max + 1) * scale_y)

        step = patch_size
        for y in range(y0, y1, step):
            for x in range(x0, x1, step):
                cx = int((x + step / 2) / scale_x)
                cy = int((y + step / 2) / scale_y)
                if 0 <= cx < mw and 0 <= cy < mh and tissue_mask[cy, cx] > 0:
                    coords.append((x, y))

        return coords

    def _keep_patch(self, patch_rgb, exclude_folding: bool = False) -> bool:
        """
        Patch 质量过滤：计算近白背景比例
        """
        import cv2
        import numpy as np

        if patch_rgb is None or patch_rgb.size == 0:
            return False

        gray = cv2.cvtColor(patch_rgb, cv2.COLOR_RGB2GRAY)
        bg_mask = gray > self.patch_bg_thresh
        bg_ratio = float(bg_mask.mean())
        return bg_ratio <= self.patch_max_bg_ratio

    def _save_png(self, path: str, rgb) -> None:
        """保存 PNG 图像"""
        import cv2
        import numpy as np

        os.makedirs(os.path.dirname(path), exist_ok=True)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, bgr)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑

        :param sample: 输入的数据样本，包含 image_path 字段
        :return: 处理后的数据样本，包含缩略图、轮廓坐标、patch 信息等
        """
        import cv2
        import numpy as np

        if 'sourceFileSize' not in sample or sample.get('sourceFileSize') is None:
            sample['sourceFileSize'] = 0

        try:
            self._init_components()

            # 获取输入 WSI 路径
            image_path = sample.get('image_path', '')
            if not image_path or not os.path.exists(image_path):
                sample['wsi_processor_error'] = f'输入 WSI 文件不存在：{image_path}'
                sample['sourceFileSize'] = 0
                return sample

            # 记录文件大小
            sample['sourceFileSize'] = os.path.getsize(image_path)

            # 准备输出目录
            slide_name = os.path.splitext(os.path.basename(image_path))[0]
            out_dir = os.path.abspath(os.path.join(
                sample.get('output_dir', './results'),
                slide_name
            ))
            os.makedirs(out_dir, exist_ok=True)

            result = {"slide_path": image_path}

            # ========== Step 1: 打开 WSI 文件 ==========
            from wsi_reader.wsi_reader import WSIReader

            with WSIReader(image_path) as reader:
                wsi_w, wsi_h = reader.width, reader.height
                result["wsi_size"] = {"w": wsi_w, "h": wsi_h}

                # ========== Step 2: 生成缩略图 ==========
                thumbnail = reader.get_thumbnail((self.thumbnail_size, self.thumbnail_size))
                thumb_path = os.path.join(out_dir, "thumbnail.png")
                self._save_png(thumb_path, thumbnail)
                result["thumbnail"] = {
                    "path": thumb_path,
                    "w": int(thumbnail.shape[1]),
                    "h": int(thumbnail.shape[0])
                }

                # ========== Step 3: 组织/笔迹/伪影检测 ==========
                det = self._processor.detect(thumbnail)

                # 轮廓坐标（缩略图坐标系）
                result["coords_thumbnail"] = {
                    "tissue_contours": self._contours_to_coords(det.contours["tissue"]),
                    "note_contours": self._contours_to_coords(det.contours["note"]),
                    "artifact_contours": self._contours_to_coords(det.contours.get("artifact", [])),
                    "bubble_contours": self._contours_to_coords(det.contours.get("bubble", [])),
                }

                # ========== Step 4: 绘制叠加图 ==========
                overlay = thumbnail.copy()
                tissue_color = (0, 255, 0)      # 绿 - 组织
                note_color = (255, 0, 0)        # 红 - 笔迹
                artifact_color = (0, 165, 255)  # 橙 - 伪影
                bubble_color = (0, 0, 255)      # 蓝 - 气泡

                cv2.drawContours(overlay, det.contours["tissue"], -1, tissue_color, 2)
                cv2.drawContours(overlay, det.contours["note"], -1, note_color, 2)
                if det.contours.get("artifact"):
                    cv2.drawContours(overlay, det.contours["artifact"], -1, artifact_color, 2)
                if det.contours.get("bubble"):
                    cv2.drawContours(overlay, det.contours["bubble"], -1, bubble_color, 2)

                # 添加图例
                h, w = overlay.shape[:2]
                legend_lines = 2 + (1 if det.contours.get("artifact") else 0) + (1 if det.contours.get("bubble") else 0)
                legend_w, legend_h = 260, 20 + legend_lines * 24
                x0, y0 = w - legend_w - 10, 10
                x1, y1 = w - 10, 10 + legend_h

                legend_bg = overlay.copy()
                cv2.rectangle(legend_bg, (x0, y0), (x1, y1), (255, 255, 255), thickness=-1)
                cv2.addWeighted(legend_bg, 0.6, overlay, 0.4, 0, overlay)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1
                line_h = 24
                yy = y0 + 20

                def draw_legend_line(color_bgr, text):
                    nonlocal yy
                    cv2.line(overlay, (x0 + 10, yy), (x0 + 40, yy), color_bgr, 3)
                    cv2.putText(overlay, text, (x0 + 50, yy + 5), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
                    yy += line_h

                draw_legend_line(tissue_color, "Tissue")
                draw_legend_line(note_color, "Note")
                if det.contours.get("artifact"):
                    draw_legend_line(artifact_color, "Artifact")
                if det.contours.get("bubble"):
                    draw_legend_line(bubble_color, "Bubble")

                overlay_path = os.path.join(out_dir, "thumbnail_overlay.png")
                self._save_png(overlay_path, overlay)
                result["thumbnail_overlay"] = {"path": overlay_path}

                # ========== Step 5: 提取 patch ==========
                # 计算用于 patch 提取的组织 mask（排除笔迹和伪影）
                tissue_for_patches = cv2.bitwise_and(
                    det.tissue_mask,
                    cv2.bitwise_not(det.note_mask)
                )
                tissue_for_patches = cv2.bitwise_and(
                    tissue_for_patches,
                    cv2.bitwise_not(det.artifact_mask)
                )

                patch_coords = self._mask_to_patch_coords(
                    tissue_for_patches, wsi_w, wsi_h, self.patch_size
                )

                positions_to_export = []
                saved_count = 0
                aug_saved_count = 0

                if patch_coords:
                    patch_dir = os.path.join(out_dir, "patches")
                    os.makedirs(patch_dir, exist_ok=True)

                    for idx, (x, y) in enumerate(patch_coords, start=1):
                        # 读取 patch
                        patch = reader.read_region(x, y, self.patch_size, self.patch_size, level=0)

                        # 质量过滤
                        if not self._keep_patch(patch):
                            continue

                        # 染色归一化（如果启用）
                        if self._normalizer is not None:
                            patch = self._normalizer.normalize(patch)

                        # 保存原始 patch
                        name = f"patch_{x}_{y}.png"
                        patch_path = os.path.join(patch_dir, name)
                        self._save_png(patch_path, patch)
                        positions_to_export.append((x, y))
                        saved_count += 1

                        # 数据增强（如果启用）
                        if self._augmenter is not None and self.aug_factor > 0:
                            augmented_patches = self._augmenter.generate_augmented_batch(
                                patch, n=self.aug_factor
                            )
                            for aug_idx, aug_patch in enumerate(augmented_patches):
                                aug_name = f"patch_{x}_{y}_aug{aug_idx + 1}.png"
                                aug_path = os.path.join(patch_dir, aug_name)
                                self._save_png(aug_path, aug_patch)
                                aug_saved_count += 1

                    result["patches"] = {
                        "count": saved_count,
                        "augmented_count": aug_saved_count,
                        "total_count": saved_count + aug_saved_count,
                        "dir": patch_dir,
                        "augment_enabled": self.augment,
                        "aug_factor": self.aug_factor if self.augment else 0,
                    }
                    if self.stain_norm:
                        result["patches"]["stain_norm_enabled"] = True
                        result["patches"]["stain_method"] = self.stain_method

                    # 保存 patch 位置 JSON
                    patch_positions_path = os.path.join(out_dir, "patch_positions.json")
                    patch_positions_data = {
                        "wsi_size": {"w": wsi_w, "h": wsi_h},
                        "patch_size": self.patch_size,
                        "patch_count": len(positions_to_export),
                        "patches": [{"x": x, "y": y} for x, y in positions_to_export],
                    }
                    with open(patch_positions_path, "w", encoding="utf-8") as f:
                        json.dump(patch_positions_data, f, ensure_ascii=False, indent=2)
                    result["patch_positions_json"] = patch_positions_path

                # ========== Step 6: 保存结果 JSON ==========
                json_path = os.path.join(out_dir, "results.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                result["results_json"] = json_path

                # ========== Step 7: 填充输出字段 ==========
                sample['thumbnail_path'] = thumb_path
                sample['thumbnail_overlay_path'] = overlay_path
                sample['patch_positions_json'] = result.get('patch_positions_json', '')
                sample['patches_dir'] = result.get('patches', {}).get('dir', '')
                sample['patch_count'] = saved_count
                sample['augmented_count'] = aug_saved_count
                sample['wsi_size'] = result['wsi_size']
                sample['coords_thumbnail'] = result['coords_thumbnail']

                # 元数据
                sample['wsi_processor_metadata'] = {
                    'patch_size': self.patch_size,
                    'thumbnail_size': self.thumbnail_size,
                    'patch_bg_thresh': self.patch_bg_thresh,
                    'patch_max_bg_ratio': self.patch_max_bg_ratio,
                    'augment_enabled': self.augment,
                    'aug_factor': self.aug_factor if self.augment else 0,
                    'stain_norm_enabled': self.stain_norm,
                    'stain_method': self.stain_method if self.stain_norm else None,
                    'processor_config': {
                        'sat_thresh': self.sat_thresh,
                        'val_max': self.val_max,
                        'tissue_min_area': self.tissue_min_area,
                        'note_val_max': self.note_val_max,
                        'note_min_area': self.note_min_area,
                    }
                }

            return sample

        except Exception as e:
            sample['wsi_processor_error'] = str(e)
            sample['coords_thumbnail'] = {
                'tissue_contours': [],
                'note_contours': [],
                'artifact_contours': [],
                'bubble_contours': [],
            }
            sample['patch_count'] = 0
            sample['augmented_count'] = 0
            return sample
