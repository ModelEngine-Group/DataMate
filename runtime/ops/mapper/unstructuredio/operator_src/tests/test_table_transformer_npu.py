import sys
import types

from test_pdf_npu_ocr_priority import _load_process_module


def _install_fake_transformers(monkeypatch, calls):
    transformers = types.ModuleType("transformers")

    class FakeProcessor:
        @classmethod
        def from_pretrained(cls, model_path, local_files_only=False):
            calls.append(("processor", str(model_path), local_files_only))
            return cls()

    class FakeConfig:
        last = None

        def __init__(self):
            self.use_pretrained_backbone = True
            FakeConfig.last = self

        @classmethod
        def from_pretrained(cls, model_path, local_files_only=False):
            calls.append(("config", str(model_path), local_files_only))
            return cls()

    class FakeModel:
        def __init__(self, config):
            calls.append(("model_init", config.use_pretrained_backbone))
            self.config = config
            self.loaded = None
            self.to_device = None

        def load_state_dict(self, state_dict, strict=False):
            calls.append(("load_state_dict", state_dict, strict))
            self.loaded = state_dict
            return [], []

        def eval(self):
            calls.append(("eval",))
            return self

        def to(self, device):
            calls.append(("to", device))
            self.to_device = device
            return self

    transformers.DetrImageProcessor = FakeProcessor
    transformers.TableTransformerConfig = FakeConfig
    transformers.TableTransformerForObjectDetection = FakeModel
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return FakeModel


def _install_fake_safetensors(monkeypatch, calls):
    safetensors = types.ModuleType("safetensors")
    safetensors_torch = types.ModuleType("safetensors.torch")

    def load_file(path, device="cpu"):
        calls.append(("load_safetensors", str(path), device))
        return {"weight": "from-safetensors"}

    safetensors_torch.load_file = load_file
    monkeypatch.setitem(sys.modules, "safetensors", safetensors)
    monkeypatch.setitem(sys.modules, "safetensors.torch", safetensors_torch)


def test_table_transformer_loader_uses_config_state_dict_and_npu(monkeypatch, tmp_path):
    process = _load_process_module()
    calls = []
    model_cls = _install_fake_transformers(monkeypatch, calls)
    _install_fake_safetensors(monkeypatch, calls)
    (tmp_path / "model.safetensors").write_text("fake", encoding="utf-8")

    feature_extractor, model = process._load_local_table_transformer_model(tmp_path, "npu:0")

    assert feature_extractor is not None
    assert isinstance(model, model_cls)
    assert ("config", str(tmp_path), True) in calls
    assert ("model_init", False) in calls
    assert ("load_safetensors", str(tmp_path / "model.safetensors"), "cpu") in calls
    assert ("load_state_dict", {"weight": "from-safetensors"}, False) in calls
    assert ("to", "npu:0") in calls
    assert model.to_device == "npu:0"


def test_pdf_runtime_overrides_initializes_table_agent_on_npu(monkeypatch, tmp_path):
    process = _load_process_module()
    calls = []
    _install_fake_transformers(monkeypatch, calls)

    unstructured_inference = types.ModuleType("unstructured_inference")
    models_module = types.ModuleType("unstructured_inference.models")
    tables_module = types.ModuleType("unstructured_inference.models.tables")

    class FakeTableAgent:
        model = None

    class FakeTableTransformerModel:
        initialize = lambda self, model=None, device="cpu": None

    tables_module.DEFAULT_MODEL = "old-model"
    tables_module.tables_agent = FakeTableAgent()
    tables_module.UnstructuredTableTransformerModel = FakeTableTransformerModel
    tables_module.load_agent = lambda: None
    models_module.tables = tables_module
    unstructured_inference.models = models_module
    monkeypatch.setitem(sys.modules, "unstructured_inference", unstructured_inference)
    monkeypatch.setitem(sys.modules, "unstructured_inference.models", models_module)
    monkeypatch.setitem(sys.modules, "unstructured_inference.models.tables", tables_module)
    monkeypatch.setattr(process, "PDF_TABLE_MODEL_PATH", str(tmp_path))
    monkeypatch.setattr(process, "_select_table_transformer_device", lambda: "npu:0")

    def fake_loader(model_path, device):
        calls.append(("loader", str(model_path), device))
        return "feature-extractor", "table-model"

    monkeypatch.setattr(process, "_load_local_table_transformer_model", fake_loader, raising=False)

    with process._pdf_runtime_overrides():
        tables_module.load_agent()

    assert ("loader", str(tmp_path), "npu:0") in calls
    assert tables_module.tables_agent.device == "npu:0"
    assert tables_module.tables_agent.feature_extractor == "feature-extractor"
    assert tables_module.tables_agent.model == "table-model"


def test_pdf_runtime_overrides_rejects_cpu_table_device_in_strict_mode(monkeypatch, tmp_path):
    process = _load_process_module()

    unstructured_inference = types.ModuleType("unstructured_inference")
    models_module = types.ModuleType("unstructured_inference.models")
    tables_module = types.ModuleType("unstructured_inference.models.tables")

    class FakeTableAgent:
        model = None

    class FakeTableTransformerModel:
        initialize = lambda self, model=None, device="cpu": None

    tables_module.DEFAULT_MODEL = "old-model"
    tables_module.tables_agent = FakeTableAgent()
    tables_module.UnstructuredTableTransformerModel = FakeTableTransformerModel
    tables_module.load_agent = lambda: None
    models_module.tables = tables_module
    unstructured_inference.models = models_module
    monkeypatch.setitem(sys.modules, "unstructured_inference", unstructured_inference)
    monkeypatch.setitem(sys.modules, "unstructured_inference.models", models_module)
    monkeypatch.setitem(sys.modules, "unstructured_inference.models.tables", tables_module)
    monkeypatch.setattr(process, "PDF_TABLE_MODEL_PATH", str(tmp_path))
    monkeypatch.setattr(process, "_select_table_transformer_device", lambda: "cpu")
    monkeypatch.setenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS", "1")

    with process._pdf_runtime_overrides():
        try:
            tables_module.load_agent()
        except RuntimeError as exc:
            assert "Table transformer NPU is required" in str(exc)
        else:
            raise AssertionError("strict mode accepted CPU table transformer device")
