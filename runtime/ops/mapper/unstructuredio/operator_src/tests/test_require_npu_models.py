from pathlib import Path

import pytest

from test_pdf_npu_ocr_priority import _Element, _load_process_module


def test_pdf_require_npu_models_rejects_missing_adapters(monkeypatch):
    process = _load_process_module()

    monkeypatch.setattr(process, "partition_pdf", lambda **kwargs: [_Element("unused")])
    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: False)

    mapper = process.UnstructuredIOMapper(requireNpuModels=True)

    with pytest.raises(RuntimeError, match="NPU layout adapter is unavailable"):
        mapper._extract_pdf(Path("sample.pdf"))


def test_pdf_require_npu_models_rejects_native_ocr_fallback(monkeypatch):
    process = _load_process_module()

    monkeypatch.setattr(process, "partition_pdf", lambda **kwargs: [_Element("unused")])
    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    process._NPU_OCR_ADAPTER_STATUS.update({"attempted": True, "npu": True, "ocr": True, "error": None})
    monkeypatch.setattr(
        process,
        "_get_ocr_runtime_status",
        lambda: {"device": "npu", "native_only": True, "is_alive": False},
    )

    mapper = process.UnstructuredIOMapper(requireNpuModels=True)

    with pytest.raises(RuntimeError, match="OCR NPU runtime is unavailable"):
        mapper._extract_pdf(Path("sample.pdf"))


def test_docx_require_npu_models_uses_visual_npu_route(monkeypatch):
    process = _load_process_module()
    calls = []

    monkeypatch.setattr(process, "_convert_office_to_pdf", lambda path: Path("converted.pdf"))

    def _extract_pdf(path):
        calls.append(path)
        return [{"index": 0, "category": "Title", "text": "converted"}], "pdf-npu-ocr-hi_res"

    mapper = process.UnstructuredIOMapper(requireNpuModels=True, enableDocxFastpath=True)
    monkeypatch.setattr(mapper, "_extract_pdf", _extract_pdf)

    elements, mode = mapper._extract_elements(Path("sample.docx"), "docx")

    assert calls == [Path("converted.pdf")]
    assert elements[0]["text"] == "converted"
    assert mode == "docx-visual-pdf-npu-ocr-hi_res"


def test_docx_require_npu_models_rejects_non_npu_visual_route(monkeypatch):
    process = _load_process_module()

    monkeypatch.setattr(process, "_convert_office_to_pdf", lambda path: Path("converted.pdf"))

    mapper = process.UnstructuredIOMapper(requireNpuModels=True, enableDocxFastpath=True)
    monkeypatch.setattr(
        mapper,
        "_extract_pdf",
        lambda path: ([_Element("fallback text")], "pdf-npu-ocr-fallback-fast"),
    )

    with pytest.raises(RuntimeError, match="DOCX visual NPU route did not use NPU OCR mode"):
        mapper._extract_elements(Path("sample.docx"), "docx")


def test_docx_require_npu_models_rejects_npu_without_ocr(monkeypatch):
    process = _load_process_module()

    monkeypatch.setattr(process, "_convert_office_to_pdf", lambda path: Path("converted.pdf"))

    mapper = process.UnstructuredIOMapper(requireNpuModels=True, enableDocxFastpath=True)
    monkeypatch.setattr(
        mapper,
        "_extract_pdf",
        lambda path: ([_Element("layout only")], "pdf-npu-hi_res"),
    )

    with pytest.raises(RuntimeError, match="DOCX visual NPU route did not use NPU OCR mode"):
        mapper._extract_elements(Path("sample.docx"), "docx")


def test_docx_require_npu_models_fails_without_soffice(monkeypatch):
    process = _load_process_module()

    monkeypatch.delenv("UNSTRUCTUREDIO_LIBREOFFICE_BIN", raising=False)
    monkeypatch.setattr(process.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="LibreOffice/soffice is required"):
        process._convert_office_to_pdf(Path("sample.docx"))


def test_require_npu_models_disables_ocr_native_fallback(monkeypatch):
    process = _load_process_module()

    monkeypatch.delenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS", raising=False)
    monkeypatch.delenv("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", raising=False)

    process.UnstructuredIOMapper(requireNpuModels=True)

    assert process.os.environ["UNSTRUCTUREDIO_REQUIRE_NPU_MODELS"] == "1"
    assert process.os.environ["OCR_ADAPTER_DISABLE_NATIVE_FALLBACK"] == "1"


def test_strict_npu_ocr_runtime_requires_available_flag():
    process = _load_process_module()

    assert (
        process._is_strict_npu_ocr_runtime(
            {"device": "npu", "native_only": False, "is_alive": True, "available": False}
        )
        is False
    )


def test_apply_npu_ocr_adapters_prewarms_ocr_before_torch_npu(monkeypatch):
    process = _load_process_module()
    calls = []

    class FakeNpuAdapter:
        @staticmethod
        def apply_patches():
            calls.append("npu")

    class FakeOcrAdapter:
        @staticmethod
        def apply_ocr_patch():
            calls.append("ocr_patch")

        @staticmethod
        def get_ocr_runtime_status():
            calls.append("ocr_status")
            return {"device": "npu", "native_only": False, "is_alive": True, "available": True}

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "npu_adapter":
            return FakeNpuAdapter
        if name == "ocr_npu_adapter":
            return FakeOcrAdapter
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(process, "_configure_npu_ocr_environment", lambda: None)
    monkeypatch.setattr(process.builtins, "__import__", fake_import)
    process._NPU_OCR_ADAPTER_STATUS.update({"attempted": False, "npu": False, "ocr": False, "error": None})

    assert process._apply_npu_ocr_adapters() is True
    assert calls == ["ocr_patch", "ocr_status", "npu"]


def test_pdf_partition_is_imported_after_npu_adapters(monkeypatch):
    process = _load_process_module()
    calls = []

    class FakePdfModule:
        @staticmethod
        def partition_pdf(**kwargs):
            calls.append("partition_pdf")
            return [
                _Element("long enough text from lazy pdf partition import path one"),
                _Element("long enough text from lazy pdf partition import path two"),
                _Element("long enough text from lazy pdf partition import path three"),
            ]

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "unstructured.partition.pdf":
            calls.append("import_partition_pdf")
            return FakePdfModule
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(process, "partition_pdf", None)
    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: calls.append("adapters") or True)
    process._NPU_OCR_ADAPTER_STATUS.update({"attempted": True, "npu": True, "ocr": True, "error": None})
    monkeypatch.setattr(
        process,
        "_get_ocr_runtime_status",
        lambda: {"device": "npu", "native_only": False, "is_alive": True, "available": True},
    )
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)
    monkeypatch.setattr(process.builtins, "__import__", fake_import)

    mapper = process.UnstructuredIOMapper(requireNpuModels=True)
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert calls[:3] == ["adapters", "import_partition_pdf", "partition_pdf"]
    assert mode == "pdf-npu-ocr-hi_res"
    assert elements[0]["text"].startswith("long enough text")


def test_pdf_disables_table_structure_when_local_table_model_missing(monkeypatch):
    process = _load_process_module()
    seen_kwargs = []

    monkeypatch.setattr(process, "_apply_npu_ocr_adapters", lambda: True)
    process._NPU_OCR_ADAPTER_STATUS.update({"attempted": True, "npu": True, "ocr": True, "error": None})
    monkeypatch.setattr(
        process,
        "_get_ocr_runtime_status",
        lambda: {"device": "npu", "native_only": False, "is_alive": True, "available": True},
    )
    monkeypatch.setattr(process.Path, "exists", lambda self: False)
    monkeypatch.setattr(process, "_pdf_runtime_overrides", process.contextlib.nullcontext)

    def fake_partition_pdf(**kwargs):
        seen_kwargs.append(kwargs)
        return [
            _Element("long enough text from missing table model path one"),
            _Element("long enough text from missing table model path two"),
            _Element("long enough text from missing table model path three"),
        ]

    monkeypatch.setattr(process, "partition_pdf", fake_partition_pdf)

    mapper = process.UnstructuredIOMapper(requireNpuModels=True, pdfInferTableStructure=True)
    elements, mode = mapper._extract_pdf(Path("sample.pdf"))

    assert seen_kwargs[0]["infer_table_structure"] is False
    assert mode == "pdf-npu-ocr-hi_res"
    assert len(elements) == 3
