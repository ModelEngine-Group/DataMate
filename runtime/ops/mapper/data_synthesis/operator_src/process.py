import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
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


DEFAULT_SERVICE_URL = "http://data-synthesis-service:18103"
LEGACY_SERVICE_URLS = {
    "http://data-synthesis-service:18080": DEFAULT_SERVICE_URL,
    "http://data-synthesis-service:18080/": DEFAULT_SERVICE_URL,
    }
SUPPORTED_TASK_TYPES = {"QA", "CoT", "Preference"}
DEFAULT_LOCK_PATH = os.path.join(tempfile.gettempdir(), "data_synthesis_service_call.lock")
DEFAULT_TIMEOUT_SEC = 3600
DEFAULT_LOCK_WAIT_TIMEOUT_SEC = 7200


def build_lock_path(service_url: str) -> str:
    lock_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", service_url.strip().rstrip("/"))
    return os.path.join(tempfile.gettempdir(), f"data_synthesis_service_call_{lock_key}.lock")


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


def parse_min_int(value: Any, default: int) -> int:
    parsed = int(value)
    return max(parsed, default)


def normalize_service_url(value: Any) -> str:
    raw = str(value or DEFAULT_SERVICE_URL).strip().rstrip("/")
    return LEGACY_SERVICE_URLS.get(raw, raw)


def parse_service_urls(value: Any) -> List[str]:
    if value is None or value == "":
        return [DEFAULT_SERVICE_URL]
    if isinstance(value, str):
        items = [normalize_service_url(item) for item in value.split(",") if item.strip()]
    else:
        items = [normalize_service_url(item) for item in value if str(item).strip()]
    return items or [DEFAULT_SERVICE_URL]


def parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@contextmanager
def service_call_lock(
    lock_path: str = DEFAULT_LOCK_PATH,
    poll_interval: float = 0.2,
    max_wait_sec: int = DEFAULT_LOCK_WAIT_TIMEOUT_SEC,
):
    """Serialize DataMate Ray workers before entering the single-model HTTP service."""
    lock_file = open(lock_path, "a+", encoding="utf-8")
    deadline = time.monotonic() + max_wait_sec

    def _raise_if_timed_out() -> None:
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out waiting for data_synthesis service lock after {max_wait_sec}s: {lock_path}"
            )

    try:
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    _raise_if_timed_out()
                    time.sleep(poll_interval)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            while True:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    _raise_if_timed_out()
                    time.sleep(poll_interval)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()


class DataSynthesisMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_urls = parse_service_urls(kwargs.get("serviceUrls"))
        configured_service_url = kwargs.get("serviceUrl")
        self.service_url = normalize_service_url(configured_service_url) if configured_service_url else self.service_urls[0]
        self.task_types = _parse_task_types(kwargs.get("taskTypes", "QA,CoT,Preference"))
        self.include_metrics = str(kwargs.get("includeMetrics", "false")).lower() == "true"
        self.timeout_sec = parse_min_int(kwargs.get("timeoutSec", DEFAULT_TIMEOUT_SEC), DEFAULT_TIMEOUT_SEC)
        self.lock_wait_timeout_sec = parse_min_int(
            kwargs.get("lockWaitTimeoutSec", DEFAULT_LOCK_WAIT_TIMEOUT_SEC),
            DEFAULT_LOCK_WAIT_TIMEOUT_SEC,
        )
        self.use_service_lock = parse_bool(kwargs.get("useServiceLock"), False)
        self.lock_path = str(kwargs.get("lockPath") or build_lock_path(self.service_url))
        self._service_index = 0

    def _next_service_url(self) -> str:
        service_url = self.service_urls[self._service_index % len(self.service_urls)]
        self._service_index += 1
        return service_url

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        file_name = str(sample.get(self.filename_key, "input.txt"))
        active_service_url = self._next_service_url() if len(self.service_urls) > 1 and self.service_url == self.service_urls[0] else self.service_url
        active_lock_path = build_lock_path(active_service_url)
        payload = build_service_payload(
            sample,
            self.task_types,
            self.include_metrics,
            text_key=self.text_key,
            filepath_key=self.filepath_key,
            filename_key=self.filename_key,
        )
        call_start = time.monotonic()
        if self.use_service_lock:
            wait_start = time.monotonic()
            print(
                f"[data_synthesis] waiting_lock file={file_name} "
                f"lock_path={active_lock_path} max_wait_sec={self.lock_wait_timeout_sec}",
                flush=True,
            )
            with service_call_lock(lock_path=active_lock_path, max_wait_sec=self.lock_wait_timeout_sec):
                wait_elapsed = time.monotonic() - wait_start
                print(
                    f"[data_synthesis] calling_service file={file_name} "
                    f"service_url={active_service_url} wait_elapsed={wait_elapsed:.2f}s "
                    f"task_types={','.join(self.task_types)} timeout_sec={self.timeout_sec}",
                    flush=True,
                )
                response = requests.post(
                    f"{active_service_url}/synthesize-file",
                    json=payload,
                    timeout=self.timeout_sec,
                )
        else:
            print(
                f"[data_synthesis] calling_service file={file_name} "
                f"service_url={active_service_url} wait_elapsed=0.00s "
                f"task_types={','.join(self.task_types)} timeout_sec={self.timeout_sec} "
                f"use_service_lock=false",
                flush=True,
            )
            response = requests.post(
                f"{active_service_url}/synthesize-file",
                json=payload,
                timeout=self.timeout_sec,
            )
        call_elapsed = time.monotonic() - call_start
        print(
            f"[data_synthesis] service_done file={file_name} "
            f"status_code={response.status_code} call_elapsed={call_elapsed:.2f}s",
            flush=True,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"data_synthesis service failed: {response.status_code} {response.text}"
            )
        sample[self.text_key] = serialize_service_response(response.json())
        sample[self.target_type_key] = "json"
        return sample
