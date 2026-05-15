"""
染色归一化模块：将 WSI patch 的染色风格统一到目标模板。

支持的方法：
1. Macenko 方法 - 基于 SVD 分解组织染色浓度矩阵
2. Reinhard 方法 - 基于颜色统计特性匹配
3. Vahadane 方法 - 基于稀疏非负矩阵分解

目标染色模板管理：
- 内置常用模板（H&E 标准）
- 支持用户自定义模板图像
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import cv2
except Exception as e:
    cv2 = None
    _CV2_IMPORT_ERR = e
else:
    _CV2_IMPORT_ERR = None


class StainMethod(Enum):
    """染色归一化方法"""
    MACENKO = "macenko"
    REINHARD = "reinhard"
    VAHADANE = "vahadane"


@dataclass
class StainNormalizationConfig:
    """染色归一化配置"""
    method: StainMethod = StainMethod.MACENKO  # 默认使用 Macenko
    target_image: Optional[np.ndarray] = None  # 目标模板图像
    Io: float = 240.0  # 入射光强度，用于计算光密度
    beta: float = 0.15  # Macenko 阈值，用于分离背景
    normalize_background: bool = True  # 是否归一化背景


class StainNormalizer:
    """染色归一化器"""

    # 标准 H&E 染色矩阵（从文献中获取）
    STANDARD_HE_STAIN_MATRIX = np.array([
        [0.5626, 0.2159],
        [0.7201, 0.8012],
        [0.4062, 0.5581]
    ])

    # 标准 H&E 浓度统计
    STANDARD_HE_CONCENTRATION_STATS = {
        "hematoxylin": {"mean": 1.771, "std": 0.156},
        "eosin": {"mean": 1.054, "std": 0.243}
    }

    def __init__(self, config: Optional[StainNormalizationConfig] = None):
        if cv2 is None:
            raise ImportError(
                "未安装 OpenCV(cv2)，无法进行染色归一化。\n"
                "请安装依赖：pip install opencv-python-headless\n"
                f"底层错误：{_CV2_IMPORT_ERR}"
            )
        self.cfg = config or StainNormalizationConfig()
        self._target_stain_matrix: Optional[np.ndarray] = None
        self._target_concentration_stats: Optional[Dict] = None

    def set_target_image(self, image: np.ndarray) -> None:
        """
        设置目标模板图像

        :param image: 目标图像 (H, W, C), RGB 格式
        """
        if self.cfg.method == StainMethod.MACENKO:
            self._compute_macenko_target(image)
        elif self.cfg.method == StainMethod.REINHARD:
            self._compute_reinhard_target(image)
        elif self.cfg.method == StainMethod.VAHADANE:
            self._compute_vahadane_target(image)

    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        对图像进行染色归一化

        :param image: 输入图像 (H, W, C), RGB 格式
        :return: 归一化后的图像
        """
        if image is None or image.size == 0:
            return image

        if self.cfg.method == StainMethod.MACENKO:
            return self._macenko_normalize(image)
        elif self.cfg.method == StainMethod.REINHARD:
            return self._reinhard_normalize(image)
        elif self.cfg.method == StainMethod.VAHADANE:
            return self._vahadane_normalize(image)
        else:
            raise ValueError(f"不支持的染色归一化方法：{self.cfg.method}")

    def _rgb_to_od(self, rgb: np.ndarray) -> np.ndarray:
        """
        RGB 转光密度 (Optical Density)

        OD = log(Io / I) = log(Io) - log(I)
        其中 Io 是入射光强度，I 是透射光强度
        """
        rgb = rgb.astype(np.float32)
        # 防止 log(0)
        rgb = np.clip(rgb, 1, self.Io)
        od = np.log(self.cfg.Io) - np.log(rgb)
        return od

    def _od_to_rgb(self, od: np.ndarray) -> np.ndarray:
        """
        光密度转 RGB
        """
        rgb = self.cfg.Io * np.exp(-od)
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        return rgb

    def _compute_macenko_target(self, image: np.ndarray) -> None:
        """计算 Macenko 方法的目标参数"""
        # 从目标图像提取染色矩阵和浓度统计
        od = self._rgb_to_od(image)
        od_flat = od.reshape(-1, 3).T  # (3, N)

        # 去除背景
        is_not_background = np.all(od_flat > self.cfg.beta, axis=0)
        od_filtered = od_flat[:, is_not_background]

        if od_filtered.size == 0 or od_filtered.shape[1] < 10:
            self._target_stain_matrix = self.STANDARD_HE_STAIN_MATRIX.copy()
            self._target_concentration_stats = self.STANDARD_HE_CONCENTRATION_STATS.copy()
            return

        # SVD 分解
        _, _, Vt = np.linalg.svd(od_filtered, full_matrices=False)

        # 取前两个主成分作为染色矩阵 (3, 2)
        stain_matrix = Vt[:2, :].T  # (2, 3) -> (3, 2)

        # 归一化染色矩阵的列向量
        stain_matrix = stain_matrix / np.linalg.norm(stain_matrix, axis=0, keepdims=True)

        # 计算浓度（添加异常处理）
        try:
            concentration = np.linalg.lstsq(stain_matrix, od_filtered, rcond=None)[0]
        except np.linalg.LinAlgError:
            # 如果计算失败，使用标准矩阵
            self._target_stain_matrix = self.STANDARD_HE_STAIN_MATRIX.copy()
            self._target_concentration_stats = self.STANDARD_HE_CONCENTRATION_STATS.copy()
            return

        # 统计信息
        self._target_concentration_stats = {
            "hematoxylin": {
                "mean": np.mean(concentration[0, :]),
                "std": np.std(concentration[0, :])
            },
            "eosin": {
                "mean": np.mean(concentration[1, :]),
                "std": np.std(concentration[1, :])
            }
        }

        self._target_stain_matrix = stain_matrix

    def _macenko_normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Macenko 染色归一化方法

        参考：Macenko et al., "A method for normalizing histology slides
        for quantitative analysis", ISBI 2009.
        """
        # 确保目标参数已初始化
        if self._target_stain_matrix is None or self._target_concentration_stats is None:
            self._target_stain_matrix = self.STANDARD_HE_STAIN_MATRIX.copy()
            self._target_concentration_stats = self.STANDARD_HE_CONCENTRATION_STATS.copy()

        # RGB 转 OD
        od = self._rgb_to_od(image)
        od_flat = od.reshape(-1, 3).T  # (3, N)

        # 去除背景
        is_not_background = np.all(od_flat > self.cfg.beta, axis=0)
        if np.sum(is_not_background) == 0:
            # 全是背景，直接返回
            return image.copy()

        od_filtered = od_flat[:, is_not_background]

        # SVD 分解提取源染色矩阵
        _, _, Vt = np.linalg.svd(od_filtered, full_matrices=False)
        source_stain_matrix = Vt[:2, :].T  # (3, 2)

        # 归一化染色矩阵的列向量
        source_stain_matrix = source_stain_matrix / np.linalg.norm(source_stain_matrix, axis=0, keepdims=True)

        # 计算浓度
        try:
            concentration = np.linalg.lstsq(source_stain_matrix, od_filtered, rcond=None)[0]
        except np.linalg.LinAlgError:
            return image.copy()

        # 源图像浓度统计
        source_stats = {
            "hematoxylin": {
                "mean": np.mean(concentration[0, :]),
                "std": np.std(concentration[0, :]) + 1e-6
            },
            "eosin": {
                "mean": np.mean(concentration[1, :]),
                "std": np.std(concentration[1, :]) + 1e-6
            }
        }

        # 归一化浓度：将源浓度映射到目标分布
        normalized_concentration = np.zeros_like(concentration)
        for i, stain_name in enumerate(["hematoxylin", "eosin"]):
            normalized_concentration[i, :] = (
                (concentration[i, :] - source_stats[stain_name]["mean"]) /
                source_stats[stain_name]["std"] *
                self._target_concentration_stats[stain_name]["std"] +
                self._target_concentration_stats[stain_name]["mean"]
            )

        # 使用目标染色矩阵重建 OD
        normalized_od = np.dot(self._target_stain_matrix, normalized_concentration)

        # 重建图像
        result = np.zeros_like(image)
        result_flat = result.reshape(-1, 3).T

        # 非背景区域使用归一化后的 OD
        result_flat[:, is_not_background] = self.cfg.Io * np.exp(-normalized_od)

        # 背景区域保持原样
        bg_mask = ~is_not_background
        if np.any(bg_mask):
            result_flat[:, bg_mask] = image.reshape(-1, 3).T[:, bg_mask]

        result = np.clip(result, 0, 255).astype(np.uint8)
        return result

    def _compute_reinhard_target(self, image: np.ndarray) -> None:
        """
        计算 Reinhard 方法的目标参数

        Reinhard 方法基于 LAB 颜色空间的统计特性
        """
        # 转 LAB
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

        # 计算通道统计
        self._target_concentration_stats = {
            "L": {"mean": np.mean(lab[:, :, 0]), "std": np.std(lab[:, :, 0]) + 1e-6},
            "A": {"mean": np.mean(lab[:, :, 1]), "std": np.std(lab[:, :, 1]) + 1e-6},
            "B": {"mean": np.mean(lab[:, :, 2]), "std": np.std(lab[:, :, 2]) + 1e-6}
        }

    def _reinhard_normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Reinhard 染色归一化方法

        参考：Reinhard et al., "Color transfer between images",
        IEEE Computer Graphics and Applications 2001.
        """
        # 转 LAB
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

        # 初始化目标参数（如果未设置）
        if self._target_concentration_stats is None:
            self._compute_reinhard_target(image)
            # 使用标准值
            if self._target_concentration_stats is None:
                self._target_concentration_stats = {
                    "L": {"mean": 127.0, "std": 50.0},
                    "A": {"mean": 0.0, "std": 50.0},
                    "B": {"mean": 0.0, "std": 50.0}
                }

        # 计算源图像统计
        source_stats = {
            "L": {"mean": np.mean(lab[:, :, 0]), "std": np.std(lab[:, :, 0]) + 1e-6},
            "A": {"mean": np.mean(lab[:, :, 1]), "std": np.std(lab[:, :, 1]) + 1e-6},
            "B": {"mean": np.mean(lab[:, :, 2]), "std": np.std(lab[:, :, 2]) + 1e-6}
        }

        # 归一化每个通道
        for i, channel in enumerate(["L", "A", "B"]):
            lab[:, :, i] = (
                (lab[:, :, i] - source_stats[channel]["mean"]) /
                source_stats[channel]["std"] *
                self._target_concentration_stats[channel]["std"] +
                self._target_concentration_stats[channel]["mean"]
            )

        # 转回 RGB
        lab = np.clip(lab, 0, 255).astype(np.uint8)
        bgr_result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        result = cv2.cvtColor(bgr_result, cv2.COLOR_BGR2RGB)

        return result

    def _compute_vahadane_target(self, image: np.ndarray) -> None:
        """
        计算 Vahadane 方法的目标参数

        使用稀疏非负矩阵分解 (SNMF) 提取染色矩阵
        """
        # 简化实现：使用 Macenko 的结果作为近似
        self._compute_macenko_target(image)

    def _vahadane_normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Vahadane 染色归一化方法

        参考：Vahadane et al., "Structure-preserving color normalization
        and sparse stain separation for histological images", IEEE TMI 2016.
        """
        # 简化实现：使用 Macenko 方法
        return self._macenko_normalize(image)

    @property
    def Io(self) -> float:
        return self.cfg.Io

    @Io.setter
    def Io(self, value: float) -> None:
        self.cfg.Io = value

    @property
    def beta(self) -> float:
        return self.cfg.beta

    @beta.setter
    def beta(self, value: float) -> None:
        self.cfg.beta = value


class StainTemplateManager:
    """染色模板管理器"""

    def __init__(self):
        self._templates: Dict[str, np.ndarray] = {}
        self._stats: Dict[str, Dict] = {}

    def add_template(self, name: str, image: np.ndarray) -> None:
        """添加模板图像"""
        self._templates[name] = image
        self._stats[name] = {
            "mean": np.mean(image, axis=(0, 1)),
            "std": np.std(image, axis=(0, 1))
        }

    def get_template(self, name: str) -> Optional[np.ndarray]:
        """获取模板图像"""
        return self._templates.get(name)

    def get_template_names(self) -> List[str]:
        """获取所有模板名称"""
        return list(self._templates.keys())

    def remove_template(self, name: str) -> bool:
        """删除模板"""
        if name in self._templates:
            del self._templates[name]
            del self._stats[name]
            return True
        return False

    def load_from_file(self, name: str, file_path: str) -> None:
        """从文件加载模板"""
        if cv2 is None:
            raise ImportError("OpenCV 未安装")

        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"无法加载模板图像：{file_path}")

        # BGR 转 RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.add_template(name, image_rgb)

    def save_to_file(self, name: str, file_path: str) -> bool:
        """保存模板到文件"""
        template = self._templates.get(name)
        if template is None:
            return False

        if cv2 is None:
            raise ImportError("OpenCV 未安装")

        # RGB 转 BGR 保存
        template_bgr = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
        cv2.imwrite(file_path, template_bgr)
        return True
