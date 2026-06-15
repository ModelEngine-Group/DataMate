import importlib.util
import os
import sys
import types
from pathlib import Path


def _load_process_module():
    datamate = types.ModuleType("datamate")
    core = types.ModuleType("datamate.core")
    base_op = types.ModuleType("datamate.core.base_op")

    class _Mapper:
        def __init__(self, *args, **kwargs):
            self.filepath_key = "filepath"
            self.filetype_key = "filetype"
            self.text_key = "text"
            self.target_type_key = "target_type"

    base_op.Mapper = _Mapper
    core.base_op = base_op
    datamate.core = core
    sys.modules["datamate"] = datamate
    sys.modules["datamate.core"] = core
    sys.modules["datamate.core.base_op"] = base_op

    if "unstructured" not in sys.modules:
        unstructured = types.ModuleType("unstructured")
        partition = types.ModuleType("unstructured.partition")
        auto = types.ModuleType("unstructured.partition.auto")

        def _partition(*args, **kwargs):
            raise NotImplementedError("partition_auto stub should not be used in these tests")

        auto.partition = _partition
        partition.auto = auto
        unstructured.partition = partition
        sys.modules["unstructured"] = unstructured
        sys.modules["unstructured.partition"] = partition
        sys.modules["unstructured.partition.auto"] = auto

    module_path = Path(__file__).resolve().parents[1] / "process.py"
    spec = importlib.util.spec_from_file_location("unstructuredio_process_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Metadata:
    page_number = 1
    coordinates = None
    text_as_html = None


class _Element:
    category = "NarrativeText"
    metadata = _Metadata()

    def __init__(self, text):
        self.text = text


def test_process_disables_nltk_auto_download_before_unstructured_import(monkeypatch):
    monkeypatch.delenv("AUTO_DOWNLOAD_NLTK", raising=False)

    _load_process_module()

    assert os.environ["AUTO_DOWNLOAD_NLTK"] == "False"


def test_pdf_keeps_fast_result_when_auto_fallback_raises(monkeypatch):
    process = _load_process_module()
    calls = []

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process, "_get_ocr_runtime_status", lambda: {"available": False, "device": "npu"})

    def _partition_pdf(**kwargs):
        calls.append(kwargs["strategy"])
        if kwargs["strategy"] == "auto":
            raise RuntimeError("simulated auto fallback failure")
        return [_Element("x"), _Element("y"), _Element("z")]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert calls == ["fast", "auto"]
    assert mode == "pdf-npu-ocr-fallback-fast"
    assert [item["text"] for item in elements] == ["x", "y", "z"]


def test_pdf_skips_cpu_hi_res_model_fallback_even_when_cpu_ocr_exists(monkeypatch):
    process = _load_process_module()
    calls = []

    monkeypatch.delenv("UNSTRUCTUREDIO_TABLE_DEVICE", raising=False)
    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process, "_has_cpu_ocr_runtime", lambda: True)
    monkeypatch.setattr(process, "_get_ocr_runtime_status", lambda: {"available": False, "device": "npu"})

    def _partition_pdf(**kwargs):
        calls.append(
            {
                "strategy": kwargs["strategy"],
                "hi_res_model_name": kwargs.get("hi_res_model_name"),
                "table_device": process.os.environ.get("UNSTRUCTUREDIO_TABLE_DEVICE"),
            }
        )
        return [
            _Element("long enough text from fast fallback one with useful content"),
            _Element("long enough text from fast fallback two with useful content"),
            _Element("long enough text from fast fallback three with useful content"),
        ]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert calls == [{"strategy": "fast", "hi_res_model_name": None, "table_device": None}]
    assert mode == "pdf-npu-ocr-fallback-fast"
    assert len(elements) == 3


def test_pdf_skips_cpu_hi_res_when_cpu_ocr_runtime_missing(monkeypatch):
    process = _load_process_module()
    calls = []

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process, "_has_cpu_ocr_runtime", lambda: False)
    monkeypatch.setattr(process, "_get_ocr_runtime_status", lambda: {"available": False, "device": "npu"})

    def _partition_pdf(**kwargs):
        calls.append(kwargs["strategy"])
        return [
            _Element("fast text one with enough useful extracted content"),
            _Element("fast text two with enough useful extracted content"),
            _Element("fast text three with enough useful extracted content"),
        ]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert calls == ["fast"]
    assert mode == "pdf-npu-ocr-fallback-fast"
    assert len(elements) == 3


def test_pdf_runs_npu_hi_res_when_npu_ocr_is_available(monkeypatch):
    process = _load_process_module()
    seen_kwargs = []

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    process._NPU_OCR_ADAPTER_STATUS.update({"attempted": True, "npu": True, "ocr": True, "error": None})
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(
        process,
        "_get_ocr_runtime_status",
        lambda: {"available": True, "device": "npu", "native_only": False, "is_alive": True},
    )

    def _partition_pdf(**kwargs):
        seen_kwargs.append(kwargs)
        return [
            _Element("long enough npu layout text one with useful extracted content"),
            _Element("long enough npu layout text two with useful extracted content"),
            _Element("long enough npu layout text three with useful extracted content"),
        ]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert seen_kwargs[0]["strategy"] == "hi_res"
    assert seen_kwargs[0]["hi_res_model_name"] == "yolox"
    assert seen_kwargs[0]["ocr_strategy"] == "force"
    assert seen_kwargs[0]["ocr_mode"] == "entire_page"
    assert mode == "pdf-npu-ocr-hi_res"
    assert len(elements) == 3


def test_pdf_uses_fast_path_when_ocr_adapter_is_unavailable(monkeypatch):
    process = _load_process_module()
    seen_kwargs = []

    def apply_partial_adapters():
        process._NPU_OCR_ADAPTER_STATUS.update(
            {"attempted": True, "npu": True, "ocr": False, "error": "ocr unavailable"}
        )
        return False

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", apply_partial_adapters)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process, "_get_ocr_runtime_status", lambda: {"available": False})

    def _partition_pdf(**kwargs):
        seen_kwargs.append(kwargs)
        return [
            _Element("long enough npu layout text one with useful extracted content"),
            _Element("long enough npu layout text two with useful extracted content"),
            _Element("long enough npu layout text three with useful extracted content"),
        ]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert seen_kwargs[0]["strategy"] == "fast"
    assert "hi_res_model_name" not in seen_kwargs[0]
    assert "ocr_strategy" not in seen_kwargs[0]
    assert mode == "pdf-npu-ocr-fallback-fast"
    assert len(elements) == 3


def test_pdf_falls_back_when_table_caption_has_no_table(monkeypatch):
    process = _load_process_module()
    calls = []

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process, "_has_cpu_ocr_runtime", lambda: False)
    monkeypatch.setattr(process, "_get_ocr_runtime_status", lambda: {"available": True, "device": "npu", "native_only": False, "is_alive": True})

    def _partition_pdf(**kwargs):
        calls.append(kwargs["strategy"])
        if kwargs["strategy"] == "hi_res":
            return [
                _Element("Attention Is All You Need"),
                _Element(
                    "Table 3: Variations on the Transformer architecture. "
                    "This line says a table exists but the model did not return a Table element."
                ),
                _Element("long enough surrounding text with useful extracted content"),
            ]
        return [
            _Element("fast text one with enough useful extracted content"),
            _Element("Table 3: Variations  BLEU  PPL  params  25.8  4.92  65M  26.4  4.75  80M"),
            _Element("fast text three with enough useful extracted content"),
        ]

    monkeypatch.setattr(process, "partition_pdf", _partition_pdf)

    mapper = process.UnstructuredIOMapper(pdfStrategy="auto")
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert calls[:2] == ["hi_res", "fast"]
    assert mode == "pdf-npu-ocr-fallback-fast"
    assert any(item["category"] == "Table" for item in elements)


def test_pdf_table_body_heuristic_rejects_numeric_citation_paragraph():
    process = _load_process_module()

    text = (
        "Recurrent neural networks, long short-term memory [13] and gated recurrent [7] "
        "neural networks in particular, have been firmly established as state of the art "
        "approaches in sequence modeling and transduction problems such as language "
        "modeling and machine translation [35, 2, 5]. Numerous efforts have since "
        "continued to push the boundaries of recurrent language models and encoder-decoder "
        "architectures [38, 24, 15]."
    )

    assert process._looks_like_table_body(text) is False


def test_pdf_table_body_heuristic_accepts_dense_numeric_table_row():
    process = _load_process_module()

    text = (
        "PPL train steps (dev) 100K 4.92 5.29 5.00 4.91 5.01 5.16 5.01 "
        "6.11 5.19 4.88 5.75 4.66 5.12 4.75 5.77 4.95 4.67 5.47 4.92 300K 4.33"
    )

    assert process._looks_like_table_body(text) is True


def test_existing_pdf_table_gets_html_when_missing():
    process = _load_process_module()

    items = [
        {
            "category": "Table",
            "text": "Layer Type Complexity O(n) Self-Attention O(n².d)",
            "text_as_html": None,
        }
    ]

    promoted = process._promote_obvious_pdf_tables(items)

    assert promoted[0]["category"] == "Table"
    assert promoted[0]["text_as_html"].startswith("<table>")


def test_npu_mode_name_does_not_treat_cpu_ocr_as_npu(monkeypatch):
    process = _load_process_module()
    process._NPU_OCR_ADAPTER_STATUS.update({"npu": True, "ocr": True})
    monkeypatch.setattr(
        process,
        "_get_ocr_runtime_status",
        lambda: {"available": True, "device": "cpu", "native_only": False, "is_alive": True},
    )

    assert process._npu_ocr_mode_name() == "pdf-npu-hi_res"


def test_apply_adapters_prewarms_cpu_ocr_before_npu_adapter(monkeypatch):
    process = _load_process_module()
    calls = []

    fake_ocr = types.ModuleType("ocr_npu_adapter")

    def apply_ocr_patch():
        calls.append("ocr_patch")

    def prewarm_ocr_runtime():
        calls.append("ocr_prewarm")
        return {"available": True, "device": "cpu", "native_only": False, "is_alive": True}

    def get_ocr_runtime_status():
        calls.append("ocr_status")
        return {"available": True, "device": "cpu", "native_only": False, "is_alive": True}

    fake_ocr.apply_ocr_patch = apply_ocr_patch
    fake_ocr.prewarm_ocr_runtime = prewarm_ocr_runtime
    fake_ocr.get_ocr_runtime_status = get_ocr_runtime_status

    fake_npu = types.ModuleType("npu_adapter")

    def apply_patches():
        calls.append("npu_patch")

    fake_npu.apply_patches = apply_patches

    monkeypatch.setitem(sys.modules, "ocr_npu_adapter", fake_ocr)
    monkeypatch.setitem(sys.modules, "npu_adapter", fake_npu)
    monkeypatch.setenv("UNSTRUCTUREDIO_OCR_DEVICE", "cpu")
    monkeypatch.setenv("OCR_ADAPTER_FORCE_PADDLE_CPU", "1")
    monkeypatch.setenv("UNSTRUCTUREDIO_ENABLE_CPU_OCR_FALLBACK", "1")

    assert process._apply_npu_ocr_adapters() is True
    assert calls == ["ocr_patch", "ocr_prewarm", "npu_patch"]
    assert process._NPU_OCR_ADAPTER_STATUS["ocr"] is True
    assert process._NPU_OCR_ADAPTER_STATUS["npu"] is True


def test_apply_adapters_does_not_prewarm_default_npu_ocr(monkeypatch):
    process = _load_process_module()
    calls = []

    fake_ocr = types.ModuleType("ocr_npu_adapter")
    fake_ocr.apply_ocr_patch = lambda: calls.append("ocr_patch")
    fake_ocr.prewarm_ocr_runtime = lambda: calls.append("ocr_prewarm")
    fake_ocr.get_ocr_runtime_status = lambda: {"available": False, "device": "npu"}

    fake_npu = types.ModuleType("npu_adapter")
    fake_npu.apply_patches = lambda: calls.append("npu_patch")

    monkeypatch.setitem(sys.modules, "ocr_npu_adapter", fake_ocr)
    monkeypatch.setitem(sys.modules, "npu_adapter", fake_npu)
    monkeypatch.delenv("UNSTRUCTUREDIO_OCR_DEVICE", raising=False)
    monkeypatch.delenv("OCR_ADAPTER_DEVICE", raising=False)

    assert process._apply_npu_ocr_adapters() is True
    assert calls == ["ocr_patch", "npu_patch"]


def test_configure_npu_ocr_environment_overrides_cpu_ocr_request(monkeypatch):
    process = _load_process_module()

    monkeypatch.setenv("UNSTRUCTUREDIO_OCR_DEVICE", "cpu")
    monkeypatch.setenv("OCR_ADAPTER_DEVICE", "cpu")
    monkeypatch.setenv("OCR_ADAPTER_FORCE_PADDLE_CPU", "1")
    monkeypatch.delenv("UNSTRUCTUREDIO_ENABLE_CPU_OCR_FALLBACK", raising=False)
    monkeypatch.setattr(process, "_prepend_existing_sys_path", lambda path: None)
    monkeypatch.setattr(process, "_configure_ascend_runtime_environment", lambda: None)

    process._configure_npu_ocr_environment()

    assert process.os.environ["OCR_ADAPTER_DEVICE"] == "npu"
    assert process.os.environ["OCR_ADAPTER_DISABLE_NATIVE_FALLBACK"] == "1"
