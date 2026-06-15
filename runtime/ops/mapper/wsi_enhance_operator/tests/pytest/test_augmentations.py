"""
数据增强模块单元测试
"""
import numpy as np
import pytest
from augmentations import Augmenter, AugmentationConfig


class TestAugmentationConfig:
    """测试 AugmentationConfig 配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = AugmentationConfig()
        assert config.enable_rotate is True
        assert config.rotate_range == (-30, 30)
        assert config.enable_flip is True
        assert config.enable_color_jitter is True
        assert config.enable_noise is False
        assert config.enable_blur is False
        assert config.enable_elastic is False

    def test_custom_config(self):
        """测试自定义配置"""
        config = AugmentationConfig(
            enable_rotate=False,
            rotate_range=(-45, 45),
            enable_flip=False,
            brightness_range=(0.5, 1.5),
        )
        assert config.enable_rotate is False
        assert config.rotate_range == (-45, 45)
        assert config.enable_flip is False
        assert config.brightness_range == (0.5, 1.5)


class TestAugmenter:
    """测试 Augmenter 数据增强器"""

    @pytest.fixture
    def sample_image(self):
        """创建测试样本图像"""
        return np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)

    @pytest.fixture
    def augmenter(self):
        """创建增强器实例"""
        config = AugmentationConfig()
        return Augmenter(config)

    def test_augment_basic(self, sample_image, augmenter):
        """测试基本增强功能"""
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8
        assert result.min() >= 0
        assert result.max() <= 255

    def test_augment_reproducibility(self, sample_image, augmenter):
        """测试增强结果可复现性"""
        result1 = augmenter.augment(sample_image, seed=42)
        result2 = augmenter.augment(sample_image, seed=42)
        assert np.array_equal(result1, result2)

    def test_augment_different_seeds(self, sample_image, augmenter):
        """测试不同种子产生不同结果"""
        result1 = augmenter.augment(sample_image, seed=42)
        result2 = augmenter.augment(sample_image, seed=100)
        assert not np.array_equal(result1, result2)

    def test_generate_augmented_batch(self, sample_image, augmenter):
        """测试批量生成增强图像"""
        results = augmenter.generate_augmented_batch(sample_image, n=3)
        assert len(results) == 3
        for img in results:
            assert img.shape == sample_image.shape
            assert img.dtype == np.uint8

    def test_generate_batch_with_seeds(self, sample_image, augmenter):
        """测试带种子的批量生成"""
        seeds = [1, 2, 3]
        results = augmenter.generate_augmented_batch(sample_image, n=3, seeds=seeds)
        assert len(results) == 3

    def test_empty_image(self, augmenter):
        """测试空图像处理"""
        empty = np.array([], dtype=np.uint8)
        result = augmenter.augment(empty)
        assert result.size == 0

    def test_rotate_only(self, sample_image):
        """测试仅旋转增强"""
        config = AugmentationConfig(
            enable_rotate=True,
            enable_flip=False,
            enable_color_jitter=False,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_flip_only(self, sample_image):
        """测试仅翻转增强"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_flip=True,
            enable_color_jitter=False,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_color_jitter_only(self, sample_image):
        """测试仅颜色抖动"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_flip=False,
            enable_color_jitter=True,
            enable_noise=False,
            enable_blur=False,
            enable_elastic=False,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_noise_enabled(self, sample_image):
        """测试噪声增强"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_color_jitter=False,
            enable_noise=True,
            gaussian_noise_var=0.01,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_blur_enabled(self, sample_image):
        """测试模糊增强"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_color_jitter=False,
            enable_blur=True,
            blur_kernel_size=5,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_elastic_enabled(self, sample_image):
        """测试弹性形变"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_color_jitter=False,
            enable_elastic=True,
            elastic_alpha=34.0,
            elastic_sigma=4.0,
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == sample_image.shape

    def test_output_size(self, sample_image):
        """测试输出尺寸裁剪"""
        config = AugmentationConfig(
            enable_rotate=False,
            enable_flip=False,
            enable_color_jitter=False,
            output_size=(128, 128),
        )
        augmenter = Augmenter(config)
        result = augmenter.augment(sample_image, seed=42)
        assert result.shape == (128, 128, 3)
