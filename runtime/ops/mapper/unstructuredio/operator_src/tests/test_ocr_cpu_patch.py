import importlib.util
from pathlib import Path


def _load_ocr_adapter():
    module_path = Path(__file__).resolve().parents[1] / "adapters" / "ocr_npu_adapter.py"
    spec = importlib.util.spec_from_file_location("ocr_adapter_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_force_paddle_cpu_patch_does_not_require_native_tesseract(monkeypatch):
    adapter = _load_ocr_adapter()

    def fail_native_load():
        raise ModuleNotFoundError("pytesseract")

    monkeypatch.setattr(adapter, "_load_native_tesseract_modules", fail_native_load)
    monkeypatch.setenv("OCR_ADAPTER_FORCE_PADDLE_CPU", "1")

    adapter.apply_ocr_patch()

    assert "pytesseract" in adapter.sys.modules
    assert "unstructured_pytesseract" in adapter.sys.modules


def test_cpu_paddle_availability_check_does_not_import_paddle_in_parent(monkeypatch):
    adapter = _load_ocr_adapter()
    imported = []

    def fake_find_spec(name):
        return object() if name in {"paddle", "paddleocr"} else None

    def fail_import(name):
        imported.append(name)
        raise AssertionError("parent process must not import paddle for CPU OCR availability")

    monkeypatch.setattr(adapter.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(adapter.importlib, "import_module", fail_import)
    monkeypatch.setenv("OCR_ADAPTER_DEVICE", "cpu")

    assert adapter._paddle_ocr_available() is True
    assert imported == []
