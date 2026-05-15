"""
数据增强模块：支持 WSI patch 的各种增强操作。

支持的增强类型：
1. 几何变换：随机旋转、翻转、弹性形变
2. 颜色变换：亮度、对比度、饱和度、色调调整
3. 噪声添加：高斯噪声、椒盐噪声
4. 模糊变换：高斯模糊、运动模糊
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

try:
    import cv2
except Exception as e:
    cv2 = None
    _CV2_IMPORT_ERR = e
else:
    _CV2_IMPORT_ERR = None


@dataclass
class AugmentationConfig:
    """数据增强配置"""
    # 几何变换
    enable_rotate: bool = True          # 是否启用随机旋转
    rotate_range: Tuple[int, int] = (-30, 30)  # 旋转角度范围
    enable_flip: bool = True            # 是否启用随机翻转
    flip_horizontal: bool = True        # 水平翻转
    flip_vertical: bool = True          # 垂直翻转

    # 颜色变换
    enable_color_jitter: bool = True    # 是否启用颜色抖动
    brightness_range: Tuple[float, float] = (0.8, 1.2)  # 亮度调整范围
    contrast_range: Tuple[float, float] = (0.8, 1.2)    # 对比度调整范围
    saturation_range: Tuple[float, float] = (0.8, 1.2)  # 饱和度调整范围
    hue_range: Tuple[float, float] = (-0.1, 0.1)        # 色调调整范围（-0.5~0.5）

    # 噪声添加
    enable_noise: bool = False          # 是否启用噪声
    gaussian_noise_var: float = 0.01    # 高斯噪声方差
    salt_pepper_ratio: float = 0.01     # 椒盐噪声比例

    # 模糊变换
    enable_blur: bool = False           # 是否启用模糊
    blur_kernel_size: int = 5           # 模糊核大小
    blur_sigma: float = 1.5             # 高斯模糊 sigma

    # 弹性形变
    enable_elastic: bool = False        # 是否启用弹性形变
    elastic_alpha: float = 34.0         # 弹性形变强度
    elastic_sigma: float = 4.0          # 弹性形变平滑度

    # 输出配置
    output_size: Optional[Tuple[int, int]] = None  # 输出尺寸，None 表示保持原尺寸


class Augmenter:
    """数据增强器"""

    def __init__(self, config: Optional[AugmentationConfig] = None):
        if cv2 is None:
            raise ImportError(
                "未安装 OpenCV(cv2)，无法进行数据增强。\n"
                "请安装依赖：pip install opencv-python-headless\n"
                f"底层错误：{_CV2_IMPORT_ERR}"
            )
        self.cfg = config or AugmentationConfig()

    def augment(self, image: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
        """
        对图像应用数据增强

        :param image: 输入图像 (H, W, C), RGB 格式
        :param seed: 随机种子，用于复现
        :return: 增强后的图像
        """
        if image is None or image.size == 0:
            return image

        # 设置随机种子
        if seed is not None:
            np.random.seed(seed)

        result = image.astype(np.float32)

        # 1. 几何变换
        result = self._apply_geometric(result)

        # 2. 颜色变换
        if self.cfg.enable_color_jitter:
            result = self._apply_color_jitter(result)

        # 3. 噪声添加
        if self.cfg.enable_noise:
            result = self._apply_noise(result)

        # 4. 模糊变换
        if self.cfg.enable_blur:
            result = self._apply_blur(result)

        # 5. 弹性形变
        if self.cfg.enable_elastic:
            result = self._apply_elastic(result)

        # 裁剪到目标尺寸
        if self.cfg.output_size is not None:
            result = self._crop_to_size(result, self.cfg.output_size)

        # 确保输出为 uint8
        result = np.clip(result, 0, 255).astype(np.uint8)

        return result

    def generate_augmented_batch(
        self,
        image: np.ndarray,
        n: int = 1,
        seeds: Optional[List[int]] = None
    ) -> List[np.ndarray]:
        """
        生成多个增强版本

        :param image: 原始图像
        :param n: 生成数量
        :param seeds: 可选的随机种子列表
        :return: 增强图像列表
        """
        results = []
        for i in range(n):
            seed = seeds[i] if seeds and i < len(seeds) else None
            augmented = self.augment(image, seed=seed)
            results.append(augmented)
        return results

    def _apply_geometric(self, image: np.ndarray) -> np.ndarray:
        """应用几何变换"""
        h, w = image.shape[:2]
        result = image.copy()

        # 旋转
        if self.cfg.enable_rotate:
            angle = np.random.uniform(*self.cfg.rotate_range)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            result = cv2.warpAffine(
                result, M, (w, h),
                borderMode=cv2.BORDER_REFLECT_101,
                flags=cv2.INTER_LINEAR
            )

        # 翻转
        if self.cfg.enable_flip:
            flip_code = -1  # 180 度翻转
            if self.cfg.flip_horizontal and not self.cfg.flip_vertical:
                flip_code = 1  # 水平翻转
            elif self.cfg.flip_vertical and not self.cfg.flip_horizontal:
                flip_code = 0  # 垂直翻转
            elif np.random.random() < 0.5:
                flip_code = 1
            else:
                flip_code = 0

            if flip_code >= 0:
                result = cv2.flip(result, flip_code)

        return result

    def _apply_color_jitter(self, image: np.ndarray) -> np.ndarray:
        """应用颜色抖动"""
        result = image.astype(np.float32)

        # 亮度调整
        brightness_factor = np.random.uniform(*self.cfg.brightness_range)
        result = result * brightness_factor

        # 对比度调整
        contrast_factor = np.random.uniform(*self.cfg.contrast_range)
        mean = np.mean(result, axis=(0, 1), keepdims=True)
        result = (result - mean) * contrast_factor + mean

        # 饱和度调整
        saturation_factor = np.random.uniform(*self.cfg.saturation_range)
        if saturation_factor != 1.0:
            hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv)
            s = np.clip(s.astype(np.float32) * saturation_factor, 0, 255)
            hsv = cv2.merge([h, s.astype(np.uint8), v])
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)

        # 色调调整
        hue_factor = np.random.uniform(*self.cfg.hue_range)
        if hue_factor != 0:
            hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv)
            h = ((h.astype(np.float32) / 180 + hue_factor) % 1) * 180
            hsv = cv2.merge([h.astype(np.uint8), s, v])
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)

        return result

    def _apply_noise(self, image: np.ndarray) -> np.ndarray:
        """应用噪声"""
        result = image.copy()

        # 高斯噪声
        if self.cfg.gaussian_noise_var > 0:
            noise = np.random.normal(0, np.sqrt(self.cfg.gaussian_noise_var) * 255, result.shape)
            result = result + noise

        # 椒盐噪声
        if self.cfg.salt_pepper_ratio > 0:
            h, w = result.shape[:2]
            num_pixels = int(h * w * self.cfg.salt_pepper_ratio)

            # 盐噪声（白色）
            salt_coords = [
                np.random.randint(0, h, num_pixels // 2),
                np.random.randint(0, w, num_pixels // 2)
            ]
            for i in range(len(salt_coords[0])):
                result[salt_coords[0][i], salt_coords[1][i]] = 255

            # 胡椒噪声（黑色）
            pepper_coords = [
                np.random.randint(0, h, num_pixels // 2),
                np.random.randint(0, w, num_pixels // 2)
            ]
            for i in range(len(pepper_coords[0])):
                result[pepper_coords[0][i], pepper_coords[1][i]] = 0

        return result

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """应用模糊"""
        kernel_size = self._odd(self.cfg.blur_kernel_size)

        # 高斯模糊
        result = cv2.GaussianBlur(
            image.astype(np.uint8),
            (kernel_size, kernel_size),
            self.cfg.blur_sigma
        )

        return result.astype(np.float32)

    def _apply_elastic(self, image: np.ndarray) -> np.ndarray:
        """应用弹性形变"""
        h, w = image.shape[:2]

        # 生成随机位移场
        sigma = self.cfg.elastic_sigma
        alpha = self.cfg.elastic_alpha

        # 生成平滑随机场
        dx = cv2.GaussianBlur(
            np.random.randn(h, w).astype(np.float32),
            (0, 0),
            sigma
        ) * alpha

        dy = cv2.GaussianBlur(
            np.random.randn(h, w).astype(np.float32),
            (0, 0),
            sigma
        ) * alpha

        # 创建映射
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        map_x = (x + dx).astype(np.float32)
        map_y = (y + dy).astype(np.float32)

        # 应用弹性形变
        result = cv2.remap(
            image.astype(np.uint8),
            map_x, map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101
        )

        return result.astype(np.float32)

    def _crop_to_size(self, image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """裁剪到目标尺寸"""
        h, w = image.shape[:2]
        target_h, target_w = size

        # 计算中心裁剪区域
        start_y = max(0, (h - target_h) // 2)
        start_x = max(0, (w - target_w) // 2)

        end_y = min(h, start_y + target_h)
        end_x = min(w, start_x + target_w)

        # 如果目标尺寸大于原图，则填充
        if target_h > h or target_w > w:
            result = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
            paste_y = max(0, (target_h - h) // 2)
            paste_x = max(0, (target_w - w) // 2)
            result[paste_y:paste_y+h, paste_x:paste_x+w] = image
            return result

        return image[start_y:end_y, start_x:end_x]

    @staticmethod
    def _odd(k: int) -> int:
        """确保数字为奇数"""
        return k if (k % 2 == 1) else (k + 1)
