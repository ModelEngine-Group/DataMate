"""Unit tests for the WSI processor module."""

import numpy as np
import pytest

from wsi_processor import DetectionResult, ProcessorConfig, WSIProcessor


class TestProcessorConfig:
    def test_default_config(self):
        config = ProcessorConfig()
        assert config.sat_thresh == 8
        assert config.val_max == 225
        assert config.tissue_min_area == 3000
        assert config.tissue_close_kernel == 51
        assert config.enable_bubble is False
        assert config.enable_artifact is True

    def test_custom_config(self):
        config = ProcessorConfig(
            sat_thresh=10,
            val_max=200,
            tissue_min_area=5000,
            enable_bubble=True,
        )
        assert config.sat_thresh == 10
        assert config.val_max == 200
        assert config.tissue_min_area == 5000
        assert config.enable_bubble is True


class TestDetectionResult:
    def test_detection_result_creation(self):
        tissue_mask = np.zeros((100, 100), dtype=np.uint8)
        bubble_mask = np.zeros((100, 100), dtype=np.uint8)
        note_mask = np.zeros((100, 100), dtype=np.uint8)
        artifact_mask = np.zeros((100, 100), dtype=np.uint8)
        global_stain_mask = np.zeros((100, 100), dtype=np.uint8)
        contours = {
            "tissue": [],
            "bubble": [],
            "note": [],
            "artifact": [],
            "global_stain": [],
        }
        result = DetectionResult(
            tissue_mask=tissue_mask,
            bubble_mask=bubble_mask,
            note_mask=note_mask,
            artifact_mask=artifact_mask,
            global_stain_mask=global_stain_mask,
            contours=contours,
        )
        assert result.tissue_mask.shape == (100, 100)
        assert result.bubble_mask.shape == (100, 100)
        assert len(result.contours["tissue"]) == 0


class TestWSIProcessor:
    @pytest.fixture
    def sample_thumbnail(self):
        img = np.zeros((256, 256, 3), dtype=np.uint8)
        img[:, :] = [200, 150, 150]
        return img

    @pytest.fixture
    def processor(self):
        return WSIProcessor(ProcessorConfig())

    def test_detect_basic(self, sample_thumbnail, processor):
        result = processor.detect(sample_thumbnail)
        assert isinstance(result, DetectionResult)
        assert result.tissue_mask.shape == sample_thumbnail.shape[:2]
        assert result.note_mask.shape == sample_thumbnail.shape[:2]
        assert result.artifact_mask.shape == sample_thumbnail.shape[:2]
        assert result.global_stain_mask.shape == sample_thumbnail.shape[:2]

    def test_detect_contours(self, sample_thumbnail, processor):
        result = processor.detect(sample_thumbnail)
        assert "tissue" in result.contours
        assert "bubble" in result.contours
        assert "note" in result.contours
        assert "artifact" in result.contours
        assert "global_stain" in result.contours

    def test_empty_input(self, processor):
        empty = np.array([], dtype=np.uint8)
        with pytest.raises(ValueError):
            processor.detect(empty)

    def test_wrong_shape_input(self, processor):
        wrong_shape = np.zeros((256, 256), dtype=np.uint8)
        with pytest.raises(ValueError):
            processor.detect(wrong_shape)

    def test_tissue_mask_values(self, sample_thumbnail, processor):
        result = processor.detect(sample_thumbnail)
        assert result.tissue_mask.min() >= 0
        assert result.tissue_mask.max() <= 255

    def test_bubble_disabled(self, sample_thumbnail):
        config = ProcessorConfig(enable_bubble=False)
        processor = WSIProcessor(config)
        result = processor.detect(sample_thumbnail)
        assert result.bubble_mask.shape == sample_thumbnail.shape[:2]

    def test_bubble_enabled(self, sample_thumbnail):
        config = ProcessorConfig(enable_bubble=True)
        processor = WSIProcessor(config)
        result = processor.detect(sample_thumbnail)
        assert result.bubble_mask.shape == sample_thumbnail.shape[:2]

    def test_artifact_disabled(self, sample_thumbnail):
        config = ProcessorConfig(enable_artifact=False)
        processor = WSIProcessor(config)
        result = processor.detect(sample_thumbnail)
        assert result.artifact_mask.shape == sample_thumbnail.shape[:2]

    def test_folding_detection(self, sample_thumbnail):
        config = ProcessorConfig(
            enable_folding_artifact=True,
            treat_folding_as_tissue=False,
        )
        processor = WSIProcessor(config)
        result = processor.detect(sample_thumbnail)
        assert result.artifact_mask is not None

    def test_note_detection_dark_region(self, processor):
        img = np.zeros((256, 256, 3), dtype=np.uint8)
        img[:, :] = [200, 150, 150]
        img[100:120, 100:120] = [30, 30, 30]
        result = processor.detect(img)
        assert result.note_mask.shape == (256, 256)

    def test_global_stain_detection(self, sample_thumbnail, processor):
        result = processor.detect(sample_thumbnail)
        assert result.global_stain_mask.shape == sample_thumbnail.shape[:2]

    def test_processor_with_simulated_tissue(self):
        img = np.full((512, 512, 3), 255, dtype=np.uint8)
        img[100:400, 100:400] = [180, 120, 140]
        config = ProcessorConfig(tissue_min_area=1000)
        processor = WSIProcessor(config)
        result = processor.detect(img)
        assert result.tissue_mask.shape == (512, 512)
        assert np.any(result.tissue_mask > 0)

    def test_filter_small_components(self, processor):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:12, 10:12] = 255
        mask[50:60, 50:60] = 255
        result = processor._filter_small_components(mask, min_area=50)
        assert np.sum(result > 0) == 100

    def test_odd_helper(self, processor):
        assert processor._odd(3) == 3
        assert processor._odd(4) == 5
        assert processor._odd(1) == 1

    def test_hsv_conversion(self, processor):
        rgb = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        hsv = processor._to_hsv(rgb)
        assert hsv.shape == rgb.shape
        assert hsv.dtype == np.uint8
