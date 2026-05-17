import json
import os
from typing import Any, Dict, Iterable, List, Optional

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


DEFAULT_SERVICE_URL = "http://data-synthesis-service:18080"
SUPPORTED_TASK_TYPES = {"QA", "CoT", "Preference"}


def _parse_task_types(value: Any) -> List[str]:
    if value is None or value == "":
        return ["QA", "CoT", "Preference"]
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    else:
        items = [str(item).strip() for item in value if str(item).strip()]
    invalid = [item for item in items if item not in SUPPORTED_TASK_TYPES]
    if invalid:
        raise ValueError(f"Unsupported taskTypes: {invalid}")
    return items or ["QA", "CoT", "Preference"]


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
    task_types: Iterable[str],
    include_metrics: bool,
    text_key: str = "text",
    filepath_key: str = "filePath",
    filename_key: str = "fileName",
) -> Dict[str, Any]:
    text = _read_text_from_sample(sample, text_key, filepath_key)
    if not text:
        raise ValueError("Input text is empty")
    return {
        "file_name": sample.get(filename_key, "input.txt"),
        "text": text,
        "task_types": list(task_types),
        "include_metrics": include_metrics,
    }


def serialize_service_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


class DataSynthesisMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_url = str(kwargs.get("serviceUrl", DEFAULT_SERVICE_URL)).rstrip("/")
        self.task_types = _parse_task_types(kwargs.get("taskTypes", "QA,CoT,Preference"))
        self.include_metrics = str(kwargs.get("includeMetrics", "true")).lower() == "true"
        self.timeout_sec = int(kwargs.get("timeoutSec", 300))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        payload = build_service_payload(
            sample,
            self.task_types,
            self.include_metrics,
            text_key=self.text_key,
            filepath_key=self.filepath_key,
            filename_key=self.filename_key,
        )
        response = requests.post(
            f"{self.service_url}/synthesize-file",
            json=payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"data_synthesis service failed: {response.status_code} {response.text}"
            )
        sample[self.text_key] = serialize_service_response(response.json())
        sample[self.target_type_key] = "json"
        return sample
