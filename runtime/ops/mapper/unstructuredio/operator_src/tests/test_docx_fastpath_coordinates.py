import importlib.util
import sys
import types
from pathlib import Path


def _load_process_module():
    if "datamate" not in sys.modules:
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
            raise NotImplementedError("partition stub should not be used in docx fastpath tests")

        auto.partition = _partition
        partition.auto = auto
        unstructured.partition = partition
        sys.modules["unstructured"] = unstructured
        sys.modules["unstructured.partition"] = partition
        sys.modules["unstructured.partition.auto"] = auto

    module_path = Path(__file__).resolve().parents[1] / "process.py"
    spec = importlib.util.spec_from_file_location("unstructuredio_process", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


process = _load_process_module()
TEST_INPUT_DIR = Path(__file__).resolve().parents[2] / "test_cases" / "example_input"


def _extract(sample_name: str):
    return process._extract_docx_fastpath(TEST_INPUT_DIR / sample_name)


def test_docx_corpus_sample_1_coordinates_are_not_all_null():
    elements = _extract("docx_corpus_sample_1.docx")

    assert elements
    assert any(item.get("coordinates") for item in elements)
    assert all(item.get("page_number") is not None for item in elements)


def test_docx_corpus_sample_2_coordinates_are_not_all_null():
    elements = _extract("docx_corpus_sample_2.docx")

    assert elements
    assert any(item.get("coordinates") for item in elements)
    assert any(item.get("category") == "Table" for item in elements)
