"""Helper and edge-case unit tests for WSIEnhance modules."""

import numpy as np
import pytest

from augmentations import Augmenter, AugmentationConfig
from stain_normalization import (
    StainMethod,
    StainNormalizationConfig,
    StainNormalizer,
)
from wsi_processor import DetectionResult, ProcessorConfig, WSIProcessor

try:
    import cv2
except ImportError:
    cv2 = None


class TestWSIProcessorHelpers:
    @pytest.fixture
    def processor(self):
        return WSIProcessor(ProcessorConfig())

    def test_odd_helper(self, processor):
        assert processor._odd(1) == 1
        assert processor._odd(2) == 3
        assert processor._odd(3) == 3
        assert processor._odd(4) == 5
        assert processor._odd(100) == 101

    def test_to_hsv_conversion(self, processor):
        red = np.array([[[255, 0, 0]]], dtype=np.uint8)
        hsv = processor._to_hsv(red)
        assert hsv.shape == red.shape
        assert hsv.dtype == np.uint8

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_to_hsv_white(self, processor):
        white = np.full((10, 10, 3), 255, dtype=np.uint8)
        hsv = processor._to_hsv(white)
        _, _, v = cv2.split(hsv)
        assert np.all(v == 255)

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_to_hsv_black(self, processor):
        black = np.zeros((10, 10, 3), dtype=np.uint8)
        hsv = processor._to_hsv(black)
        _, _, v = cv2.split(hsv)
        assert np.all(v == 0)

    def test_filter_small_components_empty(self, processor):
        mask = np.zeros((50, 50), dtype=np.uint8)
        result = processor._filter_small_components(mask, min_area=10)
        assert np.array_equal(result, mask)

    def test_filter_small_components_all_kept(self, processor):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[10:20, 10:20] = 255
        result = processor._filter_small_components(mask, min_area=50)
        assert np.sum(result > 0) == 100

    def test_filter_small_components_some_removed(self, processor):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[10:12, 10:12] = 255
        mask[30:40, 30:40] = 255
        result = processor._filter_small_components(mask, min_area=10)
        assert np.sum(result > 0) == 100

    def test_filter_small_components_multiple_components(self, processor):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:15, 10:15] = 255
        mask[30:40, 30:40] = 255
        mask[60:63, 60:63] = 255
        result = processor._filter_small_components(mask, min_area=20)
        assert np.sum(result > 0) == 125

    def test_fill_holes_empty(self, processor):
        mask = np.zeros((50, 50), dtype=np.uint8)
        result = processor._fill_holes(mask)
        assert np.array_equal(result, mask)

    def test_fill_holes_with_hole(self, processor):
        mask = np.ones((50, 50), dtype=np.uint8) * 255
        mask[20:30, 20:30] = 0
        result = processor._fill_holes(mask)
        assert np.all(result[20:30, 20:30] == 255)


class TestAugmenterHelpers:
    @pytest.fixture
    def augmenter(self):
        return Augmenter(AugmentationConfig())

    def test_odd_helper(self, augmenter):
        assert augmenter._odd(1) == 1
        assert augmenter._odd(2) == 3
        assert augmenter._odd(3) == 3
        assert augmenter._odd(100) == 101

    def test_crop_to_center(self, augmenter):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = augmenter._crop_to_size(img, (50, 50))
        assert result.shape == (50, 50, 3)

    def test_crop_to_larger(self, augmenter):
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        result = augmenter._crop_to_size(img, (100, 100))
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result[25:75, 25:75], img)

    def test_crop_same_size(self, augmenter):
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = augmenter._crop_to_size(img, (64, 64))
        assert result.shape == (64, 64, 3)


class TestStainNormalizerHelpers:
    @pytest.fixture
    def normalizer(self):
        return StainNormalizer(StainNormalizationConfig(method=StainMethod.MACENKO))

    def test_rgb_to_od_basic(self, normalizer):
        rgb = np.array([[[128, 128, 128]]], dtype=np.uint8)
        od = normalizer._rgb_to_od(rgb)
        assert od.shape == rgb.shape
        assert np.issubdtype(od.dtype, np.floating)

    def test_rgb_to_od_white(self, normalizer):
        white = np.full((10, 10, 3), 240, dtype=np.uint8)
        od = normalizer._rgb_to_od(white)
        assert np.all(od < 1)

    def test_rgb_to_od_clipping(self, normalizer):
        black = np.zeros((10, 10, 3), dtype=np.uint8)
        od = normalizer._rgb_to_od(black)
        assert np.all(np.isfinite(od))

    def test_od_to_rgb_basic(self, normalizer):
        od = np.log(240) - np.log(np.array([[[128, 128, 128]]], dtype=np.float32))
        rgb = normalizer._od_to_rgb(od)
        assert rgb.dtype == np.uint8
        assert rgb.shape == od.shape

    def test_io_property(self, normalizer):
        assert normalizer.Io == 240.0
        normalizer.Io = 255.0
        assert normalizer.Io == 255.0

    def test_beta_property(self, normalizer):
        assert normalizer.beta == 0.15
        normalizer.beta = 0.2
        assert normalizer.beta == 0.2


class TestConfigDataclasses:
    def test_processor_config_all_fields(self):
        cfg = ProcessorConfig()
        assert hasattr(cfg, "sat_thresh")
        assert hasattr(cfg, "val_max")
        assert hasattr(cfg, "tissue_min_area")
        assert hasattr(cfg, "enable_bubble")
        assert hasattr(cfg, "enable_artifact")

    def test_augmentation_config_all_fields(self):
        cfg = AugmentationConfig()
        assert hasattr(cfg, "enable_rotate")
        assert hasattr(cfg, "enable_flip")
        assert hasattr(cfg, "enable_color_jitter")
        assert hasattr(cfg, "enable_noise")
        assert hasattr(cfg, "enable_blur")
        assert hasattr(cfg, "enable_elastic")

    def test_stain_normalization_config_all_fields(self):
        cfg = StainNormalizationConfig()
        assert hasattr(cfg, "method")
        assert hasattr(cfg, "Io")
        assert hasattr(cfg, "beta")
        assert hasattr(cfg, "normalize_background")


class TestModuleImports:
    def test_wsi_processor_import(self):
        assert WSIProcessor is not None
        assert ProcessorConfig is not None
        assert DetectionResult is not None

    def test_augmentations_import(self):
        assert Augmenter is not None
        assert AugmentationConfig is not None

    def test_stain_normalization_import(self):
        assert StainNormalizer is not None
        assert StainNormalizationConfig is not None
        assert StainMethod is not None


class TestColorConversions:
    @pytest.fixture
    def processor(self):
        return WSIProcessor(ProcessorConfig())

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_hsv_red_color(self, processor):
        red = np.full((10, 10, 3), [255, 0, 0], dtype=np.uint8)
        hsv = processor._to_hsv(red)
        h, _, _ = cv2.split(hsv)
        h_val = h[0, 0]
        assert h_val <= 10 or h_val >= 160

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_hsv_green_color(self, processor):
        green = np.full((10, 10, 3), [0, 255, 0], dtype=np.uint8)
        hsv = processor._to_hsv(green)
        h, _, _ = cv2.split(hsv)
        h_val = h[0, 0]
        assert 40 <= h_val <= 80

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_hsv_blue_color(self, processor):
        blue = np.full((10, 10, 3), [0, 0, 255], dtype=np.uint8)
        hsv = processor._to_hsv(blue)
        h, _, _ = cv2.split(hsv)
        h_val = h[0, 0]
        assert 100 <= h_val <= 130

    @pytest.mark.skipif(cv2 is None, reason="cv2 required")
    def test_hsv_gray_color(self, processor):
        gray = np.full((10, 10, 3), [128, 128, 128], dtype=np.uint8)
        hsv = processor._to_hsv(gray)
        _, s, v = cv2.split(hsv)
        s_val = s[0, 0]
        v_val = v[0, 0]
        assert s_val < 30
        assert 100 <= v_val <= 150
