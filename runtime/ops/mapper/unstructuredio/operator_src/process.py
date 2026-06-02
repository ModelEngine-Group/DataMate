from __future__ import annotations

import builtins
import contextlib
import html
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable


def _nltk_path_has_bad_zip(path: str | Path) -> bool:
    root = Path(path)
    if not root.exists():
        return False
    for zip_path in root.rglob("*.zip"):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.testzip()
        except zipfile.BadZipFile:
            return True
        except OSError:
            continue
    return False


def _configure_nltk_import_environment() -> None:
    # Avoid import-time downloads and corrupted global NLTK caches blocking PDF partition.
    os.environ.setdefault("AUTO_DOWNLOAD_NLTK", "False")
    preferred_paths = [
        os.getenv("UNSTRUCTUREDIO_NLTK_DATA", ""),
        "/models/unstructuredio/nltk_data",
        "/model/unstructuredio/nltk_data",
    ]
    for preferred in preferred_paths:
        if preferred and Path(preferred).exists() and not _nltk_path_has_bad_zip(preferred):
            os.environ["NLTK_DATA"] = preferred
            break


_configure_nltk_import_environment()

from datamate.core.base_op import Mapper
from unstructured.partition.auto import partition as partition_auto

try:
    from unstructured.partition.doc import partition_doc
except ImportError:
    partition_doc = None

partition_pdf = None

try:
    from docx import Document
    from docx.document import Document as DocxDocument
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table as DocxTable
    from docx.text.paragraph import Paragraph
except ImportError:
    Document = None
    DocxDocument = None
    CT_Tbl = None
    CT_P = None
    DocxTable = None
    Paragraph = None


logger = logging.getLogger(__name__)
OPERATOR_DIR = Path(__file__).resolve().parent
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PDF_LAYOUT_MODEL_PATH = os.getenv(
    "UNSTRUCTUREDIO_LAYOUT_MODEL_PATH",
    "/models/unstructuredio/yolo_x_layout/yolox_l0.05.onnx",
)
PDF_TABLE_MODEL_PATH = os.getenv(
    "UNSTRUCTUREDIO_TABLE_MODEL_PATH",
    "/models/unstructuredio/table-transformer-structure-recognition",
)
ADAPTERS_DIR = OPERATOR_DIR / "adapters"
DEFAULT_YOLOX_MODEL_PATH = os.getenv(
    "UNSTRUCTUREDIO_YOLOX_MODEL_PATH",
    "/models/unstructuredio/yolox_l.pt",
)
DEFAULT_OCR_MODEL_ROOT = os.getenv(
    "UNSTRUCTUREDIO_OCR_MODEL_ROOT",
    "/models/unstructuredio/paddleocr",
)
DEFAULT_OCR_DET_MODEL_DIR = os.getenv(
    "UNSTRUCTUREDIO_OCR_DET_MODEL_DIR",
    f"{DEFAULT_OCR_MODEL_ROOT}/ch_PP-OCRv4_det_infer",
)
DEFAULT_OCR_REC_MODEL_DIR = os.getenv(
    "UNSTRUCTUREDIO_OCR_REC_MODEL_DIR",
    f"{DEFAULT_OCR_MODEL_ROOT}/ch_PP-OCRv4_rec_infer",
)
DEFAULT_OCR_CLS_MODEL_DIR = os.getenv(
    "UNSTRUCTUREDIO_OCR_CLS_MODEL_DIR",
    f"{DEFAULT_OCR_MODEL_ROOT}/ch_ppocr_mobile_v2.0_cls_infer",
)
DEFAULT_YOLOX_SRC_PATHS = [
    os.getenv("UNSTRUCTUREDIO_YOLOX_SRC_PATH", ""),
    str(ADAPTERS_DIR / "YOLOX-main"),
    str(OPERATOR_DIR / "YOLOX-main"),
    "/models/unstructuredio/YOLOX-main",
]
IMAGE_PARTITION_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "bmp"}
DOCX_COORDINATE_WIDTH = 1224
DOCX_COORDINATE_HEIGHT = 1584
DOCX_LEFT_MARGIN = 96
DOCX_TOP_MARGIN = 72
DOCX_CONTENT_WIDTH = DOCX_COORDINATE_WIDTH - DOCX_LEFT_MARGIN * 2
DOCX_BOTTOM_MARGIN = 96
YOLOX_LABEL_MAP = {
    0: "Caption",
    1: "Footnote",
    2: "Formula",
    3: "ListItem",
    4: "PageFooter",
    5: "PageHeader",
    6: "Picture",
    7: "SectionHeader",
    8: "Table",
    9: "Text",
    10: "Title",
}
_NPU_OCR_ADAPTER_STATUS = {
    "attempted": False,
    "npu": False,
    "ocr": False,
    "error": None,
}
ASCEND_NPU_LIBRARY_PATHS = [
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
]


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_language_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        languages = [part for part in parts if part]
        return languages or list(default)
    if isinstance(value, (list, tuple, set)):
        languages = [str(item).strip() for item in value if str(item).strip()]
        return languages or list(default)
    return list(default)


def _cpu_ocr_fallback_enabled() -> bool:
    return _as_bool(os.getenv("UNSTRUCTUREDIO_ENABLE_CPU_OCR_FALLBACK"), False)


def _prepend_existing_sys_path(path: str | Path | None) -> None:
    if not path:
        return
    resolved = Path(path)
    if not resolved.exists():
        return
    path_text = str(resolved)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


def _configure_npu_ocr_environment() -> None:
    _prepend_existing_sys_path(ADAPTERS_DIR)
    for candidate in DEFAULT_YOLOX_SRC_PATHS:
        _prepend_existing_sys_path(candidate)

    os.environ.setdefault("CUSTOM_DEVICE_ROOT", "/tmp/block_paddle_npu_in_main_process")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("NPU_ADAPTER_YOLOX_MODEL_PATH", DEFAULT_YOLOX_MODEL_PATH)
    if _cpu_ocr_fallback_enabled():
        os.environ.setdefault("OCR_ADAPTER_DEVICE", os.getenv("UNSTRUCTUREDIO_OCR_DEVICE", "npu"))
    else:
        os.environ["OCR_ADAPTER_DEVICE"] = "npu"
        os.environ.setdefault("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", "1")
        os.environ["OCR_ADAPTER_INIT_TIMEOUT"] = os.getenv("UNSTRUCTUREDIO_OCR_NPU_PROBE_TIMEOUT", "20")
    os.environ.setdefault("OCR_ADAPTER_INIT_TIMEOUT", "300")
    os.environ.setdefault("OCR_ADAPTER_REQUEST_TIMEOUT", "180")
    os.environ.setdefault("OCR_ADAPTER_LANG", "ch")
    os.environ.setdefault("OCR_ADAPTER_MODEL_ROOT", DEFAULT_OCR_MODEL_ROOT)
    _configure_ascend_runtime_environment()
    if _as_bool(os.getenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS"), False):
        os.environ.setdefault("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", "1")
    if Path(DEFAULT_OCR_DET_MODEL_DIR).exists():
        os.environ.setdefault("OCR_ADAPTER_TEXT_DET_MODEL_DIR", DEFAULT_OCR_DET_MODEL_DIR)
    if Path(DEFAULT_OCR_REC_MODEL_DIR).exists():
        os.environ.setdefault("OCR_ADAPTER_TEXT_REC_MODEL_DIR", DEFAULT_OCR_REC_MODEL_DIR)
    if Path(DEFAULT_OCR_CLS_MODEL_DIR).exists():
        os.environ.setdefault("OCR_ADAPTER_TEXT_CLS_MODEL_DIR", DEFAULT_OCR_CLS_MODEL_DIR)


def _prepend_ld_library_paths(paths: list[str]) -> None:
    existing = [part for part in os.environ.get("LD_LIBRARY_PATH", "").split(":") if part]
    merged: list[str] = []
    for path in paths + existing:
        if path and os.path.exists(path) and path not in merged:
            merged.append(path)
    if merged:
        os.environ["LD_LIBRARY_PATH"] = ":".join(merged)


def _configure_ascend_runtime_environment() -> None:
    os.environ.setdefault("FLAGS_npu_jit_compile", "0")
    _prepend_ld_library_paths(ASCEND_NPU_LIBRARY_PATHS)


def _apply_npu_ocr_adapters() -> bool:
    if _NPU_OCR_ADAPTER_STATUS["attempted"]:
        return bool(_NPU_OCR_ADAPTER_STATUS["npu"] and _NPU_OCR_ADAPTER_STATUS["ocr"])

    _NPU_OCR_ADAPTER_STATUS["attempted"] = True
    _configure_npu_ocr_environment()

    errors: list[str] = []
    try:
        import ocr_npu_adapter  # type: ignore

        ocr_npu_adapter.apply_ocr_patch()
        if _should_prewarm_cpu_ocr_runtime() and hasattr(ocr_npu_adapter, "prewarm_ocr_runtime"):
            status = ocr_npu_adapter.prewarm_ocr_runtime()
            if not _is_cpu_paddle_ocr_runtime(status):
                raise RuntimeError(f"CPU PaddleOCR runtime is unavailable: {status}")
        if _as_bool(os.getenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS"), False):
            status = ocr_npu_adapter.get_ocr_runtime_status()
            if not _is_strict_npu_ocr_runtime(status):
                raise RuntimeError(f"OCR NPU runtime is unavailable: {status}")
        _NPU_OCR_ADAPTER_STATUS["ocr"] = True
    except Exception as exc:
        errors.append(f"ocr_npu_adapter: {exc}")
        logger.warning("OCR adapter unavailable, will use fallback OCR path: %s", exc)

    try:
        import npu_adapter  # type: ignore

        npu_adapter.apply_patches()
        _NPU_OCR_ADAPTER_STATUS["npu"] = True
    except Exception as exc:
        errors.append(f"npu_adapter: {exc}")
        logger.warning("NPU adapter unavailable, will use fallback path: %s", exc)

    _NPU_OCR_ADAPTER_STATUS["error"] = "; ".join(errors) if errors else None
    return bool(_NPU_OCR_ADAPTER_STATUS["npu"] and _NPU_OCR_ADAPTER_STATUS["ocr"])


def _should_prewarm_cpu_ocr_runtime() -> bool:
    if not _cpu_ocr_fallback_enabled():
        return False
    requested_device = (
        os.getenv("UNSTRUCTUREDIO_OCR_DEVICE")
        or os.getenv("OCR_ADAPTER_DEVICE")
        or ""
    ).strip().lower()
    return requested_device == "cpu" and _as_bool(os.getenv("OCR_ADAPTER_FORCE_PADDLE_CPU"), False)


def _get_partition_pdf():
    global partition_pdf
    if partition_pdf is not None:
        return partition_pdf
    try:
        from unstructured.partition.pdf import partition_pdf as loaded_partition_pdf
    except ImportError:
        return None
    partition_pdf = loaded_partition_pdf
    return partition_pdf


def _get_ocr_runtime_status() -> dict[str, Any]:
    try:
        import ocr_npu_adapter  # type: ignore

        if hasattr(ocr_npu_adapter, "get_ocr_runtime_status"):
            status = ocr_npu_adapter.get_ocr_runtime_status()
            if isinstance(status, dict):
                return status
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {"available": False, "error": "ocr runtime status is unavailable"}


def _is_strict_npu_ocr_runtime(status: dict[str, Any]) -> bool:
    return (
        str(status.get("device") or "").lower() == "npu"
        and bool(status.get("available"))
        and bool(status.get("is_alive"))
        and not bool(status.get("native_only"))
    )


def _can_run_npu_ocr(status: dict[str, Any]) -> bool:
    return _is_strict_npu_ocr_runtime(status)


def _is_cpu_paddle_ocr_runtime(status: dict[str, Any]) -> bool:
    return (
        str(status.get("device") or "").lower() == "cpu"
        and bool(status.get("available"))
        and bool(status.get("is_alive"))
        and not bool(status.get("native_only"))
    )


def _npu_ocr_mode_name() -> str:
    if _NPU_OCR_ADAPTER_STATUS["npu"] and _NPU_OCR_ADAPTER_STATUS["ocr"]:
        status = _get_ocr_runtime_status()
        if _can_run_npu_ocr(status):
            return "pdf-npu-ocr-hi_res"
        return "pdf-npu-hi_res"
    if _NPU_OCR_ADAPTER_STATUS["npu"]:
        return "pdf-npu-hi_res"
    if _NPU_OCR_ADAPTER_STATUS["ocr"]:
        return "pdf-ocr-adapter-hi_res"
    return "pdf-hi_res"


def _can_infer_pdf_table_structure(requested: bool) -> bool:
    if not requested:
        return False
    return Path(PDF_TABLE_MODEL_PATH).exists()


def _has_cpu_ocr_runtime() -> bool:
    return bool(
        importlib.util.find_spec("unstructured_pytesseract")
        or importlib.util.find_spec("pytesseract")
    )


def _select_table_transformer_device() -> str:
    requested = os.getenv("UNSTRUCTUREDIO_TABLE_DEVICE")
    if requested:
        return requested
    _configure_ascend_runtime_environment()
    try:
        import torch
        import torch_npu  # noqa: F401

        if torch.npu.is_available():
            return "npu:0"
    except Exception as exc:
        logger.warning("Table transformer NPU unavailable, falling back to CPU: %s", exc)
    return "cpu"


def _load_local_table_transformer_model(model_path: str | Path, device: str):
    model_dir = Path(model_path)
    from transformers import (
        DetrImageProcessor,
        TableTransformerConfig,
        TableTransformerForObjectDetection,
    )

    feature_extractor = DetrImageProcessor.from_pretrained(model_dir, local_files_only=True)
    config = TableTransformerConfig.from_pretrained(model_dir, local_files_only=True)
    config.use_pretrained_backbone = False
    model = TableTransformerForObjectDetection(config)

    safetensors_path = model_dir / "model.safetensors"
    pytorch_path = model_dir / "pytorch_model.bin"
    if safetensors_path.exists():
        from safetensors.torch import load_file as load_safetensors

        state_dict = load_safetensors(str(safetensors_path), device="cpu")
    elif pytorch_path.exists():
        import torch

        state_dict = torch.load(pytorch_path, map_location="cpu")
    else:
        raise FileNotFoundError(
            f"Missing table transformer weights under {model_dir}: "
            "expected model.safetensors or pytorch_model.bin"
        )

    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing or unexpected:
        logger.warning(
            "Loaded table transformer with missing keys=%s unexpected keys=%s",
            len(missing),
            len(unexpected),
        )
    model.eval()
    model = model.to(device)
    return feature_extractor, model


def _render_txt(elements: Iterable[Dict[str, Any]]) -> str:
    sections = []
    for item in elements:
        sections.append(f"[{item['index']}] [{item['category']}] {item['text']}".rstrip())
        if item.get("text_as_html"):
            sections.append(f"HTML: {item['text_as_html']}")
    return "\n\n".join(sections)


@contextlib.contextmanager
def _pdf_runtime_overrides():
    temp_json_path = None
    env_backup = {
        "UNSTRUCTURED_DEFAULT_MODEL_INITIALIZE_PARAMS_JSON_PATH": os.environ.get(
            "UNSTRUCTURED_DEFAULT_MODEL_INITIALIZE_PARAMS_JSON_PATH"
        ),
        "UNSTRUCTURED_HI_RES_MODEL_NAME": os.environ.get("UNSTRUCTURED_HI_RES_MODEL_NAME"),
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
    }
    tables_module = None
    default_table_model = None
    original_load_agent = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", delete=False
        ) as handle:
            json.dump({"model_path": PDF_LAYOUT_MODEL_PATH, "label_map": YOLOX_LABEL_MAP}, handle)
            temp_json_path = handle.name

        os.environ["UNSTRUCTURED_DEFAULT_MODEL_INITIALIZE_PARAMS_JSON_PATH"] = temp_json_path
        os.environ["UNSTRUCTURED_HI_RES_MODEL_NAME"] = "yolox"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        try:
            from unstructured_inference.models import tables as tables_module  # type: ignore

            default_table_model = getattr(tables_module, "DEFAULT_MODEL", None)
            original_load_agent = getattr(tables_module, "load_agent", None)
            original_initialize = getattr(tables_module.UnstructuredTableTransformerModel, "initialize", None)
            if default_table_model is not None:
                tables_module.DEFAULT_MODEL = PDF_TABLE_MODEL_PATH
            if callable(original_load_agent):
                def _initialize_table_model_local(self, model=None, device=None):
                    selected_device = device or _select_table_transformer_device()
                    self.device = selected_device
                    self.feature_extractor, self.model = _load_local_table_transformer_model(
                        model or PDF_TABLE_MODEL_PATH,
                        selected_device,
                    )

                def _initialize_table_model_with_fallback(self, model=None, device=None):
                    selected_device = device or _select_table_transformer_device()
                    strict_npu = _as_bool(os.getenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS"), False)
                    if strict_npu and selected_device == "cpu":
                        raise RuntimeError("Table transformer NPU is required but unavailable")
                    try:
                        _initialize_table_model_local(self, model=model, device=selected_device)
                    except Exception:
                        if strict_npu:
                            raise
                        if selected_device == "cpu":
                            raise
                        logger.warning(
                            "Unable to initialize table transformer on NPU, falling back to CPU",
                            exc_info=True,
                        )
                        _initialize_table_model_local(self, model=model, device="cpu")

                def _load_agent_with_local_model():
                    if getattr(tables_module.tables_agent, "model", None) is None:
                        _initialize_table_model_with_fallback(
                            tables_module.tables_agent,
                            PDF_TABLE_MODEL_PATH,
                            device=_select_table_transformer_device(),
                        )

                if original_initialize is not None:
                    tables_module.UnstructuredTableTransformerModel.initialize = (
                        _initialize_table_model_with_fallback
                    )
                tables_module.load_agent = _load_agent_with_local_model
        except Exception as exc:
            logger.warning("Unable to override unstructured table model path: %s", exc)

        yield
    finally:
        if tables_module is not None:
            if default_table_model is not None:
                tables_module.DEFAULT_MODEL = default_table_model
            if original_load_agent is not None:
                tables_module.load_agent = original_load_agent
            if "original_initialize" in locals() and original_initialize is not None:
                tables_module.UnstructuredTableTransformerModel.initialize = original_initialize
        for key, value in env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if temp_json_path:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temp_json_path)


def _element_to_dict(index: int, element: Any) -> Dict[str, Any]:
    metadata = getattr(element, "metadata", None)
    coordinates = getattr(metadata, "coordinates", None) if metadata else None
    text = getattr(element, "text", None)
    if text is None:
        with contextlib.suppress(Exception):
            text = str(element)
    if text is None:
        text = ""
    return {
        "index": index,
        "category": getattr(element, "category", element.__class__.__name__),
        "text": str(text),
        "page_number": getattr(metadata, "page_number", None) if metadata else None,
        "coordinates": str(coordinates) if coordinates is not None else None,
        "text_as_html": getattr(metadata, "text_as_html", None) if metadata else None,
    }


def _serialize_elements(elements: Iterable[Any]) -> list[Dict[str, Any]]:
    return [_element_to_dict(index, element) for index, element in enumerate(elements)]


def _looks_like_rotated_margin_noise(text: str) -> bool:
    compact = text.replace(" ", "")
    if len(compact) < 4:
        return False
    tokens = text.split()
    if len(tokens) < 4:
        return False
    alnum_chars = [ch for ch in compact if ch.isalnum()]
    if len(alnum_chars) < 3:
        return False
    single_char_ratio = sum(1 for token in tokens if len(token) == 1) / max(len(tokens), 1)
    unique_ratio = len(set(compact.lower())) / max(len(compact), 1)
    alpha_num_ratio = sum(1 for ch in compact if ch.isalnum()) / max(len(compact), 1)
    has_word = any(len(token) >= 4 and token.isalpha() for token in tokens)
    long_token_count = sum(1 for token in tokens if len(token) >= 2)
    return (
        not has_word
        and single_char_ratio >= 0.6
        and unique_ratio >= 0.5
        and alpha_num_ratio >= 0.45
        and long_token_count <= 1
    )


def _looks_like_left_margin_strip(coordinates: str | None) -> bool:
    if not coordinates:
        return False
    return "PixelSpace" in coordinates and "((" in coordinates


def _filter_obvious_pdf_noise(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    filtered = []
    for item in items:
        if item.get("page_number") != 1:
            filtered.append(item)
            continue
        text = str(item.get("text") or "").strip()
        if not _looks_like_rotated_margin_noise(text):
            filtered.append(item)
            continue
        if not _looks_like_left_margin_strip(item.get("coordinates")):
            filtered.append(item)
            continue
    return filtered


_PDF_TABLE_CAPTION_RE = re.compile(r"^\s*Table\s+\d+\s*:", re.IGNORECASE)


def _looks_like_table_caption(text: str) -> bool:
    return bool(_PDF_TABLE_CAPTION_RE.match(text or ""))


def _looks_like_table_body(text: str) -> bool:
    normalized = " ".join((text or "").split())
    if len(normalized) < 30:
        return False
    citation_stripped = re.sub(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]", " ", normalized)
    numeric_tokens = re.findall(r"(?<!\w)[+-]?\d+(?:\.\d+)?(?:[KkMm%])?(?!\w)", citation_stripped)
    alpha_tokens = re.findall(r"[A-Za-z]{2,}", normalized)
    if len(numeric_tokens) < 8 or len(alpha_tokens) < 3:
        return False
    numeric_density = len(numeric_tokens) / max(len(alpha_tokens), 1)
    return numeric_density >= 0.45


def _table_text_to_html(text: str) -> str:
    rows = []
    for line in (text or "").splitlines():
        cells = [cell for cell in re.split(r"\s{2,}|\t+", line.strip()) if cell]
        if not cells and line.strip():
            cells = [line.strip()]
        if cells:
            rows.append(cells)
    if not rows:
        rows = [[(text or "").strip()]]
    rendered_rows = []
    for row_index, row in enumerate(rows):
        tag = "th" if row_index == 0 else "td"
        rendered_rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in row) + "</tr>")
    return "<table>\n" + "\n".join(rendered_rows) + "\n</table>"


def _promote_obvious_pdf_tables(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    promoted = []
    for item in items:
        text = str(item.get("text") or "").strip()
        if item.get("category") == "Table" and text and not item.get("text_as_html"):
            item = dict(item)
            item["text_as_html"] = _table_text_to_html(text)
        elif item.get("category") != "Table" and (
            _looks_like_table_caption(text) or _looks_like_table_body(text)
        ):
            item = dict(item)
            item["category"] = "Table"
            if not item.get("text_as_html"):
                item["text_as_html"] = _table_text_to_html(text)
        promoted.append(item)
    return promoted


def _has_table_reference(items: list[Dict[str, Any]]) -> bool:
    return any(_looks_like_table_caption(str(item.get("text") or "").strip()) for item in items)


def _merge_pdf_table_supplements(
    base_items: list[Dict[str, Any]],
    supplement_items: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    if any(item.get("category") == "Table" for item in base_items):
        return base_items
    existing_texts = {" ".join(str(item.get("text") or "").split()).lower() for item in base_items}
    merged = list(base_items)
    for item in supplement_items:
        if item.get("category") != "Table":
            continue
        normalized = " ".join(str(item.get("text") or "").split()).lower()
        if not normalized or normalized in existing_texts:
            continue
        table_item = dict(item)
        table_item["index"] = len(merged)
        merged.append(table_item)
        existing_texts.add(normalized)
    return merged


def _normalize_paragraph_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _classify_paragraph(text: str, index: int, paragraph: Paragraph) -> str:
    compact = text.strip()
    if not compact:
        return "NarrativeText"

    style_name = ""
    try:
        style_name = (paragraph.style.name or "").lower()
    except Exception:
        style_name = ""

    if style_name.startswith("heading") or "title" in style_name:
        return "Title"
    if compact.isupper() and len(compact) > 20:
        return "UncategorizedText"
    if compact.lower().startswith("date:"):
        return "UncategorizedText"
    if index == 0 and len(compact) <= 80:
        return "Title"
    if len(compact) <= 60 and compact.count(".") <= 1:
        return "Title"
    return "NarrativeText"


def _iter_block_items(parent: DocxDocument):
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield DocxTable(child, parent)


def _iter_paragraph_chunks(paragraph: Paragraph):
    text_parts: list[str] = []
    for node in paragraph._element.iter():
        tag = node.tag
        if tag == f"{W_NS}t":
            text_parts.append(node.text or "")
            continue
        if tag == f"{W_NS}tab":
            text_parts.append("\t")
            continue
        if tag == f"{W_NS}br" and node.get(f"{W_NS}type") == "page":
            text = _normalize_paragraph_text("".join(text_parts))
            if text:
                yield "text", text
            yield "page_break", ""
            text_parts = []
            continue
        if tag == f"{W_NS}lastRenderedPageBreak":
            text = _normalize_paragraph_text("".join(text_parts))
            if text:
                yield "text", text
            yield "page_break", ""
            text_parts = []
    tail_text = _normalize_paragraph_text("".join(text_parts))
    if tail_text:
        yield "text", tail_text


def _table_rows(table: DocxTable) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        rows.append([_normalize_paragraph_text(cell.text) for cell in row.cells])
    return rows


def _table_to_text(rows: list[list[str]]) -> str:
    rendered_rows = []
    for row in rows:
        rendered_rows.append("  ".join(cell for cell in row if cell))
    return "\n".join(row for row in rendered_rows if row.strip())


def _table_to_html(rows: list[list[str]]) -> str | None:
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return None
    head_html = "".join(f"<th>{html.escape(cell)}</th>" for cell in rows[0])
    if len(rows) == 1:
        return f"<table>\n<thead>\n<tr>{head_html}</tr>\n</thead>\n</table>"
    body_rows = []
    for row in rows[1:]:
        body_rows.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>")
    return (
        "<table>\n<thead>\n<tr>"
        + head_html
        + "</tr>\n</thead>\n<tbody>\n"
        + "\n".join(body_rows)
        + "\n</tbody>\n</table>"
    )


def _docx_coordinate_string(left: int, top: int, right: int, bottom: int) -> str:
    points = (
        (float(left), float(top)),
        (float(left), float(bottom)),
        (float(right), float(bottom)),
        (float(right), float(top)),
    )
    return (
        "CoordinatesMetadata("
        f"points={points}, "
        f"system=PixelSpace(width={DOCX_COORDINATE_WIDTH}, height={DOCX_COORDINATE_HEIGHT})"
        ")"
    )


def _estimate_docx_block_height(category: str, text: str, table_rows: int = 0) -> int:
    normalized = (text or "").strip()
    char_count = len(normalized)
    line_count = max(1, sum(1 for line in normalized.splitlines() if line.strip()))
    if category == "Table":
        return max(72, 28 * max(table_rows, line_count))
    if category == "Title":
        return min(140, 34 + line_count * 20 + char_count // 18)
    if category == "UncategorizedText":
        return min(110, 28 + line_count * 18 + char_count // 24)
    return min(160, 26 + line_count * 18 + char_count // 26)


def _estimate_docx_block_width(category: str, text: str) -> int:
    normalized = (text or "").strip()
    if category == "Table":
        return DOCX_CONTENT_WIDTH
    if category == "Title":
        return min(DOCX_CONTENT_WIDTH, max(320, len(normalized) * 9))
    return min(DOCX_CONTENT_WIDTH, max(280, len(normalized) * 8))


def _assign_docx_coordinates(
    *,
    page_number: int,
    category: str,
    text: str,
    page_offsets: dict[int, int],
    table_rows: int = 0,
) -> str:
    current_top = page_offsets.get(page_number, DOCX_TOP_MARGIN)
    height = _estimate_docx_block_height(category, text, table_rows=table_rows)
    max_top = DOCX_COORDINATE_HEIGHT - DOCX_BOTTOM_MARGIN - height
    top = min(current_top, max_top)
    if top < DOCX_TOP_MARGIN:
        top = DOCX_TOP_MARGIN
    bottom = min(DOCX_COORDINATE_HEIGHT - DOCX_BOTTOM_MARGIN, top + height)
    width = _estimate_docx_block_width(category, text)
    right = min(DOCX_COORDINATE_WIDTH - DOCX_LEFT_MARGIN, DOCX_LEFT_MARGIN + width)
    page_offsets[page_number] = bottom + 16
    return _docx_coordinate_string(DOCX_LEFT_MARGIN, top, right, bottom)


def _extract_docx_fastpath(file_path: Path) -> list[Dict[str, Any]]:
    if Document is None:
        return []
    document = Document(str(file_path))
    elements: list[Dict[str, Any]] = []
    current_page = 1
    paragraph_index = 0
    page_offsets: dict[int, int] = {}
    for block in _iter_block_items(document):
        if isinstance(block, Paragraph):
            for chunk_type, chunk_text in _iter_paragraph_chunks(block):
                if chunk_type == "page_break":
                    current_page += 1
                    continue
                elements.append(
                    {
                        "index": len(elements),
                        "category": _classify_paragraph(chunk_text, paragraph_index, block),
                        "text": chunk_text,
                        "page_number": current_page,
                        "coordinates": _assign_docx_coordinates(
                            page_number=current_page,
                            category=_classify_paragraph(chunk_text, paragraph_index, block),
                            text=chunk_text,
                            page_offsets=page_offsets,
                        ),
                        "text_as_html": None,
                    }
                )
                paragraph_index += 1
            continue
        if isinstance(block, DocxTable):
            rows = _table_rows(block)
            table_text = _table_to_text(rows)
            if not table_text:
                continue
            elements.append(
                {
                    "index": len(elements),
                    "category": "Table",
                    "text": table_text,
                    "page_number": current_page,
                    "coordinates": _assign_docx_coordinates(
                        page_number=current_page,
                        category="Table",
                        text=table_text,
                        page_offsets=page_offsets,
                        table_rows=len(rows),
                    ),
                    "text_as_html": _table_to_html(rows),
                }
            )
    return elements


def _convert_office_to_pdf(file_path: Path) -> Path:
    soffice = (
        os.getenv("UNSTRUCTUREDIO_LIBREOFFICE_BIN")
        or shutil.which("libreoffice")
        or shutil.which("soffice")
    )
    if not soffice:
        raise RuntimeError("LibreOffice/soffice is required for DOCX/DOC visual NPU extraction")

    output_dir = Path(tempfile.mkdtemp(prefix="unstructuredio_office_pdf_"))
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(file_path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"Office to PDF conversion failed: {message}")

    converted = output_dir / f"{file_path.stem}.pdf"
    if not converted.exists():
        candidates = sorted(output_dir.glob("*.pdf"))
        if not candidates:
            raise RuntimeError("Office to PDF conversion did not produce a PDF")
        converted = candidates[0]
    return converted


class UnstructuredIOMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.export_type = str(kwargs.get("exportType", "json") or "json").strip().lower()
        self.pdf_strategy = str(kwargs.get("pdfStrategy", "auto") or "auto").strip().lower()
        self.pdf_infer_table_structure = _as_bool(kwargs.get("pdfInferTableStructure", True), True)
        self.enable_docx_fastpath = _as_bool(kwargs.get("enableDocxFastpath", True), True)
        self.suppress_pdf_noise = _as_bool(kwargs.get("suppressPdfNoise", True), True)
        self.fallback_to_auto = _as_bool(kwargs.get("fallbackToAuto", True), True)
        self.require_npu_models = _as_bool(
            kwargs.get("requireNpuModels"),
            _as_bool(os.getenv("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS"), False),
        )
        if self.require_npu_models:
            os.environ.setdefault("UNSTRUCTUREDIO_REQUIRE_NPU_MODELS", "1")
            os.environ.setdefault("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", "1")
        self.json_indent = max(0, _as_int(kwargs.get("jsonIndent", 2), 2))
        self.pdf_languages = _as_language_list(kwargs.get("pdfLanguages"), ["chi_sim", "eng"])

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter()
        file_path = Path(sample[self.filepath_key])
        file_type = str(sample.get(self.filetype_key) or file_path.suffix.lstrip(".")).lower()
        elements, mode = self._extract_elements(file_path, file_type)
        if file_type == "pdf" and self.suppress_pdf_noise:
            elements = _filter_obvious_pdf_noise(elements)
            for index, item in enumerate(elements):
                item["index"] = index

        payload = self._build_payload(file_path, elements, mode, time.perf_counter() - start)
        sample[self.text_key] = self._render_output(payload)
        sample[self.target_type_key] = self.export_type if self.export_type in {"json", "jsonl", "txt"} else "json"
        return sample

    def _extract_elements(self, file_path: Path, file_type: str) -> tuple[list[Dict[str, Any]], str]:
        if file_type in {"docx", "doc"} and self.require_npu_models:
            converted_pdf = _convert_office_to_pdf(file_path)
            elements, mode = self._extract_pdf(converted_pdf)
            if mode != "pdf-npu-ocr-hi_res":
                raise RuntimeError(f"DOCX visual NPU route did not use NPU OCR mode: {mode}")
            return elements, f"{file_type}-visual-{mode}"

        if file_type == "docx" and self.enable_docx_fastpath:
            try:
                elements = _extract_docx_fastpath(file_path)
            except Exception as exc:
                logger.warning("DOCX fast path failed for %s: %s", file_path.name, exc)
                elements = []
            if elements:
                return elements, "docx-fastpath"

        if file_type == "pdf":
            return self._extract_pdf(file_path)

        if file_type == "doc" and partition_doc is not None:
            return _serialize_elements(partition_doc(filename=str(file_path))), "partition-doc"

        if file_type in IMAGE_PARTITION_EXTENSIONS:
            with _pdf_runtime_overrides():
                return _serialize_elements(partition_auto(filename=str(file_path))), "partition-auto-image"

        return _serialize_elements(partition_auto(filename=str(file_path))), "partition-auto"

    def _extract_pdf(self, file_path: Path) -> tuple[list[Dict[str, Any]], str]:
        pdf_kwargs = {
            "filename": str(file_path),
            "strategy": self.pdf_strategy,
            "infer_table_structure": _can_infer_pdf_table_structure(self.pdf_infer_table_structure),
            "languages": self.pdf_languages,
        }
        auto_kwargs = {
            "filename": str(file_path),
            "languages": self.pdf_languages,
        }
        npu_kwargs = dict(pdf_kwargs)
        npu_kwargs.update(
            {
                "strategy": "hi_res",
                "hi_res_model_name": "yolox",
                "pdf_image_dpi": 150,
            }
        )
        try:
            adapters_ready = _apply_npu_ocr_adapters()
            npu_layout_ready = adapters_ready or bool(_NPU_OCR_ADAPTER_STATUS["npu"])
            if not npu_layout_ready:
                raise RuntimeError("NPU layout adapter is unavailable")
            ocr_runtime_status = _get_ocr_runtime_status()
            npu_ocr_ready = _can_run_npu_ocr(ocr_runtime_status)
            if not npu_ocr_ready:
                if self.require_npu_models:
                    raise RuntimeError("OCR NPU runtime is unavailable; refusing CPU OCR fallback")
                logger.warning(
                    "OCR NPU runtime unavailable for %s; using fast PDF fallback instead of CPU OCR",
                    file_path.name,
                )
                raise RuntimeError("OCR NPU runtime is unavailable")
            npu_kwargs.update({"ocr_strategy": "force", "ocr_mode": "entire_page"})
            pdf_partition = _get_partition_pdf()
            if pdf_partition is None:
                raise RuntimeError("partition_pdf is required for NPU PDF extraction")
            with _pdf_runtime_overrides():
                npu_elements = _serialize_elements(pdf_partition(**npu_kwargs))
            if not self._needs_pdf_fallback(npu_elements):
                npu_elements = _promote_obvious_pdf_tables(npu_elements)
                npu_elements = self._supplement_pdf_tables_if_missing(file_path, npu_elements)
                return npu_elements, _npu_ocr_mode_name()
            logger.warning("NPU/OCR PDF path produced weak output for %s; falling back", file_path.name)
        except Exception as exc:
            if self.require_npu_models:
                raise
            logger.warning("NPU/OCR PDF path failed for %s; falling back: %s", file_path.name, exc)

        pdf_partition = _get_partition_pdf()
        if pdf_partition is None:
            return _serialize_elements(partition_auto(**auto_kwargs)), "partition-auto"

        fallback_strategy = "fast" if self.fallback_to_auto else self.pdf_strategy
        if self.pdf_strategy == "hi_res" and not self.fallback_to_auto:
            fallback_strategy = "auto"
        pdf_kwargs["strategy"] = fallback_strategy
        try:
            with _pdf_runtime_overrides():
                elements = pdf_partition(**pdf_kwargs)
            serialized = _serialize_elements(elements)
            serialized = _promote_obvious_pdf_tables(serialized)
        except Exception as exc:
            logger.warning(
                "PDF fallback strategy %s failed for %s: %s",
                fallback_strategy,
                file_path.name,
                exc,
            )
            if fallback_strategy != "auto":
                fallback_kwargs = dict(pdf_kwargs)
                fallback_kwargs["strategy"] = "auto"
                with _pdf_runtime_overrides():
                    return (
                        _promote_obvious_pdf_tables(_serialize_elements(pdf_partition(**fallback_kwargs))),
                        "pdf-npu-ocr-fallback-auto",
                    )
            raise
        if fallback_strategy == "fast" and self.fallback_to_auto and self._needs_pdf_fallback(serialized):
            fallback_kwargs = dict(pdf_kwargs)
            fallback_kwargs["strategy"] = "auto"
            try:
                with _pdf_runtime_overrides():
                    return (
                        _promote_obvious_pdf_tables(_serialize_elements(pdf_partition(**fallback_kwargs))),
                        "pdf-npu-ocr-fallback-auto",
                    )
            except Exception as exc:
                logger.warning(
                    "PDF auto fallback failed for %s; keeping fast result: %s",
                    file_path.name,
                    exc,
                )
        return serialized, f"pdf-npu-ocr-fallback-{fallback_strategy}"

    def _supplement_pdf_tables_if_missing(
        self,
        file_path: Path,
        elements: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        if any(item.get("category") == "Table" for item in elements):
            return elements
        pdf_partition = _get_partition_pdf()
        if pdf_partition is None:
            return elements
        try:
            with _pdf_runtime_overrides():
                supplement = _serialize_elements(
                    pdf_partition(
                        filename=str(file_path),
                        strategy="fast",
                        infer_table_structure=False,
                        languages=self.pdf_languages,
                    )
                )
        except Exception as exc:
            logger.warning("PDF table supplement failed for %s: %s", file_path.name, exc)
            return elements
        return _merge_pdf_table_supplements(elements, _promote_obvious_pdf_tables(supplement))

    @staticmethod
    def _needs_pdf_fallback(elements: list[Dict[str, Any]]) -> bool:
        texts = [str(item.get("text") or "") for item in elements]
        text_chars = sum(len(text) for text in texts)
        informative_chars = sum(ch.isalnum() or "\u4e00" <= ch <= "\u9fff" for text in texts for ch in text)
        if len(elements) < 3 or text_chars < 80 or informative_chars < 20:
            return True
        has_structured_table = any(item.get("category") == "Table" for item in elements)
        return _has_table_reference(elements) and not has_structured_table

    def _render_output(self, payload: Dict[str, Any]) -> str:
        if self.export_type == "txt":
            return _render_txt(payload["elements"])
        if self.export_type == "jsonl":
            return "\n".join(json.dumps(item, ensure_ascii=False) for item in payload["elements"])
        return json.dumps(payload, ensure_ascii=False, indent=self.json_indent)

    @staticmethod
    def _build_payload(
        file_path: Path,
        elements: list[Dict[str, Any]],
        mode: str,
        duration_seconds: float,
    ) -> Dict[str, Any]:
        table_count = sum(1 for item in elements if item.get("category") == "Table")
        table_html_count = sum(
            1 for item in elements if item.get("category") == "Table" and item.get("text_as_html")
        )
        return {
            "input_file": file_path.name,
            "mode": mode,
            "duration_seconds": round(duration_seconds, 2),
            "element_count": len(elements),
            "table_count": table_count,
            "table_html_count": table_html_count,
            "elements": elements,
        }
