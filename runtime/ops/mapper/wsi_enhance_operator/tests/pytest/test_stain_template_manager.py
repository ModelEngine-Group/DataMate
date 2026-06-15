"""
染色归一化模块补充单元测试 - StainTemplateManager
"""
import os
import numpy as np
import pytest

from stain_normalization import StainTemplateManager

# 检查 cv2 是否可用
try:
    import cv2 as _cv2_check
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class TestStainTemplateManager:
    """测试 StainTemplateManager 染色模板管理器"""

    @pytest.fixture
    def manager(self):
        """创建模板管理器实例"""
        return StainTemplateManager()

    @pytest.fixture
    def sample_template(self):
        """创建样本模板图像"""
        return np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)

    def test_add_template(self, manager, sample_template):
        """测试添加模板"""
        manager.add_template("test_template", sample_template)
        retrieved = manager.get_template("test_template")
        assert retrieved is not None
        assert retrieved.shape == sample_template.shape
        assert np.array_equal(retrieved, sample_template)

    def test_get_nonexistent_template(self, manager):
        """测试获取不存在的模板"""
        result = manager.get_template("nonexistent")
        assert result is None

    def test_get_template_names(self, manager, sample_template):
        """测试获取模板名称列表"""
        manager.add_template("template1", sample_template)
        manager.add_template("template2", sample_template)
        manager.add_template("template3", sample_template)
        names = manager.get_template_names()
        assert len(names) == 3
        assert "template1" in names
        assert "template2" in names
        assert "template3" in names

    def test_remove_existing_template(self, manager, sample_template):
        """测试删除存在的模板"""
        manager.add_template("to_remove", sample_template)
        result = manager.remove_template("to_remove")
        assert result is True
        assert manager.get_template("to_remove") is None
        assert "to_remove" not in manager.get_template_names()

    def test_remove_nonexistent_template(self, manager):
        """测试删除不存在的模板"""
        result = manager.remove_template("nonexistent")
        assert result is False

    def test_template_stats_stored(self, manager, sample_template):
        """测试模板统计信息被存储"""
        manager.add_template("test", sample_template)
        stats = manager._stats.get("test")
        assert stats is not None
        assert "mean" in stats
        assert "std" in stats
        assert stats["mean"].shape == (3,)
        assert stats["std"].shape == (3,)

    def test_template_mean_values(self, manager):
        """测试模板均值计算"""
        img = np.full((100, 100, 3), [100, 150, 200], dtype=np.uint8)
        manager.add_template("test", img)
        stats = manager._stats.get("test")
        assert np.allclose(stats["mean"], [100, 150, 200])

    def test_template_std_values(self, manager):
        """测试模板标准差计算"""
        img = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)
        manager.add_template("test", img)
        stats = manager._stats.get("test")
        assert np.allclose(stats["std"], [0, 0, 0])

    def test_multiple_templates_independent(self, manager, sample_template):
        """测试多个模板相互独立"""
        template1 = np.full((50, 50, 3), [100, 100, 100], dtype=np.uint8)
        template2 = np.full((50, 50, 3), [200, 200, 200], dtype=np.uint8)
        manager.add_template("dark", template1)
        manager.add_template("bright", template2)

        retrieved_dark = manager.get_template("dark")
        retrieved_bright = manager.get_template("bright")

        assert np.allclose(retrieved_dark[0, 0], [100, 100, 100])
        assert np.allclose(retrieved_bright[0, 0], [200, 200, 200])

    def test_update_template(self, manager, sample_template):
        """测试更新模板"""
        manager.add_template("test", sample_template)
        new_template = np.full((128, 128, 3), [50, 50, 50], dtype=np.uint8)
        manager.add_template("test", new_template)
        retrieved = manager.get_template("test")
        assert retrieved.shape == (128, 128, 3)
        assert np.allclose(retrieved[0, 0], [50, 50, 50])


@pytest.mark.skipif(not CV2_AVAILABLE, reason="需要 cv2 支持")
class TestStainTemplateManagerWithCV:
    """测试 StainTemplateManager 文件 I/O（需要 cv2）"""

    @pytest.fixture
    def manager_with_cv(self):
        """创建带 cv2 支持的模板管理器"""
        return StainTemplateManager()

    @pytest.fixture
    def temp_image_file(self, tmp_path):
        """创建临时图像文件"""
        img = np.random.randint(50, 200, (128, 128, 3), dtype=np.uint8)
        img_path = tmp_path / "template.png"
        _cv2_check.imwrite(str(img_path), img)
        return str(img_path)

    def test_load_from_file(self, manager_with_cv, temp_image_file, tmp_path):
        """测试从文件加载模板"""
        manager_with_cv.load_from_file("from_file", temp_image_file)
        template = manager_with_cv.get_template("from_file")
        assert template is not None
        assert template.shape == (128, 128, 3)

    def test_save_to_file(self, manager_with_cv, tmp_path):
        """测试保存模板到文件"""
        original = np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)
        manager_with_cv.add_template("to_save", original)

        save_path = str(tmp_path / "saved_template.png")
        result = manager_with_cv.save_to_file("to_save", save_path)

        assert result is True
        assert os.path.exists(save_path)

        loaded = _cv2_check.imread(save_path)
        assert loaded is not None

    def test_save_nonexistent_template(self, manager_with_cv, tmp_path):
        """测试保存不存在的模板"""
        save_path = str(tmp_path / "should_not_exist.png")
        result = manager_with_cv.save_to_file("nonexistent", save_path)
        assert result is False

    def test_load_invalid_file(self, manager_with_cv):
        """测试加载无效文件"""
        with pytest.raises(ValueError, match="无法加载模板图像"):
            manager_with_cv.load_from_file("invalid", "/nonexistent/file.png")


class TestStainTemplateManagerEdgeCases:
    """测试 StainTemplateManager 边界情况"""

    @pytest.fixture
    def manager(self):
        """创建模板管理器实例"""
        return StainTemplateManager()

    @pytest.fixture
    def sample_template(self):
        """创建样本模板图像"""
        return np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)

    def test_empty_image_template(self, manager):
        """测试空图像模板"""
        tiny = np.array([[[128, 64, 192]]], dtype=np.uint8)
        manager.add_template("tiny", tiny)
        retrieved = manager.get_template("tiny")
        assert retrieved.size == 3

    def test_single_pixel_template(self, manager):
        """测试单像素模板"""
        pixel = np.array([[[128, 64, 192]]], dtype=np.uint8)
        manager.add_template("single", pixel)
        stats = manager._stats.get("single")
        assert stats["mean"].shape == (3,)
        assert np.allclose(stats["mean"], [128, 64, 192])

    def test_grayscale_template(self, manager):
        """测试灰度图像模板"""
        gray = np.full((32, 32), 128, dtype=np.uint8)
        manager.add_template("grayscale", gray)
        retrieved = manager.get_template("grayscale")
        assert retrieved is not None

    def test_large_template(self, manager):
        """测试大尺寸模板"""
        large = np.random.randint(50, 200, (1024, 1024, 3), dtype=np.uint8)
        manager.add_template("large", large)
        stats = manager._stats.get("large")
        assert stats is not None
        assert all(0 <= m <= 255 for m in stats["mean"])

    def test_template_with_extreme_values(self, manager):
        """测试带极值的模板"""
        extreme = np.zeros((10, 10, 3), dtype=np.uint8)
        extreme[0, 0] = [255, 255, 255]
        manager.add_template("extreme", extreme)
        stats = manager._stats.get("extreme")
        assert all(m < 10 for m in stats["mean"])

    def test_remove_template_clears_stats(self, manager, sample_template):
        """测试删除模板时统计信息也被清除"""
        manager.add_template("test", sample_template)
        manager.remove_template("test")
        assert "test" not in manager._stats

    def test_add_template_with_special_characters(self, manager, sample_template):
        """测试模板名带特殊字符"""
        manager.add_template("test-template_123", sample_template)
        assert manager.get_template("test-template_123") is not None
        assert "test-template_123" in manager.get_template_names()

    def test_concurrent_template_operations(self, manager, sample_template):
        """测试并发模板操作"""
        for i in range(10):
            manager.add_template(f"template_{i}", sample_template)

        assert len(manager.get_template_names()) == 10

        for i in range(0, 10, 2):
            manager.remove_template(f"template_{i}")

        remaining = manager.get_template_names()
        assert len(remaining) == 5
        for i in range(1, 10, 2):
            assert f"template_{i}" in remaining
