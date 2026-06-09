import json
import os
from typing import Any, Dict, Iterable, List

import requests

try:
    from datamate.core.base_op import Mapper
except Exception:  # pragma: no cover
    class Mapper:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.text_key = kwargs.get("text_key", "text")
            self.filepath_key = kwargs.get("filePath_key", "filePath")
            self.filename_key = kwargs.get("fileName_key", "fileName")
            self.target_type_key = kwargs.get("target_type_key", "target_type")


DEFAULT_SERVICE_URL = "http://data-quality-evaluator-service:18112"
DEFAULT_EVALUATOR_MODEL_PATH = "/model/Qwen/Qwen2.5-7B-Instruct"
DIM_ACCURACY = "\u51c6\u786e\u6027"
DIM_RELEVANCE = "\u76f8\u5173\u6027"
DIM_SAFETY = "\u5b89\u5168\u6027"
DIM_DIVERSITY = "\u591a\u6837\u6027"
DIM_COMPLETENESS = "\u5b8c\u6574\u6027"
DIMENSION_ALIASES = {
    "accuracy": DIM_ACCURACY,
    "relevance": DIM_RELEVANCE,
    "safety": DIM_SAFETY,
    "diversity": DIM_DIVERSITY,
    "completeness": DIM_COMPLETENESS,
    DIM_ACCURACY: DIM_ACCURACY,
    DIM_RELEVANCE: DIM_RELEVANCE,
    DIM_SAFETY: DIM_SAFETY,
    DIM_DIVERSITY: DIM_DIVERSITY,
    DIM_COMPLETENESS: DIM_COMPLETENESS,
}
DEFAULT_DIMENSIONS = [
    DIM_ACCURACY,
    DIM_RELEVANCE,
    DIM_SAFETY,
    DIM_DIVERSITY,
    DIM_COMPLETENESS,
]


def _parse_dimensions(value: Any) -> List[str]:
    if value is None or value == "":
        return list(DEFAULT_DIMENSIONS)
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    else:
        items = [str(item).strip() for item in value if str(item).strip()]

    if items and all(set(item) <= {"?"} for item in items):
        return list(DEFAULT_DIMENSIONS)

    normalized = [DIMENSION_ALIASES.get(item.lower(), DIMENSION_ALIASES.get(item)) for item in items]
    invalid = [item for item, mapped in zip(items, normalized) if mapped is None]
    if invalid:
        raise ValueError(f"Unsupported targetDimensions: {invalid}")
    return [item for item in normalized if item] or list(DEFAULT_DIMENSIONS)


def _read_text_from_sample(sample: Dict[str, Any], text_key: str, filepath_key: str) -> str:
    text = str(sample.get(text_key, "") or "").strip()
    if text:
        return text

    file_path = sample.get(filepath_key)
    if file_path and os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    return ""


def build_service_payload(
    sample: Dict[str, Any],
    target_dimensions: Iterable[str],
    include_summary: bool,
    evaluator_model_path: str,
    evaluator_backend: str = "vllm",
    text_key: str = "text",
    filepath_key: str = "filePath",
    filename_key: str = "fileName",
) -> Dict[str, Any]:
    text = _read_text_from_sample(sample, text_key, filepath_key)
    if not text:
        raise ValueError("Input text is empty")
    return {
        "file_name": sample.get(filename_key, "input.json"),
        "text": text,
        "target_dimensions": list(target_dimensions),
        "include_summary": include_summary,
        "model_path": evaluator_model_path,
        "backend": evaluator_backend,
    }


def serialize_service_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


class DataQualityEvaluatorMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_url = str(kwargs.get("serviceUrl", DEFAULT_SERVICE_URL)).rstrip("/")
        self.target_dimensions = _parse_dimensions(
            kwargs.get("targetDimensions", "accuracy,relevance,safety,diversity,completeness")
        )
        self.evaluator_model_path = str(
            kwargs.get("evaluatorModelPath", DEFAULT_EVALUATOR_MODEL_PATH)
        ).strip() or DEFAULT_EVALUATOR_MODEL_PATH
        self.evaluator_backend = str(kwargs.get("evaluatorBackend", "vllm")).strip().lower() or "vllm"
        self.include_summary = str(kwargs.get("includeSummary", "true")).lower() == "true"
        self.timeout_sec = int(kwargs.get("timeoutSec", 600))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        payload = build_service_payload(
            sample,
            self.target_dimensions,
            self.include_summary,
            self.evaluator_model_path,
            self.evaluator_backend,
            text_key=self.text_key,
            filepath_key=self.filepath_key,
            filename_key=self.filename_key,
        )
        response = requests.post(
            f"{self.service_url}/evaluate-file",
            json=payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"data_quality_evaluator service failed: {response.status_code} {response.text}"
            )
        sample[self.text_key] = serialize_service_response(response.json())
        sample[self.target_type_key] = "json"
        return sample
