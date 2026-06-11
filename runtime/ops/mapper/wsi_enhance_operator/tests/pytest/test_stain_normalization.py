"""
染色归一化模块单元测试
"""
import numpy as np
import pytest
from stain_normalization import StainNormalizer, StainNormalizationConfig, StainMethod


class TestStainMethod:
    """测试 StainMethod 枚举"""

    def test_stain_method_values(self):
        """测试染色方法枚举值"""
        assert StainMethod.MACENKO.value == "macenko"
        assert StainMethod.REINHARD.value == "reinhard"
        assert StainMethod.VAHADANE.value == "vahadane"


class TestStainNormalizationConfig:
    """测试 StainNormalizationConfig 配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = StainNormalizationConfig()
        assert config.method == StainMethod.MACENKO
        assert config.Io == 240.0
        assert config.beta == 0.15
        assert config.normalize_background is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = StainNormalizationConfig(
            method=StainMethod.REINHARD,
            Io=255.0,
            beta=0.2,
        )
        assert config.method == StainMethod.REINHARD
        assert config.Io == 255.0
        assert config.beta == 0.2


class TestStainNormalizer:
    """测试 StainNormalizer 染色归一化器"""

    @pytest.fixture
    def sample_image(self):
        """创建测试样本图像"""
        return np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)

    @pytest.fixture
    def target_image(self):
        """创建目标模板图像"""
        return np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)

    def test_macenko_basic(self, sample_image):
        """测试 Macenko 方法基本功能"""
        config = StainNormalizationConfig(method=StainMethod.MACENKO)
        normalizer = StainNormalizer(config)
        result = normalizer.normalize(sample_image)
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8
        assert result.min() >= 0
        assert result.max() <= 255

    def test_reinhard_basic(self, sample_image):
        """测试 Reinhard 方法基本功能"""
        config = StainNormalizationConfig(method=StainMethod.REINHARD)
        normalizer = StainNormalizer(config)
        result = normalizer.normalize(sample_image)
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8

    def test_vahadane_basic(self, sample_image):
        """测试 Vahadane 方法基本功能"""
        config = StainNormalizationConfig(method=StainMethod.VAHADANE)
        normalizer = StainNormalizer(config)
        result = normalizer.normalize(sample_image)
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8

    def test_empty_image(self):
        """测试空图像处理"""
        normalizer = StainNormalizer()
        empty = np.array([], dtype=np.uint8)
        result = normalizer.normalize(empty)
        assert result.size == 0

    def test_set_target_image_macenko(self, target_image):
        """测试设置目标图像 (Macenko)"""
        config = StainNormalizationConfig(method=StainMethod.MACENKO)
        normalizer = StainNormalizer(config)
        normalizer.set_target_image(target_image)
        assert normalizer._target_stain_matrix is not None
        assert normalizer._target_concentration_stats is not None

    def test_set_target_image_reinhard(self, target_image):
        """测试设置目标图像 (Reinhard)"""
        config = StainNormalizationConfig(method=StainMethod.REINHARD)
        normalizer = StainNormalizer(config)
        normalizer.set_target_image(target_image)
        assert normalizer._target_concentration_stats is not None

    def test_normalize_with_target(self, sample_image, target_image):
        """测试使用目标图像的归一化"""
        config = StainNormalizationConfig(method=StainMethod.MACENKO)
        normalizer = StainNormalizer(config)
        normalizer.set_target_image(target_image)
        result = normalizer.normalize(sample_image)
        assert result.shape == sample_image.shape

    def test_rgb_to_od(self):
        """测试 RGB 转 OD 转换"""
        normalizer = StainNormalizer()
        rgb = np.array([[[100, 150, 200]]], dtype=np.uint8)
        od = normalizer._rgb_to_od(rgb)
        assert np.issubdtype(od.dtype, np.floating)
        assert od.shape == rgb.shape

    def test_od_to_rgb(self):
        """测试 OD 转 RGB 转换"""
        normalizer = StainNormalizer()
        od = np.log(240) - np.log(np.array([[[100, 150, 200]]], dtype=np.float32))
        rgb = normalizer._od_to_rgb(od)
        assert rgb.dtype == np.uint8
        assert rgb.shape == od.shape

    def test_all_background_image(self):
        """测试全背景图像（高亮度区域）"""
        config = StainNormalizationConfig(method=StainMethod.MACENKO, beta=0.15)
        normalizer = StainNormalizer(config)
        bg_image = np.full((64, 64, 3), 235, dtype=np.uint8)
        result = normalizer.normalize(bg_image)
        assert result.shape == bg_image.shape

    def test_low_content_image(self):
        """测试低内容图像（组织区域很少）"""
        config = StainNormalizationConfig(method=StainMethod.MACENKO)
        normalizer = StainNormalizer(config)
        img = np.full((64, 64, 3), 230, dtype=np.uint8)
        img[10:20, 10:20] = [150, 100, 100]
        result = normalizer.normalize(img)
        assert result.shape == img.shape

    def test_io_property(self):
        """测试 Io 属性"""
        normalizer = StainNormalizer()
        assert normalizer.Io == 240.0
        normalizer.Io = 255.0
        assert normalizer.Io == 255.0

    def test_beta_property(self):
        """测试 beta 属性"""
        normalizer = StainNormalizer()
        assert normalizer.beta == 0.15
        normalizer.beta = 0.2
        assert normalizer.beta == 0.2

    def test_reinhard_color_statistics(self, sample_image):
        """测试 Reinhard 方法的色彩统计"""
        config = StainNormalizationConfig(method=StainMethod.REINHARD)
        normalizer = StainNormalizer(config)
        normalizer.set_target_image(sample_image)
        stats = normalizer._target_concentration_stats
        assert "L" in stats
        assert "A" in stats
        assert "B" in stats
        for key in ["L", "A", "B"]:
            assert "mean" in stats[key]
            assert "std" in stats[key]
