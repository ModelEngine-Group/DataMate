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
        base_op.OPERATORS = []
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
            raise NotImplementedError("partition stub should not be used in docx fastpath checks")

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


def main():
    process = _load_process_module()
    base = Path(__file__).resolve().parents[2] / "test_cases" / "example_input"
    samples = [
        "docx_corpus_sample_1.docx",
        "docx_corpus_sample_2.docx",
    ]
    failures = []
    for sample in samples:
        elements = process._extract_docx_fastpath(base / sample)
        if not elements:
            failures.append(f"{sample}: no elements")
            continue
        if not any(item.get("coordinates") for item in elements):
            failures.append(f"{sample}: all coordinates are null")
        if not all(item.get("page_number") is not None for item in elements):
            failures.append(f"{sample}: contains null page_number")

    if failures:
        raise SystemExit("\n".join(failures))

    print("docx fastpath coordinate checks passed")


if __name__ == "__main__":
    main()
