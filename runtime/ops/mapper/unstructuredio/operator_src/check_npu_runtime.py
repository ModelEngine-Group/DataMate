from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ASCEND_NPU_LIBRARY_PATHS = (
    "/usr/local/Ascend/nnal/asdsip/8.5.1/lib",
    "/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_0/lib",
    "/usr/local/Ascend/nnal/atb/latest/atb/cxx_abi_1/lib",
    "/usr/local/Ascend/nnal/asdsip/latest/lib",
    "/usr/local/Ascend/cann-8.5.1/lib64",
    "/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64",
    "/usr/local/Ascend/cann-8.5.1/aarch64-linux/devlib",
    "/usr/local/Ascend/cann-8.5.0/lib64",
    "/usr/local/Ascend/cann-8.5.0/aarch64-linux/lib64",
    "/usr/local/Ascend/cann-8.5.0/aarch64-linux/devlib",
    "/usr/local/Ascend/ascend-toolkit/latest/lib64",
    "/usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/lib64",
    "/usr/local/Ascend/driver/lib64",
    "/usr/local/Ascend/driver/lib64/driver",
    "/usr/local/Ascend/driver/lib64/common",
)


def _probe_env() -> dict[str, str]:
    env = dict(os.environ)
    current = [part for part in env.get("LD_LIBRARY_PATH", "").split(":") if part]
    merged: list[str] = []
    for path in list(ASCEND_NPU_LIBRARY_PATHS) + current:
        if path and os.path.exists(path) and path not in merged:
            merged.append(path)
    if merged:
        env["LD_LIBRARY_PATH"] = ":".join(merged)
    return env


def _module_version(name: str) -> dict[str, object]:
    code = (
        "import importlib, json\n"
        "try:\n"
        f"    module = importlib.import_module({name!r})\n"
        "    print(json.dumps({\n"
        "        'available': True,\n"
        "        'version': getattr(module, '__version__', getattr(module, 'VERSION', '')),\n"
        "    }, ensure_ascii=False))\n"
        "except Exception as exc:\n"
        "    print(json.dumps({'available': False, 'error': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False))\n"
        "    raise SystemExit(1)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
        env=_probe_env(),
    )
    output = (proc.stdout or "").strip().splitlines()
    if output:
        try:
            return json.loads(output[-1])
        except json.JSONDecodeError:
            pass
    error = (proc.stderr or proc.stdout or "unknown import probe failure").strip()
    return {"available": False, "error": error}


def _path_status(path: str | None) -> dict[str, object]:
    if not path:
        return {"configured": False, "exists": False}
    resolved = Path(path)
    return {"configured": True, "path": str(resolved), "exists": resolved.exists()}


def main() -> int:
    model_root = os.getenv("UNSTRUCTUREDIO_OCR_MODEL_ROOT", "/models/unstructuredio/paddleocr")
    report = {
        "python_modules": {
            "torch": _module_version("torch"),
            "torch_npu": _module_version("torch_npu"),
            "paddle": _module_version("paddle"),
            "paddleocr": _module_version("paddleocr"),
            "unstructured": _module_version("unstructured"),
            "unstructured_inference": _module_version("unstructured_inference"),
        },
        "models": {
            "yolox_pt": _path_status(
                os.getenv("UNSTRUCTUREDIO_YOLOX_MODEL_PATH", "/models/unstructuredio/yolox_l.pt")
            ),
            "yolox_src": _path_status(
                os.getenv("UNSTRUCTUREDIO_YOLOX_SRC_PATH", "/models/unstructuredio/YOLOX-main")
            ),
            "ocr_det": _path_status(
                os.getenv(
                    "UNSTRUCTUREDIO_OCR_DET_MODEL_DIR",
                    f"{model_root}/ch_PP-OCRv4_det_infer",
                )
            ),
            "ocr_rec": _path_status(
                os.getenv(
                    "UNSTRUCTUREDIO_OCR_REC_MODEL_DIR",
                    f"{model_root}/ch_PP-OCRv4_rec_infer",
                )
            ),
            "ocr_cls": _path_status(
                os.getenv(
                    "UNSTRUCTUREDIO_OCR_CLS_MODEL_DIR",
                    f"{model_root}/ch_ppocr_mobile_v2.0_cls_infer",
                )
            ),
        },
        "tools": {
            "soffice": shutil.which("soffice") or shutil.which("libreoffice"),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    required_modules = ("torch", "torch_npu", "paddle", "paddleocr", "unstructured")
    modules_ok = all(report["python_modules"][name]["available"] for name in required_modules)
    models_ok = all(item["exists"] for item in report["models"].values())
    return 0 if modules_ok and models_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
