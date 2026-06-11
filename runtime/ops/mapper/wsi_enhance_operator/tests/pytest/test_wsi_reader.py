"""Unit tests for the WSI reader module."""

import os

import numpy as np
import pytest

from wsi_reader import WSIReader
import wsi_reader.wsi_reader as wsi_reader_module


# Reuse the operator module's preload result instead of importing openslide
# directly here; the operator bundles libopenslide under its own directory.
OPENSLIDE_AVAILABLE = wsi_reader_module.openslide is not None


def _resolve_test_wsi_path():
    env_path = os.environ.get("WSI_TEST_FILE")
    if env_path and os.path.exists(env_path):
        return env_path

    test_files = [
        "Tests/patient_190_node_0.tif",
        "Tests/hcmi_cmdc_test1.svs",
    ]
    for file_path in test_files:
        if os.path.exists(file_path):
            return file_path
    return None


def _create_test_raster(tmp_path):
    image_cls = wsi_reader_module.Image
    if image_cls is None:
        raise AssertionError("Pillow is required for raster-based WSIReader tests")

    height, width = 1000, 1200
    yy, xx = np.indices((height, width))
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[:, :, 0] = (xx % 256).astype(np.uint8)
    rgb[:, :, 1] = (yy % 256).astype(np.uint8)
    rgb[:, :, 2] = ((xx + yy) % 256).astype(np.uint8)

    raster_path = tmp_path / "generated_test_image.png"
    image_cls.fromarray(rgb, mode="RGB").save(raster_path)
    return str(raster_path)


def _resolve_supported_test_input(tmp_path):
    return _resolve_test_wsi_path() or _create_test_raster(tmp_path)


class TestWSIReader:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            WSIReader("/nonexistent/path/file.svs")

    def test_missing_openslide(self, tmp_path, monkeypatch):
        fake_wsi = tmp_path / "fake_missing_openslide.svs"
        fake_wsi.write_bytes(b"placeholder")

        monkeypatch.setattr(wsi_reader_module, "openslide", None)
        monkeypatch.setattr(
            wsi_reader_module,
            "_OPENSLIDE_IMPORT_ERROR",
            ImportError("mock missing openslide"),
            raising=False,
        )

        with pytest.raises(ImportError, match="openslide"):
            WSIReader(str(fake_wsi))


class TestWSIReaderMock:
    @pytest.fixture
    def temp_image_file(self, tmp_path):
        return _create_test_raster(tmp_path)

    def test_reader_creation_with_mock(self, temp_image_file):
        with WSIReader(temp_image_file) as reader:
            assert reader.width == 1200
            assert reader.height == 1000
            assert reader.level_count >= 1


class TestWSIReaderIntegration:
    @pytest.fixture
    def test_wsi_path(self, tmp_path):
        return _resolve_supported_test_input(tmp_path)

    def test_open_wsi(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            assert reader.width > 0
            assert reader.height > 0
            assert reader.level_count > 0

    def test_get_thumbnail(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            thumbnail = reader.get_thumbnail((1024, 1024))
            assert isinstance(thumbnail, np.ndarray)
            assert thumbnail.ndim == 3
            assert thumbnail.shape[2] == 3
            assert thumbnail.dtype == np.uint8

    def test_read_region(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            region = reader.read_region(0, 0, 256, 256, level=0)
            assert isinstance(region, np.ndarray)
            assert region.shape == (256, 256, 3) or region.shape == (256, 256)
            assert region.dtype == np.uint8

    def test_dimensions_property(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            assert reader.width > 0
            assert reader.height > 0

    def test_context_manager(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            if reader._mode == "openslide":
                assert reader._slide is not None
            else:
                assert reader._image is not None
        assert reader._slide is None

    def test_close_method(self, test_wsi_path):
        reader = WSIReader(test_wsi_path)
        if reader._mode == "openslide":
            assert reader._slide is not None
        else:
            assert reader._image is not None
        reader.close()
        assert reader._slide is None

    def test_thumbnail_size_variations(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            for size in [(512, 512), (1024, 1024), (2048, 2048)]:
                thumb = reader.get_thumbnail(size)
                assert thumb.shape[0] <= size[1]
                assert thumb.shape[1] <= size[0]

    def test_read_multiple_regions(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            regions = []
            for x in [0, 1000, 2000]:
                for y in [0, 1000, 2000]:
                    try:
                        region = reader.read_region(x, y, 256, 256)
                        regions.append(region)
                    except Exception:
                        pass
            assert len(regions) > 0


class TestWSIReaderEdgeCases:
    @pytest.fixture
    def test_wsi_path(self, tmp_path):
        return _resolve_supported_test_input(tmp_path)

    def test_read_region_at_boundary(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            w, h = reader.width, reader.height
            region = reader.read_region(w - 256, h - 256, 256, 256)
            assert region.shape[0] == 256
            assert region.shape[1] == 256

    def test_read_multiple_levels(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            for level in range(min(3, reader.level_count)):
                region = reader.read_region(0, 0, 256, 256, level=level)
                assert region is not None

    def test_thumbnail_grayscale_handling(self, test_wsi_path):
        with WSIReader(test_wsi_path) as reader:
            thumb = reader.get_thumbnail((512, 512))
            assert thumb.ndim == 3
            assert thumb.shape[2] in [3, 4]


class TestWSIReaderRealWSIPathResolution:
    def test_real_wsi_env_path_is_preferred_when_present(self, tmp_path, monkeypatch):
        real_wsi = tmp_path / "override.svs"
        real_wsi.write_bytes(b"placeholder")
        monkeypatch.setenv("WSI_TEST_FILE", str(real_wsi))
        assert _resolve_test_wsi_path() == str(real_wsi)

    def test_raster_fallback_is_created_when_real_wsi_missing(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WSI_TEST_FILE", raising=False)
        for candidate in ("Tests/patient_190_node_0.tif", "Tests/hcmi_cmdc_test1.svs"):
            if os.path.exists(candidate):
                monkeypatch.setattr(os.path, "exists", lambda path, _orig=os.path.exists: False if path == candidate else _orig(path))
        fallback = _resolve_supported_test_input(tmp_path)
        assert os.path.exists(fallback)
        assert fallback.endswith(".png")
