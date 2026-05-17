from __future__ import annotations

import contextlib
import html
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from datamate.core.base_op import Mapper
from unstructured.partition.auto import partition as partition_auto

try:
    from unstructured.partition.doc import partition_doc
except ImportError:
    partition_doc = None

try:
    from unstructured.partition.pdf import partition_pdf
except ImportError:
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
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PDF_LAYOUT_MODEL_PATH = os.getenv(
    "UNSTRUCTUREDIO_LAYOUT_MODEL_PATH",
    "/models/unstructuredio/yolo_x_layout/yolox_l0.05.onnx",
)
PDF_TABLE_MODEL_PATH = os.getenv(
    "UNSTRUCTUREDIO_TABLE_MODEL_PATH",
    "/models/unstructuredio/table-transformer-structure-recognition",
)
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
                from transformers import DetrImageProcessor, TableTransformerForObjectDetection

                def _initialize_table_model_local(self, model=None, device="cpu"):
                    self.device = device
                    self.feature_extractor = DetrImageProcessor.from_pretrained(
                        PDF_TABLE_MODEL_PATH,
                        local_files_only=True,
                    )
                    self.model = TableTransformerForObjectDetection.from_pretrained(
                        PDF_TABLE_MODEL_PATH,
                        local_files_only=True,
                        use_pretrained_backbone=False,
                    )
                    self.model.eval()
                    self.model = self.model.to(device)

                def _load_agent_with_local_model():
                    if getattr(tables_module.tables_agent, "model", None) is None:
                        _initialize_table_model_local(
                            tables_module.tables_agent,
                            PDF_TABLE_MODEL_PATH,
                            device="cpu",
                        )

                if original_initialize is not None:
                    tables_module.UnstructuredTableTransformerModel.initialize = _initialize_table_model_local
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
    return {
        "index": index,
        "category": getattr(element, "category", element.__class__.__name__),
        "text": str(getattr(element, "text", str(element))),
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


class UnstructuredIOMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.export_type = str(kwargs.get("exportType", "json") or "json").strip().lower()
        self.pdf_strategy = str(kwargs.get("pdfStrategy", "auto") or "auto").strip().lower()
        self.pdf_infer_table_structure = _as_bool(kwargs.get("pdfInferTableStructure", True), True)
        self.enable_docx_fastpath = _as_bool(kwargs.get("enableDocxFastpath", True), True)
        self.suppress_pdf_noise = _as_bool(kwargs.get("suppressPdfNoise", True), True)
        self.fallback_to_auto = _as_bool(kwargs.get("fallbackToAuto", True), True)
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
            "infer_table_structure": self.pdf_infer_table_structure,
            "languages": self.pdf_languages,
        }
        auto_kwargs = {
            "filename": str(file_path),
            "languages": self.pdf_languages,
        }
        if partition_pdf is None:
            return _serialize_elements(partition_auto(**auto_kwargs)), "partition-auto"

        with _pdf_runtime_overrides():
            elements = partition_pdf(**pdf_kwargs)
        serialized = _serialize_elements(elements)
        if self.pdf_strategy == "fast" and self.fallback_to_auto and self._needs_pdf_fallback(serialized):
            fallback_kwargs = dict(pdf_kwargs)
            fallback_kwargs["strategy"] = "auto"
            with _pdf_runtime_overrides():
                return _serialize_elements(partition_pdf(**fallback_kwargs)), "pdf-fast-fallback-auto"
        return serialized, f"pdf-{self.pdf_strategy}"

    @staticmethod
    def _needs_pdf_fallback(elements: list[Dict[str, Any]]) -> bool:
        text_chars = sum(len(str(item.get("text") or "")) for item in elements)
        return len(elements) < 3 or text_chars < 80

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
