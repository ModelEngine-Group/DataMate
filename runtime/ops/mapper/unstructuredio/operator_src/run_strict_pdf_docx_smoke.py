from __future__ import annotations

import json
import os
import sys
import time
import types
from pathlib import Path


def _install_datamate_stub() -> None:
    if "datamate.core.base_op" in sys.modules:
        return
    datamate = types.ModuleType("datamate")
    core = types.ModuleType("datamate.core")
    base_op = types.ModuleType("datamate.core.base_op")

    class Mapper:
        def __init__(self, *args, **kwargs):
            self.filepath_key = "filepath"
            self.filetype_key = "filetype"
            self.text_key = "text"
            self.target_type_key = "target_type"

    class Operators:
        def register_module(self, *args, **kwargs):
            return None

    base_op.Mapper = Mapper
    base_op.OPERATORS = Operators()
    core.base_op = base_op
    datamate.core = core
    sys.modules["datamate"] = datamate
    sys.modules["datamate.core"] = core
    sys.modules["datamate.core.base_op"] = base_op


def _run_one(process, file_path: Path) -> dict[str, object]:
    mapper = process.UnstructuredIOMapper(requireNpuModels=True, pdfStrategy="auto")
    file_type = file_path.suffix.lstrip(".").lower()
    started = time.perf_counter()
    elements, mode = mapper._extract_elements(file_path, file_type)
    duration = round(time.perf_counter() - started, 2)
    payload = mapper._build_payload(file_path, elements, mode, duration)
    out_path = file_path.with_name(f"{file_path.stem}_strict_npu_result.json")
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "input": str(file_path),
        "output": str(out_path),
        "mode": mode,
        "duration_seconds": duration,
        "element_count": len(elements),
        "table_count": payload["table_count"],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python run_strict_pdf_docx_smoke.py <pdf-or-docx> [more-files...]", file=sys.stderr)
        return 2

    os.environ.setdefault("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS", "1")
    os.environ.setdefault("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", "1")
    os.environ.setdefault("OCR_ADAPTER_DEVICE", "npu")

    _install_datamate_stub()
    import process

    results = []
    for item in argv[1:]:
        results.append(_run_one(process, Path(item).resolve()))

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
