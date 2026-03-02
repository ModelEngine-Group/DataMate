# -*- coding: utf-8 -*-
"""
WSIEnhance WSI 智能增强分析算子
支持组织检测、伪影识别、质量评估和 Patch 提取
"""

from typing import Dict, Any, List, Tuple
import os
import json
import numpy as np

from datamate.core.base_op import Mapper


class WSIEnhanceMapper(Mapper):
    """
    WSI 智能增强分析算子

    功能：
    1. WSI 读取：支持多种 WSI 格式（.svs/.tif/.ndpi 等）
    2. 组织检测：基于 HSV 颜色空间的智能分割
    3. 笔迹检测：识别记号笔笔迹、墨水痕迹
    4. 伪影检测：识别染色异常、折叠、空白裂隙
    5. 气泡检测：可选的气泡区域识别
    6. Patch 提取：批量提取高质量组织 Patch
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子参数
        """
        super().__init__(*args, **kwargs)

        # 从 kwargs 获取前端配置参数
        self.save_patches = kwargs.get('save_patches', False)
        self.save_patch_positions = kwargs.get('save_patch_positions', True)
        self.enable_bubble = kwargs.get('enable_bubble', False)
        self.enable_artifact = kwargs.get('enable_artifact', True)

        # 折叠处理策略
        treat_folding = kwargs.get('treat_folding_as_tissue', 'tissue')
        self.treat_folding_as_tissue = (treat_folding == 'tissue')

        # 数值参数
        self.patch_size = int(kwargs.get('patch_size', 256))
        self.patch_bg_thresh = int(kwargs.get('patch_bg_thresh', 210))
        self.patch_max_bg_ratio = float(kwargs.get('patch_max_bg_ratio', 0.85))
        self.thumbnail_size = int(kwargs.get('thumbnail_size', 3072))
        self.sat_thresh = int(kwargs.get('sat_thresh', 8))
        self.val_max = int(kwargs.get('val_max', 225))
        self.tissue_min_area = int(kwargs.get('tissue_min_area', 1000))

        # 延迟初始化组件
        self._initialized = False

    def _init_components(self):
        """
        延迟初始化所有组件
        """
        if self._initialized:
            return

        try:
            # 导入本地模块
            from wsi_reader.wsi_reader import WSIReader
            from wsi_processor.wsi_processor import WSIProcessor, ProcessorConfig

            self._WSIReader = WSIReader
            self._WSIProcessor = WSIProcessor
            self._ProcessorConfig = ProcessorConfig

            self._initialized = True

        except ImportError as e:
            raise RuntimeError(f"导入组件失败：{e}")
        except Exception as e:
            raise RuntimeError(f"初始化组件失败：{e}")

    def _contours_to_list(self, contours) -> List[List[List[int]]]:
        """
        将 OpenCV 轮廓转换为 JSON 可序列化的列表格式
        """
        out = []
        for c in contours:
            pts = c.squeeze(axis=1) if getattr(c, "ndim", 0) == 3 else c
            out.append([[int(x), int(y)] for x, y in pts])
        return out

    def _keep_patch(self, patch_rgb: np.ndarray) -> bool:
        """
        Patch 质量过滤：白背景比例过高的 patch 直接丢弃
        """
        try:
            import cv2
        except ImportError:
            return True

        if patch_rgb is None or patch_rgb.size == 0:
            return False

        gray = cv2.cvtColor(patch_rgb, cv2.COLOR_RGB2GRAY)
        bg_mask = gray > self.patch_bg_thresh
        bg_ratio = float(bg_mask.mean())
        return bg_ratio <= self.patch_max_bg_ratio

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑

        :param sample: 输入的数据样本，包含 image_path 或 image 字段
        :return: 处理后的数据样本，包含检测结果、轮廓坐标、Patch 信息等
        """
        # 确保 sourceFileSize 字段存在（平台框架必需，不能为 None）
        if 'sourceFileSize' not in sample or sample.get('sourceFileSize') is None:
            sample['sourceFileSize'] = 0

        try:
            # 初始化组件
            self._init_components()

            # 获取输入 WSI 文件路径
            wsi_path = sample.get('image_path', '')
            if not wsi_path or not os.path.exists(wsi_path):
                sample['wsienhance_error'] = f'WSI 文件不存在：{wsi_path}'
                # 尝试获取文件大小
                try:
                    if wsi_path and os.path.exists(wsi_path):
                        sample['sourceFileSize'] = os.path.getsize(wsi_path)
                except Exception:
                    pass
                return sample

            # 创建输出目录
            slide_name = os.path.splitext(os.path.basename(wsi_path))[0]
            out_dir = os.path.join(os.path.dirname(wsi_path), "wsienhance_results", slide_name)
            os.makedirs(out_dir, exist_ok=True)

            # 初始化 Processor 配置
            proc_cfg = self._ProcessorConfig(
                sat_thresh=self.sat_thresh,
                val_max=self.val_max,
                tissue_min_area=self.tissue_min_area,
                enable_bubble=self.enable_bubble,
                enable_artifact=self.enable_artifact,
                treat_folding_as_tissue=self.treat_folding_as_tissue,
            )

            # 处理 WSI
            result = {"wsi_path": wsi_path}

            with self._WSIReader(wsi_path) as reader:
                wsi_w, wsi_h = reader.width, reader.height
                result["wsi_size"] = {"w": wsi_w, "h": wsi_h}

                # 1. 生成缩略图
                thumb = reader.get_thumbnail((self.thumbnail_size, self.thumbnail_size))
                thumb_path = os.path.join(out_dir, "thumbnail.png")

                # 保存缩略图
                import cv2
                os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(thumb_path, bgr)
                result["thumbnail"] = {
                    "path": thumb_path,
                    "w": int(thumb.shape[1]),
                    "h": int(thumb.shape[0])
                }

                # 2. 执行检测
                processor = self._WSIProcessor(proc_cfg)
                det = processor.detect(thumb)

                # 3. 整理轮廓坐标
                result["coords_thumbnail"] = {
                    "tissue_contours": self._contours_to_list(det.contours["tissue"]),
                    "note_contours": self._contours_to_list(det.contours["note"]),
                    "artifact_contours": self._contours_to_list(det.contours.get("artifact", [])),
                    "bubble_contours": self._contours_to_list(det.contours.get("bubble", [])),
                }

                # 4. 统计信息
                result["statistics"] = {
                    "tissue_contour_count": len(det.contours["tissue"]),
                    "note_contour_count": len(det.contours["note"]),
                    "artifact_contour_count": len(det.contours.get("artifact", [])),
                    "bubble_contour_count": len(det.contours.get("bubble", [])),
                    "tissue_area_pixels": int(np.sum(det.tissue_mask > 0)),
                    "tissue_ratio": float(np.sum(det.tissue_mask > 0) / det.tissue_mask.size),
                }

                # 5. Patch 提取（可选）
                if self.save_patches or self.save_patch_positions:
                    tissue_for_patches = cv2.bitwise_and(
                        det.tissue_mask,
                        cv2.bitwise_not(det.note_mask)
                    )
                    tissue_for_patches = cv2.bitwise_and(
                        tissue_for_patches,
                        cv2.bitwise_not(det.artifact_mask)
                    )

                    # 计算 patch 坐标
                    patch_coords = self._mask_to_patch_coords(
                        tissue_for_patches, wsi_w, wsi_h, self.patch_size
                    )
                    result["patch_candidates"] = len(patch_coords)

                    positions_to_export: List[Tuple[int, int]] = []

                    if self.save_patches:
                        patch_dir = os.path.join(out_dir, "patches")
                        os.makedirs(patch_dir, exist_ok=True)
                        saved = 0

                        for idx, (x, y) in enumerate(patch_coords):
                            patch = reader.read_region(x, y, self.patch_size, self.patch_size, level=0)
                            if not self._keep_patch(patch):
                                continue

                            name = f"patch_{x}_{y}.png"
                            bgr_patch = cv2.cvtColor(patch, cv2.COLOR_RGB2BGR)
                            cv2.imwrite(os.path.join(patch_dir, name), bgr_patch)

                            if self.save_patch_positions:
                                positions_to_export.append((x, y))
                            saved += 1

                        result["patches"] = {
                            "count": saved,
                            "dir": patch_dir,
                            "patch_size": self.patch_size
                        }

                    elif self.save_patch_positions:
                        positions_to_export = patch_coords

                    if self.save_patch_positions:
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

                # 6. 保存叠加标注图
                overlay_path = os.path.join(out_dir, "thumbnail_overlay.png")
                overlay = thumb.copy()
                cv2.drawContours(overlay, det.contours["tissue"], -1, (0, 255, 0), 2)
                cv2.drawContours(overlay, det.contours["note"], -1, (255, 0, 0), 2)
                if det.contours.get("artifact"):
                    cv2.drawContours(overlay, det.contours["artifact"], -1, (0, 165, 255), 2)
                if det.contours.get("bubble"):
                    cv2.drawContours(overlay, det.contours["bubble"], -1, (0, 0, 255), 2)
                cv2.imwrite(overlay_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
                result["thumbnail_overlay"] = {"path": overlay_path}

            # 7. 保存结果 JSON
            json_path = os.path.join(out_dir, "results.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result["results_json"] = json_path

            # 获取文件大小并写入 sample（平台框架需要 sourceFileSize 字段）
            file_size = os.path.getsize(wsi_path)

            # 将关键结果写入 sample
            sample['wsienhance_result'] = result
            sample['wsienhance_output_dir'] = out_dir
            sample['sourceFileSize'] = file_size  # 平台框架必需字段
            sample['tissue_ratio'] = result["statistics"]["tissue_ratio"]
            sample['patch_count'] = result.get("patches", {}).get("count", 0) if self.save_patches else result.get("patch_candidates", 0)

            # 设置平台期望的输出字段
            # 1. 读取缩略图作为图像输出（RGB 格式）
            sample['image'] = cv2.cvtColor(cv2.imread(thumb_path), cv2.COLOR_BGR2RGB)
            sample['image_path'] = thumb_path
            sample['output_image_path'] = thumb_path

            # 2. 添加结果 JSON 路径
            sample['results_json_path'] = json_path

            # 3. 添加文本描述（用于平台显示）
            sample['text'] = f"WSI 分析完成：{slide_name}, 组织占比：{result['statistics']['tissue_ratio']:.2%}, Patch 数量：{sample['patch_count']}"

            # 4. 添加文件类型标识
            sample['file_type'] = 'png'
            sample['output_type'] = 'wsi_analysis'

            return sample

        except Exception as e:
            # 异常处理：避免单条数据异常导致整个任务崩溃
            import traceback
            sample['wsienhance_error'] = f"{str(e)}\n{traceback.format_exc()}"
            # 即使出错也要设置 sourceFileSize，防止平台框架报错
            try:
                if 'wsi_path' in sample and sample['wsi_path'] and os.path.exists(sample['wsi_path']):
                    sample['sourceFileSize'] = os.path.getsize(sample['wsi_path'])
                else:
                    sample['sourceFileSize'] = 0
            except Exception:
                sample['sourceFileSize'] = 0
            return sample

    def _mask_to_patch_coords(self, tissue_mask: np.ndarray, wsi_w: int, wsi_h: int,
                              patch_size: int) -> List[Tuple[int, int]]:
        """
        从 mask 计算 patch 中心坐标
        """
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
