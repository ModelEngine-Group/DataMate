"""
【算法层】WSIProcessor：只负责算图，不关心图从哪读。

输入：RGB 缩略图 (numpy array, HxWx3)
输出：
- tissue_mask / bubble_mask / note_mask / artifact_mask (uint8 0/255)
- 轮廓（用于可视化与导出坐标）

说明：
- tissue：HSV 饱和度/亮度阈值，形态学后得到组织区域。
- note(笔迹)：仅保留组织轮廓内的笔迹。
- artifact(伪影)：组织轮廓内与主色偏差过大的区域（LAB delta E），如红褐色染色异常。
- bubble：可选，简单气泡检测。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

try:
    import cv2
except Exception as e:  # pragma: no cover
    cv2 = None
    _CV2_IMPORT_ERR = e


@dataclass
class ProcessorConfig:
    # tissue（尽量包住整块组织，含淡染/脂肪/浅粉区）
    sat_thresh: int = 8           # 饱和度下限，更低以包含很淡的粉/近白区
    val_max: int = 225            # 亮度上限，更高以包含左侧/底部浅粉
    tissue_min_area: int = 3000   # 缩略图尺度下过滤碎片（像素数）
    tissue_close_kernel: int = 51 # 闭运算核，大核糊住脂肪、轮廓圆润少锯齿（可试 45–61）
    tissue_open_kernel: int = 3   # 开运算核，偏小以免咬掉细组织/连接
    tissue_fill_holes: bool = True
    tissue_merge_dilate: int = 17 # 合并邻近碎块：膨胀像素数，越大越易成整块
    tissue_final_close_kernel: int = 61  # 最终平滑轮廓用闭运算核（主要针对脂肪“海岸线”）
    # 浅灰/无色细长杂质过滤（划痕/纤维/盖玻片边缘）：亮但几乎无饱和度 → 当背景剔除
    tissue_gray_v_min: int = 200         # “很亮”的下限
    tissue_gray_s_max: int = 14          # “几乎无色”的上限（坏死浅粉通常 S 会更高）
    # 细长条伪组织（扫描划痕/纤维/碎屑）过滤：防止背景细线被当组织
    tissue_remove_line_artifacts: bool = True
    tissue_line_max_thickness: int = 40     # 连通域短边<=该值视为“细”
    tissue_line_min_aspect: float = 5.0     # 长宽比>=该值视为“长条”
    tissue_line_max_area: int = 1500000     # 面积过大不按长条删除，避免误删真正长条组织
    tissue_line_open_kernel: int = 31       # 用于分离“细长残差”的开运算核（越大越能抹掉细线）

    # note/pen mark
    note_val_max: int = 30  # 黑色阈值：更严格，避免误杀深紫色细胞核
    note_sat_max: int = 80  # 可适当限制饱和度，避免把深色组织当笔迹
    note_val_strict: int = 20  # 极暗像素（例如角落黑块）无视饱和度直接判为笔迹/伪影
    note_dark_val_max: int = 58  # 组织内仅“很暗”的像素才强制为笔迹
    note_dark_sat_max: int = 45  # 组织内“黑/灰笔迹”通常低饱和；深紫组织饱和度高，避免误标
    note_close_kernel: int = 5
    note_edge_exclusion: int = 11
    note_edge_overlap_ratio: float = 0.45
    note_edge_keep_min_aspect: float = 3.2
    note_edge_min_area: int = 35
    note_min_area: int = 25     # 笔迹连通域最小面积（像素），过滤细胞核大小的孤立点
    # 蓝墨水：HSV 色相 + 高饱和 + “蓝通道占优(B≫R,G)”联合判定，避免把深紫组织当笔迹
    ink_blue_h_min: int = 85
    ink_blue_h_max: int = 140
    ink_blue_s_min: int = 70
    ink_blue_v_max: int = 230
    ink_blue_b_over_r: int = 25  # B > R + delta
    ink_blue_b_over_g: int = 15  # B > G + delta
    ink_blue_expand_dilate: int = 5
    ink_blue_expand_h_min: int = 80
    ink_blue_expand_h_max: int = 150
    ink_blue_expand_s_min: int = 55
    ink_blue_expand_b_over_r: int = 16
    ink_blue_expand_b_over_g: int = 10
    ink_blue_grow_dilate: int = 5
    ink_blue_grow_h_min: int = 78
    ink_blue_grow_h_max: int = 155
    ink_blue_grow_s_min: int = 50
    ink_blue_grow_b_over_r: int = 14
    ink_blue_grow_b_over_g: int = 8
    ink_blue_grow_v_max: int = 230
    # 额外“墨迹样”检测：深色、饱和度高、呈细长条，且不在组织内
    ink_val_max: int = 120
    ink_sat_min: int = 80
    ink_min_area: int = 30
    ink_min_aspect: float = 4.0

    # “细脖子”切断（连接两块组织的浅色/脂肪带），默认偏保守避免把整块组织切碎
    neck_val_min: int = 200   # 脖子区域亮度下限（越大=只切非常亮的桥）
    neck_sat_max: int = 50    # 脖子区域饱和度上限（偏灰/白）
    neck_min_area: int = 400  # 脖子最小面积，偏大以免误切真实组织连接
    neck_max_thickness: int = 28  # 只切很细的桥（像素），避免切断脂肪等宽连接

    # 细桥断开（针对内部窄连接），核越小越保留连接、组织越完整
    bridge_kernel: int = 9    # odd，默认偏小以减少碎片化

    # bubble（默认开启一个很轻的检测，可按需关闭）
    enable_bubble: bool = False
    bubble_min_area: int = 200

    # 伪影：仅针对性检测，避免误杀正常深色/多色组织
    enable_artifact: bool = True
    artifact_lab_dev_thresh: float = 42.0   # 通用颜色偏差阈值，设高以免深紫/鲜红等正常组织被标成伪影
    artifact_min_area: int = 2000          # 最小连通面积，只标大面积空白/异常，避免坏死区等被标蓝
    artifact_open_kernel: int = 5          # 形态学开运算核，去毛刺
    artifact_bg_v_min: int = 235           # 伪影/空白：近纯白亮度下限（V 通道）
    artifact_bg_s_max: int = 12            # 伪影/空白：近纯白饱和度上限（S 通道，背景≈0）
    # 深紫/蓝紫高密度组织保护：即便很暗也应当算组织，绝不标为伪影
    artifact_purple_h_min: int = 115       # OpenCV H(0-180) 紫/蓝紫下限
    artifact_purple_h_max: int = 175       # OpenCV H(0-180) 紫/蓝紫上限
    artifact_purple_s_min: int = 20        # 至少有一定饱和度，避免把灰黑当紫
    artifact_purple_v_max: int = 120       # “很暗”的上限，主要保护深紫块
    # 组织折叠：黑红色细长“带子”；若算轮廓/面积则保留为组织（不标蓝），若切图训练可标蓝剔除
    enable_folding_artifact: bool = True   # 是否检测折叠
    treat_folding_as_tissue: bool = True   # True=折叠算绿（组织），False=折叠标蓝（剔除）
    folding_L_max: int = 70                # LAB L 上限，越暗越可能是折叠
    folding_a_min: int = 120               # LAB a 下限（OpenCV 中 128 为中性，>128 偏红），排除蓝紫
    folding_min_aspect: float = 2.5        # 长宽比下限，细长带状才当折叠
    folding_min_area: int = 400            # 折叠连通域最小面积

    global_stain_min_area: int = 120
    global_stain_dark_v_max: int = 60
    global_stain_dark_s_max: int = 95
    global_stain_dark_min_area: int = 18
    global_stain_dark_open_kernel: int = 3
    global_stain_dark_expand_dilate: int = 17
    global_stain_red_s_min: int = 165
    global_stain_red_v_max: int = 185
    global_stain_red_min_area: int = 60
    global_stain_red_r_over_g: int = 60
    global_stain_red_r_over_b: int = 50
    global_stain_red_expand_dilate: int = 5
    global_stain_red_expand_s_min: int = 135
    global_stain_red_expand_r_over_g: int = 42
    global_stain_red_expand_r_over_b: int = 34
    global_stain_green_h_min: int = 35
    global_stain_green_h_max: int = 95
    global_stain_green_s_min: int = 70
    global_stain_green_v_max: int = 245
    global_stain_green_min_area: int = 60
    global_stain_green_g_over_r: int = 22
    global_stain_green_g_over_b: int = 14
    global_stain_green_expand_dilate: int = 7
    global_stain_green_expand_h_min: int = 30
    global_stain_green_expand_h_max: int = 110
    global_stain_green_expand_s_min: int = 55
    global_stain_green_expand_g_over_r: int = 12
    global_stain_green_expand_g_over_b: int = 8
    global_stain_green_grow_dilate: int = 13
    global_stain_green_grow_h_min: int = 25
    global_stain_green_grow_h_max: int = 115
    global_stain_green_grow_s_min: int = 28
    global_stain_green_grow_g_over_r: int = 2
    global_stain_green_grow_g_over_b: int = -10
    global_stain_green_close_kernel: int = 9
    global_stain_compact_area_max: int = 300
    global_stain_compact_keep_min_aspect: float = 3.0
    global_stain_red_compact_area_max: int = 2600
    global_stain_red_compact_keep_min_aspect: float = 2.1
    global_stain_purple_tissue_area_max: int = 1600
    global_stain_purple_tissue_max_aspect: float = 2.25
    global_stain_purple_tissue_h_min: int = 120
    global_stain_purple_tissue_h_max: int = 145
    global_stain_purple_tissue_s_max: int = 90
    global_stain_purple_tissue_v_min: int = 95
    global_stain_purple_tissue_overlap_min: float = 0.6
    stain_internal_score_k: float = 1.9
    stain_internal_min_area: int = 180
    stain_internal_open_kernel: int = 0
    stain_internal_score_alpha: float = 0.95
    stain_internal_v_max: int = 135
    stain_internal_s_min: int = 30
    stain_internal_h_red_hmax: int = 10
    stain_internal_h_red_hmin: int = 160
    stain_internal_h_purple_min: int = 133
    stain_internal_h_purple_max: int = 170
    stain_tissue_edge_exclusion: int = 9
    tissue_score_he_weight: float = 0.72
    tissue_score_od_weight: float = 0.28
    tissue_score_blur_sigma: float = 4.0
    tissue_he_loose_percentile: float = 25.0
    tissue_he_loose_scale: float = 0.7
    tissue_he_min: float = 0.03
    stain_support_dilate: int = 25
    stain_residual_min: float = 0.055
    stain_residual_percentile: float = 84.0
    stain_ratio_min: float = 0.34
    stain_ratio_percentile: float = 78.0
    stain_candidate_sat_min: int = 32
    stain_candidate_dark_v_max: int = 95
    stain_texture_sigma: float = 3.0
    stain_keep_texture_max: float = 0.07
    stain_seed_keep_overlap: float = 0.12
    stain_note_keep_overlap: float = 0.04
    stain_residual_keep_overlap: float = 0.18
    stain_reject_texture_min: float = 0.052
    stain_edge_reject_overlap: float = 0.58
    stain_uniform_rgb_std_max: float = 30.0
    stain_min_aspect_or_smooth: float = 1.7
    stain_he_residual_reject_ratio: float = 3.2
    stain_residual_no_seed_scale: float = 1.08
    stain_ratio_no_seed_scale: float = 1.08
    stain_candidate_sat_no_seed_boost: int = 8
    stain_pen_fill_ratio_max: float = 0.60
    stain_pen_width_max: float = 26.0
    stain_pen_width_cv_max: float = 0.95
    stain_residual_blob_min_area: int = 220
    stain_he_retention_max: float = 0.62

    # morphology
    morph_kernel: int = 5


@dataclass
class DetectionResult:
    tissue_mask: np.ndarray
    bubble_mask: np.ndarray
    note_mask: np.ndarray
    artifact_mask: np.ndarray
    global_stain_mask: np.ndarray
    contours: Dict[str, List[np.ndarray]]  # keys: tissue/bubble/note/artifact/global_stain


class WSIProcessor:
    def __init__(self, config: ProcessorConfig | None = None):
        if cv2 is None:
            raise ImportError(
                "未安装 OpenCV(cv2)，无法运行算法层。\n"
                "请安装依赖：pip install opencv-python-headless\n"
                f"底层错误: {_CV2_IMPORT_ERR}"
            )
        self.cfg = config or ProcessorConfig()

    def _to_hsv(self, rgb: np.ndarray) -> np.ndarray:
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        return hsv

    @staticmethod
    def _odd(k: int) -> int:
        return k if (k % 2 == 1) else (k + 1)

    def _fill_holes(self, mask: np.ndarray) -> np.ndarray:
        """
        填充二值 mask 内部孔洞（mask: 0/255）。
        """
        if mask is None or mask.size == 0:
            return mask
        h, w = mask.shape[:2]
        flood = mask.copy()
        ff_mask = np.zeros((h + 2, w + 2), np.uint8)
        # 从左上角背景开始 flood fill 成 255
        cv2.floodFill(flood, ff_mask, (0, 0), 255)
        flood_inv = cv2.bitwise_not(flood)
        filled = cv2.bitwise_or(mask, flood_inv)
        return filled

    @staticmethod
    def _safe_percentile(values: np.ndarray, q: float, default: float) -> float:
        if values is None:
            return default
        arr = np.asarray(values)
        if arr.size == 0:
            return default
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return default
        return float(np.percentile(arr, q))

    def _normalize_feature(self, feature: np.ndarray, low_q: float, high_q: float) -> np.ndarray:
        low = self._safe_percentile(feature, low_q, 0.0)
        high = self._safe_percentile(feature, high_q, low + 1e-6)
        if high <= low + 1e-6:
            return np.zeros(feature.shape, dtype=np.uint8)
        scaled = (feature.astype(np.float32) - low) * (255.0 / (high - low))
        return np.clip(scaled, 0, 255).astype(np.uint8)

    def _rgb_to_od(self, rgb: np.ndarray) -> np.ndarray:
        rgb_f = np.clip(rgb.astype(np.float32), 1.0, 255.0) / 255.0
        return -np.log(rgb_f)

    def _compute_stain_features(self, thumbnail_rgb: np.ndarray) -> Dict[str, np.ndarray]:
        od = self._rgb_to_od(thumbnail_rgb)

        stain_matrix = np.array(
            [
                [0.650, 0.072, 0.268],
                [0.704, 0.990, 0.570],
                [0.286, 0.105, 0.776],
            ],
            dtype=np.float32,
        )
        stain_matrix /= np.linalg.norm(stain_matrix, axis=0, keepdims=True) + 1e-8

        od_flat = od.reshape(-1, 3)
        concentrations = np.maximum(0.0, od_flat @ np.linalg.pinv(stain_matrix.T))
        hema = concentrations[:, 0].reshape(od.shape[:2]).astype(np.float32)
        eosin = concentrations[:, 1].reshape(od.shape[:2]).astype(np.float32)
        he_sum = hema + eosin

        he_recon = concentrations[:, :2] @ stain_matrix[:, :2].T
        residual = np.linalg.norm(np.maximum(0.0, od_flat - he_recon), axis=1).reshape(od.shape[:2]).astype(
            np.float32
        )
        residual_ratio = residual / (he_sum + 0.03)

        gray = cv2.cvtColor(thumbnail_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        sigma = max(0.5, float(self.cfg.stain_texture_sigma))
        local_mean = cv2.GaussianBlur(gray, (0, 0), sigmaX=sigma, sigmaY=sigma)
        local_sq_mean = cv2.GaussianBlur(gray * gray, (0, 0), sigmaX=sigma, sigmaY=sigma)
        texture = np.sqrt(np.maximum(local_sq_mean - local_mean * local_mean, 0.0)).astype(np.float32)

        return {
            "od_sum": od.sum(axis=2).astype(np.float32),
            "hema": hema,
            "eosin": eosin,
            "he_sum": he_sum.astype(np.float32),
            "residual": residual,
            "residual_ratio": residual_ratio.astype(np.float32),
            "texture": texture,
        }

    def _detect_tissue(self, h: np.ndarray, s: np.ndarray, v: np.ndarray, note_raw: np.ndarray) -> np.ndarray:
        """
        组织识别：输出 tissue mask（0/255）。

        只依赖 HSV 与配置参数；不读取/输出轮廓。
        """
        tissue = ((s > self.cfg.sat_thresh) & (v < self.cfg.val_max)).astype(np.uint8) * 255

        # 先把“极暗伪影/笔迹”从 tissue 里剔除，避免角落黑块被当组织
        tissue = cv2.bitwise_and(tissue, cv2.bitwise_not(note_raw))

        # 亮且几乎无色的像素（浅灰杂质）直接从组织里剔除，避免后续闭运算把它“连成线”
        gray_junk = (v >= self.cfg.tissue_gray_v_min) & (s <= self.cfg.tissue_gray_s_max)
        if np.any(gray_junk):
            tissue[gray_junk] = 0

        # morphology: 先闭运算连通外轮廓/填缝，再开运算去掉细碎噪声
        close_k = self._odd(max(3, int(self.cfg.tissue_close_kernel)))
        open_k = self._odd(max(3, int(self.cfg.tissue_open_kernel)))
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_OPEN, open_kernel, iterations=1)

        # 填洞：让轮廓更像“组织外轮廓”，而不是组织内部碎片
        if self.cfg.tissue_fill_holes:
            tissue = self._fill_holes(tissue)

        # 连通域过滤：去掉非常碎的组织片段，保留较大组织区域
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # -----------------------------
        # 组织“细脖子”切断：避免两块组织通过浅色/脂肪区连成一大片
        # 仅切断“贴边的亮窄带”，不影响组织内部浅色区域
        # -----------------------------
        mh, mw = tissue.shape[:2]
        neck_seed = (
            (tissue > 0)
            & (v > self.cfg.neck_val_min)
            & (s < self.cfg.neck_sat_max)
        ).astype(np.uint8) * 255
        if np.any(neck_seed):
            neck_k = self._odd(15)
            neck_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (neck_k, neck_k))
            neck = cv2.morphologyEx(neck_seed, cv2.MORPH_OPEN, neck_kernel, iterations=1)
            neck = cv2.dilate(neck, neck_kernel, iterations=1)

            num_n, labels_n, stats_n, _ = cv2.connectedComponentsWithStats(neck, connectivity=8)
            for i in range(1, num_n):
                x, y, w, h2, area = stats_n[i]
                if area < self.cfg.neck_min_area:
                    continue
                short_side = max(1, min(w, h2))
                if short_side > self.cfg.neck_max_thickness:
                    continue
                touches_border = (
                    x <= 1 or y <= 1 or x + w >= mw - 2 or y + h2 >= mh - 2
                )
                if not touches_border:
                    continue
                tissue[labels_n == i] = 0

            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # 细桥断开（保守）
        bridge_k = self._odd(self.cfg.bridge_kernel)
        bridge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bridge_k, bridge_k))
        eroded = cv2.erode(tissue, bridge_kernel, iterations=1)
        tissue = cv2.dilate(eroded, bridge_kernel, iterations=1)
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # 膨胀合并邻近碎块
        if self.cfg.tissue_merge_dilate > 0:
            merge_k = self._odd(self.cfg.tissue_merge_dilate)
            merge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (merge_k, merge_k))
            tissue = cv2.dilate(tissue, merge_kernel, iterations=1)
            loose_sat = max(5, self.cfg.sat_thresh - 2)
            loose_val = min(235, self.cfg.val_max + 12)
            loose = ((s > loose_sat) & (v < loose_val)).astype(np.uint8) * 255
            loose = cv2.bitwise_and(loose, cv2.bitwise_not(note_raw))
            tissue = cv2.bitwise_and(tissue, loose)
            if self.cfg.tissue_fill_holes:
                tissue = self._fill_holes(tissue)
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # 最终平滑：用更大的闭运算把脂肪细小空隙“糊住”
        final_k = self._odd(max(3, int(self.cfg.tissue_final_close_kernel)))
        final_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (final_k, final_k))
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_CLOSE, final_kernel, iterations=1)
        if self.cfg.tissue_fill_holes:
            tissue = self._fill_holes(tissue)
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # 最终再剔除一次浅灰无色杂质（保险）
        if np.any(gray_junk):
            tissue[gray_junk] = 0
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        # 细长条伪组织过滤：去掉背景中的细长线状伪影
        if self.cfg.tissue_remove_line_artifacts and np.any(tissue > 0):
            # 先用一次较大的开运算得到“主体组织”，细线会被抹掉
            open_k = self._odd(max(3, int(self.cfg.tissue_line_open_kernel)))
            open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
            tissue_opened = cv2.morphologyEx(tissue, cv2.MORPH_OPEN, open_kernel, iterations=1)
            residual = cv2.bitwise_and(tissue, cv2.bitwise_not(tissue_opened))

            # 在残差里找细长条并删除（即使它和主体组织靠得很近，也更容易被分离出来）
            num_l, labels_l, stats_l, _ = cv2.connectedComponentsWithStats(residual, connectivity=8)
            for i in range(1, num_l):
                x, y, w, h2, area = stats_l[i]
                short_side = max(1, min(w, h2))
                long_side = max(w, h2)
                aspect = long_side / float(short_side)
                if (
                    short_side <= self.cfg.tissue_line_max_thickness
                    and aspect >= self.cfg.tissue_line_min_aspect
                    and area <= self.cfg.tissue_line_max_area
                ):
                    residual[labels_l == i] = 0

            tissue = cv2.bitwise_or(tissue_opened, residual)
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        return tissue

    def _mask_core(self, mask: np.ndarray, margin: int) -> np.ndarray:
        if mask is None or mask.size == 0 or margin <= 0:
            return mask
        k = self._odd(max(3, int(margin) * 2 + 1))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        return cv2.erode(mask, kernel, iterations=1)

    def _dilate_mask(self, mask: np.ndarray, size: int) -> np.ndarray:
        if mask is None or mask.size == 0 or size <= 0:
            return mask.copy() if mask is not None else mask
        k = self._odd(max(3, int(size)))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        return cv2.dilate(mask, kernel, iterations=1)

    def _limit_mask_to_core(self, mask: np.ndarray, base_mask: np.ndarray, margin: int) -> np.ndarray:
        if mask is None or mask.size == 0:
            return mask
        if base_mask is None or base_mask.size == 0 or margin <= 0:
            return mask
        core = self._mask_core(base_mask, margin)
        if core is None or not np.any(core > 0):
            return np.zeros_like(mask)
        return cv2.bitwise_and(mask, core)

    def _expand_color_mark(
        self,
        seed: np.ndarray,
        hue_ok: np.ndarray,
        sat_ok: np.ndarray,
        dominant_ok: np.ndarray,
        dilate_size: int,
        val_ok: np.ndarray | None = None,
    ) -> np.ndarray:
        if seed is None or seed.size == 0 or not np.any(seed > 0):
            return seed
        if dilate_size <= 1:
            return seed
        k = self._odd(max(3, int(dilate_size)))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        neighborhood = cv2.dilate(seed, kernel, iterations=1)
        expanded = hue_ok & sat_ok & dominant_ok & (neighborhood > 0)
        if val_ok is not None:
            expanded = expanded & val_ok
        return cv2.bitwise_or(seed, expanded.astype(np.uint8) * 255)

    def _suppress_edge_hugging_note(self, note: np.ndarray, tissue_mask: np.ndarray) -> np.ndarray:
        if note is None or note.size == 0 or not np.any(note > 0):
            return note
        margin = int(self.cfg.note_edge_exclusion)
        if tissue_mask is None or tissue_mask.size == 0 or margin <= 0:
            return note
        tissue_core = self._mask_core(tissue_mask, margin)
        if tissue_core is None or not np.any(tissue_core > 0):
            return note
        edge_band = cv2.bitwise_and(tissue_mask, cv2.bitwise_not(tissue_core))
        num, labels, stats, _ = cv2.connectedComponentsWithStats(note, connectivity=8)
        out = note.copy()
        for i in range(1, num):
            x, y, w, h2, area = stats[i]
            if area < int(self.cfg.note_edge_min_area):
                continue
            comp = labels == i
            edge_overlap = int(np.count_nonzero(comp & (edge_band > 0)))
            if edge_overlap <= 0:
                continue
            overlap_ratio = edge_overlap / float(max(1, area))
            short_side = max(1, min(w, h2))
            long_side = max(w, h2)
            aspect = long_side / float(short_side)
            if overlap_ratio >= float(self.cfg.note_edge_overlap_ratio) and aspect < float(
                self.cfg.note_edge_keep_min_aspect
            ):
                out[comp] = 0
        return out

    def _filter_small_compact_components(
        self,
        mask: np.ndarray,
        area_max: int,
        keep_min_aspect: float,
    ) -> np.ndarray:
        if mask is None or mask.size == 0 or not np.any(mask > 0):
            return mask
        if area_max <= 0:
            return mask
        num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        out = mask.copy()
        for i in range(1, num):
            x, y, w, h2, area = [int(v) for v in stats[i]]
            if area > int(area_max):
                continue
            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            if aspect < float(keep_min_aspect):
                out[labels == i] = 0
        return out

    def _filter_tissue_like_purple_components(
        self,
        mask: np.ndarray,
        tissue_mask: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
    ) -> np.ndarray:
        if mask is None or mask.size == 0 or not np.any(mask > 0):
            return mask
        area_max = int(self.cfg.global_stain_purple_tissue_area_max)
        if area_max <= 0:
            return mask

        tissue_bool = (tissue_mask > 0) if tissue_mask is not None and tissue_mask.size > 0 else None
        out = mask.copy()
        num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, num):
            x, y, w, h2, area = [int(vv) for vv in stats[i]]
            if area > area_max:
                continue

            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            if aspect > float(self.cfg.global_stain_purple_tissue_max_aspect):
                continue

            comp = labels == i
            if tissue_bool is not None:
                overlap = int(np.count_nonzero(comp & tissue_bool))
                overlap_ratio = overlap / float(max(1, area))
                if overlap_ratio < float(self.cfg.global_stain_purple_tissue_overlap_min):
                    continue

            mean_h = float(h[comp].mean())
            mean_s = float(s[comp].mean())
            mean_v = float(v[comp].mean())
            if (
                float(self.cfg.global_stain_purple_tissue_h_min) <= mean_h <= float(self.cfg.global_stain_purple_tissue_h_max)
                and mean_s <= float(self.cfg.global_stain_purple_tissue_s_max)
                and mean_v >= float(self.cfg.global_stain_purple_tissue_v_min)
            ):
                out[comp] = 0
        return out

    def _detect_note(
        self,
        thumbnail_rgb: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        tissue: np.ndarray,
        mask_inside_tissue: np.ndarray,
        note_raw: np.ndarray,
    ) -> np.ndarray:
        """
        笔迹识别：输出 note mask（0/255），只保留组织轮廓内部。
        """
        # 复用组织 open kernel（对笔迹去噪）
        open_k = self._odd(max(3, int(self.cfg.tissue_open_kernel)))
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))

        note = cv2.morphologyEx(note_raw, cv2.MORPH_OPEN, open_kernel, iterations=1)
        note = cv2.bitwise_and(note, mask_inside_tissue)

        # 蓝墨水：色相+饱和度+蓝通道占优，整块填实
        r = thumbnail_rgb[:, :, 0].astype(np.int16)
        g = thumbnail_rgb[:, :, 1].astype(np.int16)
        b = thumbnail_rgb[:, :, 2].astype(np.int16)
        blue_dominant = (b > r + self.cfg.ink_blue_b_over_r) & (b > g + self.cfg.ink_blue_b_over_g)
        blue_ink = (
            (h >= self.cfg.ink_blue_h_min)
            & (h <= self.cfg.ink_blue_h_max)
            & (s >= self.cfg.ink_blue_s_min)
            & (v <= self.cfg.ink_blue_v_max)
            & blue_dominant
            & (mask_inside_tissue > 0)
        ).astype(np.uint8) * 255
        note = cv2.bitwise_or(note, blue_ink)

        if np.any(blue_ink > 0):
            blue_soft = self._expand_color_mark(
                blue_ink,
                (h >= self.cfg.ink_blue_expand_h_min) & (h <= self.cfg.ink_blue_expand_h_max),
                s >= self.cfg.ink_blue_expand_s_min,
                (b > r + self.cfg.ink_blue_expand_b_over_r)
                & (b > g + self.cfg.ink_blue_expand_b_over_g),
                self.cfg.ink_blue_expand_dilate,
            )
            note = cv2.bitwise_or(note, blue_soft)
            blue_grow = self._expand_color_mark(
                blue_soft,
                (h >= self.cfg.ink_blue_grow_h_min) & (h <= self.cfg.ink_blue_grow_h_max),
                s >= self.cfg.ink_blue_grow_s_min,
                (b >= r + self.cfg.ink_blue_grow_b_over_r)
                & (b >= g + self.cfg.ink_blue_grow_b_over_g),
                self.cfg.ink_blue_grow_dilate,
                v <= self.cfg.ink_blue_grow_v_max,
            )
            note = cv2.bitwise_or(note, blue_grow)

        # 墨迹样：深色、高饱和、细长；只保留在组织轮廓内
        ink = (
            (v < self.cfg.ink_val_max)
            & (s > self.cfg.ink_sat_min)
            & (tissue == 0)
        ).astype(np.uint8) * 255
        ink = cv2.bitwise_and(ink, mask_inside_tissue)
        num_ink, labels_ink, stats_ink, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
        for i in range(1, num_ink):
            x, y, w, h2, area = stats_ink[i]
            if area < self.cfg.ink_min_area:
                continue
            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            if aspect < self.cfg.ink_min_aspect:
                continue
            note[labels_ink == i] = 255

        # 黑/灰笔迹兜底：很暗 + 低饱和
        dark_inside_note = (
            (v < self.cfg.note_dark_val_max)
            & (s <= self.cfg.note_dark_sat_max)
            & (mask_inside_tissue > 0)
        )
        note = cv2.bitwise_or(note, (dark_inside_note.astype(np.uint8) * 255))

        # 过滤细胞核大小的孤立笔迹点
        very_dark_inside = (
            (v < 35)
            & (s <= min(80, self.cfg.note_dark_sat_max + 20))
            & (mask_inside_tissue > 0)
        ).astype(np.uint8) * 255
        very_dark_inside = cv2.morphologyEx(very_dark_inside, cv2.MORPH_OPEN, open_kernel, iterations=1)
        very_dark_inside = self._filter_small_components(very_dark_inside, max(40, self.cfg.note_min_area))
        note = cv2.bitwise_or(note, very_dark_inside)

        dark_ink_candidate = (
            (v > 35)
            & (v < 70)
            & (s < 55)
            & (mask_inside_tissue > 0)
        ).astype(np.uint8) * 255
        dark_ink_candidate = cv2.morphologyEx(dark_ink_candidate, cv2.MORPH_OPEN, open_kernel, iterations=1)
        num_dark, labels_dark, stats_dark, _ = cv2.connectedComponentsWithStats(
            dark_ink_candidate, connectivity=8
        )
        for i in range(1, num_dark):
            x, y, w, h2, area = stats_dark[i]
            if area < 70:
                continue
            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            if aspect >= 2.6:
                note[labels_dark == i] = 255

        close_k = self._odd(max(3, int(self.cfg.note_close_kernel)))
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
        note = cv2.morphologyEx(note, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        note = cv2.bitwise_and(note, mask_inside_tissue)
        note = self._suppress_edge_hugging_note(note, tissue)
        note = self._filter_small_components(note, self.cfg.note_min_area)
        return note

    def _detect_artifact(
        self,
        thumbnail_rgb: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        mask_inside_tissue: np.ndarray,
        note: np.ndarray,
    ) -> np.ndarray:
        """
        伪影识别：输出 artifact mask（0/255）。

        当前策略：只在组织轮廓内识别“近纯白空洞/裂隙”(背景)；可选折叠剔除；
        并做深紫高密度组织保护与笔迹优先级。
        """
        artifact = np.zeros_like(mask_inside_tissue)
        if not (self.cfg.enable_artifact and np.any(mask_inside_tissue > 0)):
            return artifact

        bg_candidate = (
            (mask_inside_tissue > 0)
            & (v >= self.cfg.artifact_bg_v_min)
            & (s <= self.cfg.artifact_bg_s_max)
        ).astype(np.uint8) * 255
        art_open_k = self._odd(max(3, self.cfg.artifact_open_kernel))
        art_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (art_open_k, art_open_k))
        artifact = cv2.morphologyEx(bg_candidate, cv2.MORPH_OPEN, art_kernel, iterations=1)
        artifact = self._filter_small_components(artifact, self.cfg.artifact_min_area)

        # 折叠：可选剔除
        if self.cfg.enable_folding_artifact and not self.cfg.treat_folding_as_tissue:
            bgr = cv2.cvtColor(thumbnail_rgb, cv2.COLOR_RGB2BGR)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, _b_ch = cv2.split(lab)
            folding_candidate = (
                (mask_inside_tissue > 0)
                & (l_ch < self.cfg.folding_L_max)
                & (a_ch.astype(np.int32) > self.cfg.folding_a_min)
            ).astype(np.uint8) * 255
            num_f, labels_f, stats_f, _ = cv2.connectedComponentsWithStats(
                folding_candidate, connectivity=8
            )
            for i in range(1, num_f):
                x, y, w, h2, area = stats_f[i]
                if area < self.cfg.folding_min_area:
                    continue
                long_side = max(w, h2)
                short_side = max(1, min(w, h2))
                if long_side / short_side < self.cfg.folding_min_aspect:
                    continue
                artifact[labels_f == i] = 255

        # 深紫/蓝紫高密度组织保护：绝不标为伪影
        purple_dense = (
            (mask_inside_tissue > 0)
            & (h >= self.cfg.artifact_purple_h_min)
            & (h <= self.cfg.artifact_purple_h_max)
            & (s >= self.cfg.artifact_purple_s_min)
            & (v <= self.cfg.artifact_purple_v_max)
        ).astype(np.uint8) * 255
        artifact = cv2.bitwise_and(artifact, cv2.bitwise_not(purple_dense))

        # 笔迹优先：已判为 Note 的不再标为 Artifact
        artifact = cv2.bitwise_and(artifact, cv2.bitwise_not(note))
        return artifact

    def _detect_stain_internal_stats(
        self,
        tissue_mask: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
    ) -> np.ndarray:
        if tissue_mask is None or tissue_mask.size == 0:
            return np.zeros_like(tissue_mask)

        hue_red = (h <= self.cfg.stain_internal_h_red_hmax) | (h >= self.cfg.stain_internal_h_red_hmin)
        hue_purple = (h >= self.cfg.stain_internal_h_purple_min) & (h <= self.cfg.stain_internal_h_purple_max)
        hue_keep = hue_red | hue_purple

        tissue_bin = (tissue_mask > 0).astype(np.uint8)
        tissue_core = self._mask_core(tissue_bin * 255, self.cfg.stain_tissue_edge_exclusion)
        tissue_core_bool = tissue_core > 0 if tissue_core is not None else tissue_bin > 0
        num, labels, stats, _ = cv2.connectedComponentsWithStats(tissue_bin, connectivity=8)
        if num <= 1:
            return np.zeros_like(tissue_mask)

        s_norm = s.astype(np.float32) / 255.0
        v_norm = v.astype(np.float32) / 255.0
        alpha = float(self.cfg.stain_internal_score_alpha)
        score = alpha * s_norm + (1.0 - alpha) * (1.0 - v_norm)

        out = np.zeros_like(tissue_mask)
        k = float(self.cfg.stain_internal_score_k)
        for i in range(1, num):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area < max(1, int(self.cfg.stain_internal_min_area)):
                continue
            comp = labels == i
            if self.cfg.stain_tissue_edge_exclusion > 0:
                comp = comp & tissue_core_bool
            if not np.any(comp):
                continue

            comp_scores = score[comp]
            thr = float(np.mean(comp_scores)) + k * float(np.std(comp_scores))
            comp_stain = (
                comp
                & hue_keep
                & (score >= thr)
                & (v <= self.cfg.stain_internal_v_max)
                & (s >= self.cfg.stain_internal_s_min)
            )
            out[comp_stain] = 255

        if self.cfg.stain_internal_open_kernel > 0 and np.any(out > 0):
            k2 = self._odd(max(3, int(self.cfg.stain_internal_open_kernel)))
            kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k2, k2))
            out = cv2.morphologyEx(out, cv2.MORPH_OPEN, kern, iterations=1)

        return self._filter_small_components(out, int(self.cfg.stain_internal_min_area))

    def _detect_global_stain(
        self,
        thumbnail_rgb: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        note_raw: np.ndarray,
        tissue_mask: np.ndarray,
        note: np.ndarray,
    ) -> np.ndarray:
        close_k = self._odd(max(3, int(self.cfg.note_close_kernel)))
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))

        _ = note_raw
        global_stain = note.copy()

        ink_global = ((v < self.cfg.ink_val_max) & (s > self.cfg.ink_sat_min)).astype(np.uint8) * 255
        num_ink, labels_ink, stats_ink, _ = cv2.connectedComponentsWithStats(ink_global, connectivity=8)
        for i in range(1, num_ink):
            x, y, w, h2, area = stats_ink[i]
            if area < self.cfg.ink_min_area:
                continue
            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            if aspect < self.cfg.ink_min_aspect:
                continue
            global_stain[labels_ink == i] = 255

        r = thumbnail_rgb[:, :, 0].astype(np.int16)
        g = thumbnail_rgb[:, :, 1].astype(np.int16)
        b = thumbnail_rgb[:, :, 2].astype(np.int16)

        blue_seed = (
            (h >= self.cfg.ink_blue_h_min)
            & (h <= self.cfg.ink_blue_h_max)
            & (s >= self.cfg.ink_blue_s_min)
            & (v <= self.cfg.ink_blue_v_max)
            & (b > r + self.cfg.ink_blue_b_over_r)
            & (b > g + self.cfg.ink_blue_b_over_g)
        ).astype(np.uint8) * 255
        if np.any(blue_seed > 0):
            blue_soft = self._expand_color_mark(
                blue_seed,
                (h >= self.cfg.ink_blue_expand_h_min) & (h <= self.cfg.ink_blue_expand_h_max),
                s >= self.cfg.ink_blue_expand_s_min,
                (b > r + self.cfg.ink_blue_expand_b_over_r)
                & (b > g + self.cfg.ink_blue_expand_b_over_g),
                self.cfg.ink_blue_expand_dilate,
            )
            blue_grow = self._expand_color_mark(
                blue_soft,
                (h >= self.cfg.ink_blue_grow_h_min) & (h <= self.cfg.ink_blue_grow_h_max),
                s >= self.cfg.ink_blue_grow_s_min,
                (b >= r + self.cfg.ink_blue_grow_b_over_r)
                & (b >= g + self.cfg.ink_blue_grow_b_over_g),
                self.cfg.ink_blue_grow_dilate,
                v <= self.cfg.ink_blue_grow_v_max,
            )
            global_stain = cv2.bitwise_or(global_stain, blue_grow)

        green_seed = (
            (h >= self.cfg.global_stain_green_h_min)
            & (h <= self.cfg.global_stain_green_h_max)
            & (s >= self.cfg.global_stain_green_s_min)
            & (v <= self.cfg.global_stain_green_v_max)
            & (g >= r + self.cfg.global_stain_green_g_over_r)
            & (g >= b + self.cfg.global_stain_green_g_over_b)
        ).astype(np.uint8) * 255
        if np.any(green_seed > 0):
            green_seed = cv2.morphologyEx(green_seed, cv2.MORPH_CLOSE, close_kernel, iterations=1)
            green_soft = self._expand_color_mark(
                green_seed,
                (h >= self.cfg.global_stain_green_expand_h_min)
                & (h <= self.cfg.global_stain_green_expand_h_max),
                s >= self.cfg.global_stain_green_expand_s_min,
                (g >= r + self.cfg.global_stain_green_expand_g_over_r)
                & (g >= b + self.cfg.global_stain_green_expand_g_over_b),
                self.cfg.global_stain_green_expand_dilate,
            )
            green_soft = self._expand_color_mark(
                green_soft,
                (h >= self.cfg.global_stain_green_grow_h_min)
                & (h <= self.cfg.global_stain_green_grow_h_max),
                s >= self.cfg.global_stain_green_grow_s_min,
                (g >= r + self.cfg.global_stain_green_grow_g_over_r)
                & (g >= b + self.cfg.global_stain_green_grow_g_over_b),
                self.cfg.global_stain_green_grow_dilate,
            )
            green_close_k = self._odd(max(3, int(self.cfg.global_stain_green_close_kernel)))
            green_close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (green_close_k, green_close_k))
            green_soft = cv2.morphologyEx(green_soft, cv2.MORPH_CLOSE, green_close_kernel, iterations=1)
            green_soft = self._filter_small_components(green_soft, self.cfg.global_stain_green_min_area)
            global_stain = cv2.bitwise_or(global_stain, green_soft)

        red_seed = (
            ((h <= 10) | (h >= 160))
            & (s >= self.cfg.global_stain_red_s_min)
            & (v <= self.cfg.global_stain_red_v_max)
            & (r >= g + self.cfg.global_stain_red_r_over_g)
            & (r >= b + self.cfg.global_stain_red_r_over_b)
        ).astype(np.uint8) * 255
        if np.any(red_seed > 0):
            red_seed = cv2.morphologyEx(red_seed, cv2.MORPH_CLOSE, close_kernel, iterations=1)
            red_seed = self._expand_color_mark(
                red_seed,
                ((h <= 12) | (h >= 158)),
                s >= self.cfg.global_stain_red_expand_s_min,
                (r >= g + self.cfg.global_stain_red_expand_r_over_g)
                & (r >= b + self.cfg.global_stain_red_expand_r_over_b),
                self.cfg.global_stain_red_expand_dilate,
            )
            red_seed = self._filter_small_compact_components(
                red_seed,
                area_max=self.cfg.global_stain_red_compact_area_max,
                keep_min_aspect=self.cfg.global_stain_red_compact_keep_min_aspect,
            )
            red_seed = self._filter_small_components(red_seed, self.cfg.global_stain_red_min_area)
            global_stain = cv2.bitwise_or(global_stain, red_seed)

        dark_open_k = self._odd(max(3, int(self.cfg.global_stain_dark_open_kernel)))
        dark_open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dark_open_k, dark_open_k))
        if np.any(note > 0):
            dark_expand_k = self._odd(max(3, int(self.cfg.global_stain_dark_expand_dilate)))
            dark_expand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dark_expand_k, dark_expand_k))
            note_neighbor = cv2.dilate(note, dark_expand_kernel, iterations=1)
            dark_inside = (
                (v <= self.cfg.global_stain_dark_v_max)
                & (s <= self.cfg.global_stain_dark_s_max)
                & (tissue_mask > 0)
                & (note_neighbor > 0)
            ).astype(np.uint8) * 255
            dark_inside = cv2.morphologyEx(dark_inside, cv2.MORPH_CLOSE, dark_open_kernel, iterations=1)
            dark_inside = self._filter_small_components(dark_inside, self.cfg.global_stain_dark_min_area)
            global_stain = cv2.bitwise_or(global_stain, dark_inside)

        global_stain = cv2.bitwise_or(global_stain, note)

        global_stain = cv2.morphologyEx(global_stain, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        global_stain = self._filter_small_compact_components(
            global_stain,
            area_max=self.cfg.global_stain_compact_area_max,
            keep_min_aspect=self.cfg.global_stain_compact_keep_min_aspect,
        )
        global_stain = self._filter_tissue_like_purple_components(
            global_stain,
            tissue_mask=tissue_mask,
            h=h,
            s=s,
            v=v,
        )
        return self._filter_small_components(global_stain, self.cfg.global_stain_min_area)

    def _detect_tissue(
        self,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        note_raw: np.ndarray,
        he_sum: np.ndarray,
        od_sum: np.ndarray,
    ) -> np.ndarray:
        he_score = self._normalize_feature(he_sum, low_q=1.0, high_q=99.5)
        od_score = self._normalize_feature(od_sum, low_q=1.0, high_q=99.5)
        tissue_score = cv2.addWeighted(
            he_score,
            float(self.cfg.tissue_score_he_weight),
            od_score,
            float(self.cfg.tissue_score_od_weight),
            0.0,
        )
        blur_sigma = max(0.5, float(self.cfg.tissue_score_blur_sigma))
        tissue_score = cv2.GaussianBlur(tissue_score, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)
        _, tissue_seed = cv2.threshold(tissue_score, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        loose_sat = max(3, self.cfg.sat_thresh - 4)
        loose_val = min(245, self.cfg.val_max + 18)
        loose_hsv = (s > loose_sat) & (v < loose_val)
        foreground = tissue_seed > 0
        he_loose_thr = max(
            float(self.cfg.tissue_he_min),
            self._safe_percentile(
                he_sum[foreground],
                float(self.cfg.tissue_he_loose_percentile),
                float(self.cfg.tissue_he_min),
            )
            * float(self.cfg.tissue_he_loose_scale),
        )
        tissue = (foreground & (loose_hsv | (he_sum >= he_loose_thr))).astype(np.uint8) * 255
        tissue = cv2.bitwise_and(tissue, cv2.bitwise_not(note_raw))

        gray_junk = (v >= self.cfg.tissue_gray_v_min) & (s <= self.cfg.tissue_gray_s_max)
        if np.any(gray_junk):
            tissue[gray_junk] = 0

        close_k = self._odd(max(3, int(self.cfg.tissue_close_kernel)))
        open_k = self._odd(max(3, int(self.cfg.tissue_open_kernel)))
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_OPEN, open_kernel, iterations=1)

        if self.cfg.tissue_fill_holes:
            tissue = self._fill_holes(tissue)
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        mh, mw = tissue.shape[:2]
        neck_seed = (
            (tissue > 0)
            & (v > self.cfg.neck_val_min)
            & (s < self.cfg.neck_sat_max)
        ).astype(np.uint8) * 255
        if np.any(neck_seed):
            neck_k = self._odd(15)
            neck_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (neck_k, neck_k))
            neck = cv2.morphologyEx(neck_seed, cv2.MORPH_OPEN, neck_kernel, iterations=1)
            neck = cv2.dilate(neck, neck_kernel, iterations=1)

            num_n, labels_n, stats_n, _ = cv2.connectedComponentsWithStats(neck, connectivity=8)
            for i in range(1, num_n):
                x, y, w, h2, area = [int(vv) for vv in stats_n[i]]
                if area < int(self.cfg.neck_min_area):
                    continue
                short_side = max(1, min(w, h2))
                if short_side > int(self.cfg.neck_max_thickness):
                    continue
                touches_border = x <= 1 or y <= 1 or x + w >= mw - 2 or y + h2 >= mh - 2
                if not touches_border:
                    continue
                tissue[labels_n == i] = 0

            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        bridge_k = self._odd(int(self.cfg.bridge_kernel))
        bridge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bridge_k, bridge_k))
        eroded = cv2.erode(tissue, bridge_kernel, iterations=1)
        tissue = cv2.dilate(eroded, bridge_kernel, iterations=1)
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        if self.cfg.tissue_merge_dilate > 0:
            merge_k = self._odd(int(self.cfg.tissue_merge_dilate))
            merge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (merge_k, merge_k))
            tissue = cv2.dilate(tissue, merge_kernel, iterations=1)
            loose = (loose_hsv | (he_sum >= max(float(self.cfg.tissue_he_min), he_loose_thr * 0.8))).astype(
                np.uint8
            ) * 255
            loose = cv2.bitwise_and(loose, cv2.bitwise_not(note_raw))
            tissue = cv2.bitwise_and(tissue, loose)
            if self.cfg.tissue_fill_holes:
                tissue = self._fill_holes(tissue)
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        final_k = self._odd(max(3, int(self.cfg.tissue_final_close_kernel)))
        final_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (final_k, final_k))
        tissue = cv2.morphologyEx(tissue, cv2.MORPH_CLOSE, final_kernel, iterations=1)
        if self.cfg.tissue_fill_holes:
            tissue = self._fill_holes(tissue)
        tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        if np.any(gray_junk):
            tissue[gray_junk] = 0
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        if self.cfg.tissue_remove_line_artifacts and np.any(tissue > 0):
            open_k = self._odd(max(3, int(self.cfg.tissue_line_open_kernel)))
            open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
            tissue_opened = cv2.morphologyEx(tissue, cv2.MORPH_OPEN, open_kernel, iterations=1)
            residual_mask = cv2.bitwise_and(tissue, cv2.bitwise_not(tissue_opened))

            num_l, labels_l, stats_l, _ = cv2.connectedComponentsWithStats(residual_mask, connectivity=8)
            for i in range(1, num_l):
                _, _, w, h2, area = [int(vv) for vv in stats_l[i]]
                short_side = max(1, min(w, h2))
                long_side = max(w, h2)
                aspect = long_side / float(short_side)
                if (
                    short_side <= int(self.cfg.tissue_line_max_thickness)
                    and aspect >= float(self.cfg.tissue_line_min_aspect)
                    and area <= int(self.cfg.tissue_line_max_area)
                ):
                    residual_mask[labels_l == i] = 0

            tissue = cv2.bitwise_or(tissue_opened, residual_mask)
            tissue = self._filter_small_components(tissue, self.cfg.tissue_min_area)

        return tissue

    def _component_width_stats(self, component_mask: np.ndarray) -> Tuple[float, float]:
        if component_mask is None or component_mask.size == 0 or not np.any(component_mask > 0):
            return 0.0, 1.0

        dist = cv2.distanceTransform(component_mask, cv2.DIST_L2, 5)
        widths = dist[component_mask > 0]
        widths = widths[widths > 0.5] * 2.0
        if widths.size == 0:
            return 0.0, 1.0

        mean_width = float(widths.mean())
        width_cv = float(widths.std() / max(mean_width, 1e-6))
        return mean_width, width_cv

    def _classify_stain_components(
        self,
        candidate: np.ndarray,
        thumbnail_rgb: np.ndarray,
        tissue_mask: np.ndarray,
        color_seed: np.ndarray,
        note_seed: np.ndarray,
        residual_seed: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        he_sum: np.ndarray,
        residual: np.ndarray,
        residual_ratio: np.ndarray,
        texture: np.ndarray,
        residual_thr: float,
        ratio_thr: float,
    ) -> np.ndarray:
        if candidate is None or candidate.size == 0 or not np.any(candidate > 0):
            return np.zeros_like(candidate)

        tissue_bool = tissue_mask > 0
        tissue_core = self._mask_core(tissue_mask, self.cfg.stain_tissue_edge_exclusion)
        if tissue_core is None or not np.any(tissue_core > 0):
            edge_band_bool = tissue_bool
        else:
            edge_band_bool = cv2.bitwise_and(tissue_mask, cv2.bitwise_not(tissue_core)) > 0

        color_seed_bool = color_seed > 0
        note_seed_bool = note_seed > 0
        residual_seed_bool = residual_seed > 0

        num, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, connectivity=8)
        out = np.zeros_like(candidate)
        for i in range(1, num):
            x, y, w, h2, area = [int(vv) for vv in stats[i]]
            if area <= 0:
                continue

            comp = labels == i
            overlap_tissue = int(np.count_nonzero(comp & tissue_bool)) / float(area)
            edge_overlap = int(np.count_nonzero(comp & edge_band_bool)) / float(area)
            color_overlap = int(np.count_nonzero(comp & color_seed_bool)) / float(area)
            note_overlap = int(np.count_nonzero(comp & note_seed_bool)) / float(area)
            residual_overlap = int(np.count_nonzero(comp & residual_seed_bool)) / float(area)

            mean_he = float(he_sum[comp].mean())
            mean_residual = float(residual[comp].mean())
            mean_ratio = float(residual_ratio[comp].mean())
            mean_texture = float(texture[comp].mean())
            mean_sat = float(s[comp].mean())
            mean_val = float(v[comp].mean())

            rgb_vals = thumbnail_rgb[comp].astype(np.float32)
            rgb_std = float(rgb_vals.std(axis=0).mean()) if rgb_vals.size > 0 else 0.0

            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            aspect = long_side / float(short_side)
            fill_ratio = area / float(max(1, w * h2))
            comp_crop = (labels[y : y + h2, x : x + w] == i).astype(np.uint8) * 255
            mean_width, width_cv = self._component_width_stats(comp_crop)
            he_retention = mean_he / max(mean_he + mean_residual, 1e-6)
            smooth = mean_texture <= float(self.cfg.stain_keep_texture_max)
            uniform = rgb_std <= float(self.cfg.stain_uniform_rgb_std_max)
            elongated = aspect >= float(self.cfg.stain_min_aspect_or_smooth)
            pen_like_geometry = (
                elongated
                and mean_width <= float(self.cfg.stain_pen_width_max)
                and width_cv <= float(self.cfg.stain_pen_width_cv_max)
            ) or (
                smooth
                and uniform
                and fill_ratio <= float(self.cfg.stain_pen_fill_ratio_max)
                and mean_width <= float(self.cfg.stain_pen_width_max) * 1.35
            )
            strong_seed = color_overlap >= float(self.cfg.stain_seed_keep_overlap)
            strong_note = note_overlap >= float(self.cfg.stain_note_keep_overlap)
            residual_only = not strong_seed and not strong_note
            strong_residual = (
                mean_residual >= max(float(self.cfg.stain_residual_min), residual_thr * 0.8)
                and mean_ratio >= max(float(self.cfg.stain_ratio_min), ratio_thr * 0.75)
                and mean_sat >= float(self.cfg.stain_candidate_sat_min)
                and mean_texture < float(self.cfg.stain_keep_texture_max) * 1.05
            )
            residual_dominant = (
                mean_ratio >= max(float(self.cfg.stain_ratio_min), ratio_thr * 0.9)
                and he_retention <= float(self.cfg.stain_he_retention_max)
            )

            tissue_like = (
                overlap_tissue >= 0.55
                and mean_he > max(mean_residual * float(self.cfg.stain_he_residual_reject_ratio), 0.12)
                and mean_texture >= max(0.035, float(self.cfg.stain_reject_texture_min) * 0.75)
                and not elongated
                and color_overlap < 0.20
                and note_overlap < 0.15
            )
            edge_blob = (
                edge_overlap >= float(self.cfg.stain_edge_reject_overlap)
                and aspect < 3.0
                and mean_texture >= max(0.035, float(self.cfg.stain_reject_texture_min) * 0.75)
                and note_overlap < 0.12
                and mean_residual < residual_thr * 1.35
            )
            tiny_unstable = (
                area < int(self.cfg.global_stain_min_area)
                and not strong_seed
                and not strong_note
                and residual_overlap < float(self.cfg.stain_residual_keep_overlap)
                and aspect < 2.0
            )
            residual_blob = (
                residual_only
                and area < max(
                    int(self.cfg.stain_residual_blob_min_area),
                    int(self.cfg.global_stain_min_area) * 2,
                )
                and not pen_like_geometry
                and he_retention > float(self.cfg.stain_he_retention_max) * 0.92
            )
            broad_tissue_blob = (
                overlap_tissue >= 0.65
                and fill_ratio >= 0.48
                and not elongated
                and he_retention > float(self.cfg.stain_he_retention_max)
                and mean_texture >= max(0.03, float(self.cfg.stain_reject_texture_min) * 0.7)
                and color_overlap < 0.25
                and note_overlap < 0.15
            )
            if tiny_unstable or tissue_like or edge_blob or residual_blob or broad_tissue_blob:
                continue

            keep = False
            if strong_seed and (smooth or uniform or pen_like_geometry):
                keep = True
            elif strong_note and (pen_like_geometry or smooth or mean_val <= float(self.cfg.note_dark_val_max)):
                keep = True
            elif strong_residual and residual_dominant and (
                pen_like_geometry or residual_overlap >= float(self.cfg.stain_residual_keep_overlap)
            ):
                keep = True
            elif (
                residual_only
                and residual_overlap >= float(self.cfg.stain_residual_keep_overlap)
                and mean_sat >= float(self.cfg.stain_candidate_sat_min)
                and residual_dominant
                and pen_like_geometry
            ):
                keep = True

            if keep:
                out[comp] = 255

        return out

    def _detect_global_stain(
        self,
        thumbnail_rgb: np.ndarray,
        h: np.ndarray,
        s: np.ndarray,
        v: np.ndarray,
        note_raw: np.ndarray,
        tissue_mask: np.ndarray,
        note: np.ndarray,
        he_sum: np.ndarray,
        residual: np.ndarray,
        residual_ratio: np.ndarray,
        texture: np.ndarray,
    ) -> np.ndarray:
        _ = note_raw
        close_k = self._odd(max(3, int(self.cfg.note_close_kernel)))
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
        support_mask = self._dilate_mask(tissue_mask, int(self.cfg.stain_support_dilate))
        if support_mask is None or support_mask.size == 0 or not np.any(support_mask > 0):
            return np.zeros_like(tissue_mask)

        r = thumbnail_rgb[:, :, 0].astype(np.int16)
        g = thumbnail_rgb[:, :, 1].astype(np.int16)
        b = thumbnail_rgb[:, :, 2].astype(np.int16)

        note_seed = np.zeros_like(tissue_mask)
        ink_global = ((v < self.cfg.ink_val_max) & (s > self.cfg.ink_sat_min)).astype(np.uint8) * 255
        num_ink, labels_ink, stats_ink, _ = cv2.connectedComponentsWithStats(ink_global, connectivity=8)
        for i in range(1, num_ink):
            _, _, w, h2, area = [int(vv) for vv in stats_ink[i]]
            if area < int(self.cfg.ink_min_area):
                continue
            long_side = max(w, h2)
            short_side = max(1, min(w, h2))
            if long_side / float(short_side) < float(self.cfg.ink_min_aspect):
                continue
            note_seed[labels_ink == i] = 255

        blue_seed = (
            (h >= self.cfg.ink_blue_h_min)
            & (h <= self.cfg.ink_blue_h_max)
            & (s >= self.cfg.ink_blue_s_min)
            & (v <= self.cfg.ink_blue_v_max)
            & (b > r + self.cfg.ink_blue_b_over_r)
            & (b > g + self.cfg.ink_blue_b_over_g)
        ).astype(np.uint8) * 255
        if np.any(blue_seed > 0):
            blue_seed = cv2.bitwise_and(blue_seed, support_mask)
            blue_soft = self._expand_color_mark(
                blue_seed,
                (h >= self.cfg.ink_blue_expand_h_min) & (h <= self.cfg.ink_blue_expand_h_max),
                s >= self.cfg.ink_blue_expand_s_min,
                (b > r + self.cfg.ink_blue_expand_b_over_r) & (b > g + self.cfg.ink_blue_expand_b_over_g),
                self.cfg.ink_blue_expand_dilate,
            )
            blue_seed = self._expand_color_mark(
                blue_soft,
                (h >= self.cfg.ink_blue_grow_h_min) & (h <= self.cfg.ink_blue_grow_h_max),
                s >= self.cfg.ink_blue_grow_s_min,
                (b >= r + self.cfg.ink_blue_grow_b_over_r) & (b >= g + self.cfg.ink_blue_grow_b_over_g),
                self.cfg.ink_blue_grow_dilate,
                v <= self.cfg.ink_blue_grow_v_max,
            )
        else:
            blue_seed = np.zeros_like(tissue_mask)

        green_seed = (
            (h >= self.cfg.global_stain_green_h_min)
            & (h <= self.cfg.global_stain_green_h_max)
            & (s >= self.cfg.global_stain_green_s_min)
            & (v <= self.cfg.global_stain_green_v_max)
            & (g >= r + self.cfg.global_stain_green_g_over_r)
            & (g >= b + self.cfg.global_stain_green_g_over_b)
        ).astype(np.uint8) * 255
        if np.any(green_seed > 0):
            green_seed = cv2.bitwise_and(green_seed, support_mask)
            green_seed = cv2.morphologyEx(green_seed, cv2.MORPH_CLOSE, close_kernel, iterations=1)
            green_seed = self._expand_color_mark(
                green_seed,
                (h >= self.cfg.global_stain_green_expand_h_min) & (h <= self.cfg.global_stain_green_expand_h_max),
                s >= self.cfg.global_stain_green_expand_s_min,
                (g >= r + self.cfg.global_stain_green_expand_g_over_r)
                & (g >= b + self.cfg.global_stain_green_expand_g_over_b),
                self.cfg.global_stain_green_expand_dilate,
            )
            green_seed = self._expand_color_mark(
                green_seed,
                (h >= self.cfg.global_stain_green_grow_h_min) & (h <= self.cfg.global_stain_green_grow_h_max),
                s >= self.cfg.global_stain_green_grow_s_min,
                (g >= r + self.cfg.global_stain_green_grow_g_over_r)
                & (g >= b + self.cfg.global_stain_green_grow_g_over_b),
                self.cfg.global_stain_green_grow_dilate,
            )
            green_close_k = self._odd(max(3, int(self.cfg.global_stain_green_close_kernel)))
            green_close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (green_close_k, green_close_k))
            green_seed = cv2.morphologyEx(green_seed, cv2.MORPH_CLOSE, green_close_kernel, iterations=1)
            green_seed = self._filter_small_components(green_seed, self.cfg.global_stain_green_min_area)
        else:
            green_seed = np.zeros_like(tissue_mask)

        red_seed = (
            ((h <= 10) | (h >= 160))
            & (s >= self.cfg.global_stain_red_s_min)
            & (v <= self.cfg.global_stain_red_v_max)
            & (r >= g + self.cfg.global_stain_red_r_over_g)
            & (r >= b + self.cfg.global_stain_red_r_over_b)
        ).astype(np.uint8) * 255
        if np.any(red_seed > 0):
            red_seed = cv2.bitwise_and(red_seed, support_mask)
            red_seed = cv2.morphologyEx(red_seed, cv2.MORPH_CLOSE, close_kernel, iterations=1)
            red_seed = self._expand_color_mark(
                red_seed,
                ((h <= 12) | (h >= 158)),
                s >= self.cfg.global_stain_red_expand_s_min,
                (r >= g + self.cfg.global_stain_red_expand_r_over_g) & (r >= b + self.cfg.global_stain_red_expand_r_over_b),
                self.cfg.global_stain_red_expand_dilate,
            )
            red_seed = self._filter_small_compact_components(
                red_seed,
                area_max=self.cfg.global_stain_red_compact_area_max,
                keep_min_aspect=self.cfg.global_stain_red_compact_keep_min_aspect,
            )
            red_seed = self._filter_small_components(red_seed, self.cfg.global_stain_red_min_area)
        else:
            red_seed = np.zeros_like(tissue_mask)

        color_seed = cv2.bitwise_or(blue_seed, green_seed)
        color_seed = cv2.bitwise_or(color_seed, red_seed)
        color_seed = cv2.bitwise_and(color_seed, support_mask)

        dark_inside = np.zeros_like(tissue_mask)
        dark_open_k = self._odd(max(3, int(self.cfg.global_stain_dark_open_kernel)))
        dark_open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dark_open_k, dark_open_k))
        if np.any(note > 0):
            dark_expand_k = self._odd(max(3, int(self.cfg.global_stain_dark_expand_dilate)))
            dark_expand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dark_expand_k, dark_expand_k))
            note_neighbor = cv2.dilate(note, dark_expand_kernel, iterations=1)
            dark_inside = (
                (v <= self.cfg.global_stain_dark_v_max)
                & (s <= self.cfg.global_stain_dark_s_max)
                & (tissue_mask > 0)
                & (note_neighbor > 0)
            ).astype(np.uint8) * 255
            dark_inside = cv2.morphologyEx(dark_inside, cv2.MORPH_CLOSE, dark_open_kernel, iterations=1)
            dark_inside = self._filter_small_components(dark_inside, self.cfg.global_stain_dark_min_area)

        note_seed = cv2.bitwise_or(note_seed, note)
        note_seed = cv2.bitwise_or(note_seed, dark_inside)
        note_seed = cv2.bitwise_and(note_seed, support_mask)

        seed_support = cv2.bitwise_or(color_seed, note_seed)
        has_anchor_seed = np.any(seed_support > 0)
        if has_anchor_seed:
            seed_support = self._dilate_mask(seed_support, max(int(self.cfg.stain_support_dilate), 31))
            residual_support_bool = seed_support > 0
        else:
            tissue_core = self._mask_core(tissue_mask, max(1, int(self.cfg.stain_tissue_edge_exclusion)))
            if tissue_core is not None and np.any(tissue_core > 0):
                residual_support_bool = tissue_core > 0
            else:
                residual_support_bool = tissue_mask > 0

        residual_scale = float(self.cfg.stain_residual_no_seed_scale) if not has_anchor_seed else 1.0
        ratio_scale = float(self.cfg.stain_ratio_no_seed_scale) if not has_anchor_seed else 1.0
        residual_thr = max(
            float(self.cfg.stain_residual_min),
            self._safe_percentile(
                residual[residual_support_bool],
                float(self.cfg.stain_residual_percentile),
                float(self.cfg.stain_residual_min),
            ),
        ) * residual_scale
        ratio_thr = max(
            float(self.cfg.stain_ratio_min),
            self._safe_percentile(
                residual_ratio[residual_support_bool],
                float(self.cfg.stain_ratio_percentile),
                float(self.cfg.stain_ratio_min),
            ),
        ) * ratio_scale
        sat_min = int(self.cfg.stain_candidate_sat_min)
        if not has_anchor_seed:
            sat_min = min(255, sat_min + int(self.cfg.stain_candidate_sat_no_seed_boost))
        texture_limit = float(self.cfg.stain_keep_texture_max) * (0.95 if has_anchor_seed else 0.82)
        residual_seed = (
            residual_support_bool
            & (residual >= residual_thr)
            & (residual_ratio >= ratio_thr)
            & ((s >= sat_min) | (v <= self.cfg.stain_candidate_dark_v_max))
            & (texture <= texture_limit)
        ).astype(np.uint8) * 255
        if np.any(residual_seed > 0):
            residual_seed = cv2.morphologyEx(residual_seed, cv2.MORPH_CLOSE, close_kernel, iterations=1)

        global_stain = cv2.bitwise_or(color_seed, note_seed)
        global_stain = cv2.bitwise_or(global_stain, residual_seed)
        global_stain = cv2.bitwise_and(global_stain, support_mask)
        global_stain = cv2.morphologyEx(global_stain, cv2.MORPH_CLOSE, close_kernel, iterations=1)

        global_stain = self._classify_stain_components(
            global_stain,
            thumbnail_rgb=thumbnail_rgb,
            tissue_mask=tissue_mask,
            color_seed=color_seed,
            note_seed=note_seed,
            residual_seed=residual_seed,
            s=s,
            v=v,
            he_sum=he_sum,
            residual=residual,
            residual_ratio=residual_ratio,
            texture=texture,
            residual_thr=residual_thr,
            ratio_thr=ratio_thr,
        )
        global_stain = cv2.morphologyEx(global_stain, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        global_stain = self._filter_small_compact_components(
            global_stain,
            area_max=self.cfg.global_stain_compact_area_max,
            keep_min_aspect=self.cfg.global_stain_compact_keep_min_aspect,
        )
        global_stain = self._filter_tissue_like_purple_components(
            global_stain,
            tissue_mask=tissue_mask,
            h=h,
            s=s,
            v=v,
        )
        return self._filter_small_components(global_stain, self.cfg.global_stain_min_area)

    def detect(self, thumbnail_rgb: np.ndarray) -> DetectionResult:
        if thumbnail_rgb is None or thumbnail_rgb.size == 0:
            raise ValueError("thumbnail_rgb 为空")
        if thumbnail_rgb.ndim != 3 or thumbnail_rgb.shape[2] != 3:
            raise ValueError(f"thumbnail_rgb 必须为 HxWx3 RGB，当前: {thumbnail_rgb.shape}")

        hsv = self._to_hsv(thumbnail_rgb)
        h, s, v = cv2.split(hsv)
        stain_features = self._compute_stain_features(thumbnail_rgb)

        # --- note mask (pen mark / 极暗伪影)，先做全图检测，后面会只保留轮廓内的 ---
        note_raw = (
            (v < self.cfg.note_val_max)
            & ((s < self.cfg.note_sat_max) | (v < self.cfg.note_val_strict))
        ).astype(np.uint8) * 255

        # --- tissue ---
        tissue = self._detect_tissue(
            h=h,
            s=s,
            v=v,
            note_raw=note_raw,
            he_sum=stain_features["he_sum"],
            od_sum=stain_features["od_sum"],
        )

        # 先得到组织轮廓，再在“轮廓内部”做笔迹识别，轮廓外的笔迹忽略
        tissue_contours = self._find_contours(tissue)
        mask_inside_tissue = np.zeros_like(tissue)
        if tissue_contours:
            cv2.drawContours(mask_inside_tissue, tissue_contours, -1, 255, thickness=cv2.FILLED)

        # --- note ---
        note = self._detect_note(
            thumbnail_rgb=thumbnail_rgb,
            h=h,
            s=s,
            v=v,
            tissue=tissue,
            mask_inside_tissue=mask_inside_tissue,
            note_raw=note_raw,
        )

        # --- artifact ---
        artifact = self._detect_artifact(
            thumbnail_rgb=thumbnail_rgb,
            h=h,
            s=s,
            v=v,
            mask_inside_tissue=mask_inside_tissue,
            note=note,
        )

        global_stain = self._detect_global_stain(
            thumbnail_rgb=thumbnail_rgb,
            h=h,
            s=s,
            v=v,
            note_raw=note_raw,
            tissue_mask=tissue,
            note=note,
            he_sum=stain_features["he_sum"],
            residual=stain_features["residual"],
            residual_ratio=stain_features["residual_ratio"],
            texture=stain_features["texture"],
        )

        # --- bubble mask (optional; 默认关闭避免误杀) ---
        bubble = np.zeros_like(tissue)
        if self.cfg.enable_bubble:
            # very lightweight heuristic: bright & low saturation small blobs
            bubble = ((s < 10) & (v > 230)).astype(np.uint8) * 255
            open_k = self._odd(max(3, int(self.cfg.tissue_open_kernel)))
            open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
            bubble = cv2.morphologyEx(bubble, cv2.MORPH_OPEN, open_kernel, iterations=1)
            bubble = self._filter_small_components(bubble, self.cfg.bubble_min_area)

        contours = {
            "tissue": tissue_contours,
            "note": self._find_contours(note),
            "artifact": self._find_contours(artifact),
            "bubble": self._find_contours(bubble) if self.cfg.enable_bubble else [],
            "global_stain": self._find_contours(global_stain),
        }

        return DetectionResult(
            tissue_mask=tissue,
            bubble_mask=bubble,
            note_mask=note,
            artifact_mask=artifact,
            global_stain_mask=global_stain,
            contours=contours,
        )

    def build_detection_from_external_masks(
        self,
        thumbnail_rgb: np.ndarray,
        tissue_mask: np.ndarray,
        note_mask: np.ndarray | None = None,
        global_stain_mask: np.ndarray | None = None,
    ) -> DetectionResult:
        if thumbnail_rgb is None or thumbnail_rgb.size == 0:
            raise ValueError("thumbnail_rgb 为空")
        if thumbnail_rgb.ndim != 3 or thumbnail_rgb.shape[2] != 3:
            raise ValueError(f"thumbnail_rgb 必须为 HxWx3 RGB，当前: {thumbnail_rgb.shape}")

        tissue = ((np.asarray(tissue_mask) > 0).astype(np.uint8) * 255)
        if tissue.shape[:2] != thumbnail_rgb.shape[:2]:
            raise ValueError(
                "tissue_mask shape must match thumbnail spatial shape, "
                f"got {tissue.shape[:2]} vs {thumbnail_rgb.shape[:2]}"
            )

        note_full = np.zeros_like(tissue)
        if note_mask is not None:
            note_full = ((np.asarray(note_mask) > 0).astype(np.uint8) * 255)
            if note_full.shape[:2] != thumbnail_rgb.shape[:2]:
                raise ValueError(
                    "note_mask shape must match thumbnail spatial shape, "
                    f"got {note_full.shape[:2]} vs {thumbnail_rgb.shape[:2]}"
                )

        global_stain = note_full.copy()
        if global_stain_mask is not None:
            global_stain = ((np.asarray(global_stain_mask) > 0).astype(np.uint8) * 255)
            if global_stain.shape[:2] != thumbnail_rgb.shape[:2]:
                raise ValueError(
                    "global_stain_mask shape must match thumbnail spatial shape, "
                    f"got {global_stain.shape[:2]} vs {thumbnail_rgb.shape[:2]}"
                )

        hsv = self._to_hsv(thumbnail_rgb)
        h, s, v = cv2.split(hsv)

        tissue_contours = self._find_contours(tissue)
        mask_inside_tissue = np.zeros_like(tissue)
        if tissue_contours:
            cv2.drawContours(mask_inside_tissue, tissue_contours, -1, 255, thickness=cv2.FILLED)

        note_inside_tissue = cv2.bitwise_and(note_full, mask_inside_tissue)
        artifact = self._detect_artifact(
            thumbnail_rgb=thumbnail_rgb,
            h=h,
            s=s,
            v=v,
            mask_inside_tissue=mask_inside_tissue,
            note=note_inside_tissue,
        )

        bubble = np.zeros_like(tissue)
        if self.cfg.enable_bubble:
            bubble = ((s < 10) & (v > 230)).astype(np.uint8) * 255
            open_k = self._odd(max(3, int(self.cfg.tissue_open_kernel)))
            open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
            bubble = cv2.morphologyEx(bubble, cv2.MORPH_OPEN, open_kernel, iterations=1)
            bubble = self._filter_small_components(bubble, self.cfg.bubble_min_area)

        contours = {
            "tissue": tissue_contours,
            "note": self._find_contours(note_inside_tissue),
            "artifact": self._find_contours(artifact),
            "bubble": self._find_contours(bubble) if self.cfg.enable_bubble else [],
            "global_stain": self._find_contours(global_stain),
        }

        return DetectionResult(
            tissue_mask=tissue,
            bubble_mask=bubble,
            note_mask=note_inside_tissue,
            artifact_mask=artifact,
            global_stain_mask=global_stain,
            contours=contours,
        )

    def _find_contours(self, mask: np.ndarray) -> List[np.ndarray]:
        if mask is None:
            return []
        # 使用 CHAIN_APPROX_NONE 保留所有边界点，使轮廓更加“贴边”和细致，
        # 代价是坐标点数量和 JSON 体积会略有增大。
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return cnts

    def _filter_small_components(self, mask: np.ndarray, min_area: int) -> np.ndarray:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        out = np.zeros_like(mask)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_area:
                out[labels == i] = 255
        return out

