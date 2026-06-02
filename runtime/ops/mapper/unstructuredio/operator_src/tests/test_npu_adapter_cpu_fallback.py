import importlib.util
import sys
import types
from pathlib import Path


def _load_npu_adapter():
    if "torch_npu" not in sys.modules:
        sys.modules["torch_npu"] = types.ModuleType("torch_npu")
    module_path = Path(__file__).resolve().parents[1] / "adapters" / "npu_adapter.py"
    spec = importlib.util.spec_from_file_location("npu_adapter_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_npu_get_model_delegates_to_original_loader_when_cpu_forced_and_local_model_missing(monkeypatch):
    adapter = _load_npu_adapter()
    calls = []

    def original_get_model(model_name, **kwargs):
        calls.append((model_name, kwargs))
        return "cpu-model"

    adapter._ORIGINAL_GET_MODEL = original_get_model
    monkeypatch.setattr(adapter, "_resolve_yolox_model_path", lambda: str(Path("missing.pt")))
    monkeypatch.setenv("UNSTRUCTUREDIO_FORCE_CPU_MODELS", "1")

    assert adapter.npu_get_model("yolox", foo="bar", password="secret") == "cpu-model"
    assert calls == [("yolox", {"foo": "bar"})]
