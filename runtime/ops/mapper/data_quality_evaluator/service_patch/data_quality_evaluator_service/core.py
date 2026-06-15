import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_QUALITY_EVALUATOR_DIR = os.path.join(PROJECT_ROOT, "data_quality_evaluator")
if DATA_QUALITY_EVALUATOR_DIR not in sys.path:
    sys.path.insert(0, DATA_QUALITY_EVALUATOR_DIR)

from data_evaluator import MedicalDataEvaluator


DEFAULT_EVALUATION_DIMENSIONS = ("准确性", "相关性", "安全性", "多样性", "完整性")
EVALUATION_DIMENSION_ALIASES = {
    "accuracy": "准确性",
    "relevance": "相关性",
    "safety": "安全性",
    "diversity": "多样性",
    "completeness": "完整性",
    "准确性": "准确性",
    "相关性": "相关性",
    "安全性": "安全性",
    "多样性": "多样性",
    "完整性": "完整性",
}
DEFAULT_EVALUATOR_MODEL_PATH = "/model/Qwen/Qwen2.5-7B-Instruct"
SERVICE_REQUEST_LOCK = threading.RLock()
WORKER_RESULT_PREFIX = "__DATA_QUALITY_EVALUATOR_RESULT__"


def _is_truthy_env(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _parse_worker_stdout(stdout: str) -> Dict[str, Any]:
    output_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not output_lines:
        raise RuntimeError("subprocess returned empty output")

    for line in reversed(output_lines):
        if line.startswith(WORKER_RESULT_PREFIX):
            return json.loads(line[len(WORKER_RESULT_PREFIX):])

    for line in reversed(output_lines):
        if line.startswith("{") or line.startswith("["):
            return json.loads(line)

    raise RuntimeError("subprocess returned no JSON result")


def _normalize_dimensions(target_dimensions: Optional[Iterable[str]]) -> List[str]:
    if target_dimensions is None:
        return list(DEFAULT_EVALUATION_DIMENSIONS)
    raw_dimensions = [str(dim).strip() for dim in target_dimensions if str(dim).strip()]
    normalized = [
        EVALUATION_DIMENSION_ALIASES.get(dim.lower(), EVALUATION_DIMENSION_ALIASES.get(dim))
        for dim in raw_dimensions
    ]
    invalid = [dim for dim, mapped in zip(raw_dimensions, normalized) if mapped is None]
    if invalid:
        raise ValueError(f"Unsupported target_dimensions: {invalid}")
    if not normalized:
        raise ValueError("target_dimensions must not be empty")
    return [dim for dim in normalized if dim]


def _make_record(record_id: int, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": record_id,
        "type": task_type,
        "content": json.dumps(payload, ensure_ascii=False),
    }


def _records_from_synthesis_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    next_id = 1
    results = payload.get("results", {})
    if not isinstance(results, dict):
        return records

    for task_type in ("QA", "CoT", "Preference"):
        items = results.get(task_type, [])
        if not isinstance(items, list):
            continue
        for item in items:
            data = item
            if isinstance(item, dict) and "data" in item:
                if item.get("status") != "success":
                    continue
                data = item.get("data", {})
            if not isinstance(data, dict):
                continue
            records.append(_make_record(next_id, task_type, data))
            next_id += 1
    return records


def _parse_evaluation_input(text: str) -> List[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("text must not be empty")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("evaluation input must be JSON text") from exc

    if isinstance(parsed, dict) and "results" in parsed:
        records = _records_from_synthesis_payload(parsed)
        if records:
            return records
        raise ValueError("No successful generated records found in synthesis results")

    if isinstance(parsed, dict) and isinstance(parsed.get("records"), list):
        parsed = parsed["records"]

    if isinstance(parsed, dict) and "content" in parsed:
        parsed = [parsed]

    if not isinstance(parsed, list):
        raise ValueError("evaluation input must be a JSON array, a record object, or synthesis results JSON")

    records: List[Dict[str, Any]] = []
    for idx, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise ValueError("Each evaluation record must be a JSON object")
        content = item.get("content")
        if isinstance(content, dict):
            task_type = str(item.get("type") or "QA")
            records.append(_make_record(int(item.get("id") or idx), task_type, content))
            continue
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Each evaluation record must contain non-empty content")
        records.append(
            {
                "id": int(item.get("id") or idx),
                "type": str(item.get("type") or "QA"),
                "content": content,
            }
        )

    if not records:
        raise ValueError("No evaluation records found")
    return records


class DataQualityEvaluatorService:
    def __init__(
        self,
        evaluator_model_path: Optional[str] = None,
        evaluator: Any = None,
    ) -> None:
        self.evaluator_model_path = (
            evaluator_model_path
            or os.environ.get("DATA_QUALITY_EVALUATOR_MODEL_PATH")
            or os.environ.get("DATA_EVALUATOR_MODEL_PATH")
            or DEFAULT_EVALUATOR_MODEL_PATH
        )
        self.evaluator_backend = (
            os.environ.get("DATA_QUALITY_EVALUATOR_BACKEND")
            or os.environ.get("DATA_EVALUATOR_BACKEND")
            or "vllm"
        ).strip().lower()
        requested_run_mode = os.environ.get("DATA_QUALITY_EVALUATOR_RUN_MODE", "inprocess").lower()
        force_subprocess = os.environ.get("DATA_QUALITY_EVALUATOR_FORCE_SUBPROCESS", "").lower() == "true"
        self.run_mode = "subprocess" if requested_run_mode == "subprocess" and force_subprocess else "inprocess"
        self.evaluator = evaluator
        self._evaluator_error: Optional[str] = None
        self._model_lock = threading.RLock()
        self._model_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="data-quality-evaluator-model")

    def _run_on_model_thread(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return self._model_executor.submit(func, *args, **kwargs).result()

    def _run_exclusive_request(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        with SERVICE_REQUEST_LOCK:
            return func(*args, **kwargs)

    def _ensure_evaluator_initialized(self, backend: Optional[str] = None) -> None:
        requested_backend = (backend or self.evaluator_backend or "vllm").strip().lower()
        current_backend = getattr(self.evaluator, "backend", None)
        if self.evaluator is not None and current_backend in (None, requested_backend):
            self._evaluator_error = None
            return
        try:
            self.evaluator = self._run_on_model_thread(
                MedicalDataEvaluator,
                self.evaluator_model_path,
                backend=requested_backend,
            )
            self._evaluator_error = None
        except Exception as exc:
            self._evaluator_error = str(exc)
            raise

    def warmup(self) -> Dict[str, Any]:
        if self.run_mode == "subprocess":
            return self.health()
        try:
            self._ensure_evaluator_initialized(self.evaluator_backend)
        except Exception:
            pass
        return self.health()

    def health(self) -> Dict[str, Any]:
        return {
            "service": "data_quality_evaluator",
            "ready": True if self.run_mode == "subprocess" else self.evaluator is not None,
            "evaluator_model_path": self.evaluator_model_path,
            "evaluator_backend": self.evaluator_backend,
            "error": None if self.run_mode == "subprocess" else self._evaluator_error,
        }

    def evaluate_text(
        self,
        file_name: str,
        text: str,
        target_dimensions: Optional[Iterable[str]] = None,
        include_summary: bool = True,
        model_path: Optional[str] = None,
        backend: Optional[str] = None,
    ) -> Dict[str, Any]:
        requested_backend = (backend or self.evaluator_backend or "vllm").strip().lower()
        evaluator_worker = _is_truthy_env("DATA_QUALITY_EVALUATOR_ISOLATED_WORKER")
        if self.run_mode == "subprocess" or (requested_backend == "vllm" and not evaluator_worker):
            return self._run_exclusive_request(
                self._evaluate_via_subprocess,
                file_name=file_name,
                text=text,
                target_dimensions=target_dimensions,
                include_summary=include_summary,
                model_path=model_path,
                backend=requested_backend,
            )

        return self._evaluate_text_inprocess(
            file_name=file_name,
            text=text,
            target_dimensions=target_dimensions,
            include_summary=include_summary,
            model_path=model_path,
            backend=requested_backend,
        )

    def _evaluate_text_inprocess(
        self,
        file_name: str,
        text: str,
        target_dimensions: Optional[Iterable[str]] = None,
        include_summary: bool = True,
        model_path: Optional[str] = None,
        backend: Optional[str] = None,
    ) -> Dict[str, Any]:
        requested_backend = (backend or self.evaluator_backend or "vllm").strip().lower()
        if model_path and model_path != self.evaluator_model_path:
            self.evaluator_model_path = model_path
            self.evaluator = None
        try:
            self._ensure_evaluator_initialized(requested_backend)
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc
        if self.evaluator is None:
            raise RuntimeError(self._evaluator_error or "Evaluator is not ready")

        records = _parse_evaluation_input(text)
        dimensions = _normalize_dimensions(target_dimensions)
        with self._model_lock:
            evaluation_results = self._run_on_model_thread(
                self.evaluator.evaluate,
                records,
                target_dimensions=dimensions,
            )

        response: Dict[str, Any] = {
            "source_file": file_name,
            "record_count": len(records),
            "dimensions": dimensions,
            "results": evaluation_results,
            "runtime": (
                self.evaluator.runtime_metadata()
                if hasattr(self.evaluator, "runtime_metadata")
                else {
                    "evaluator_backend": getattr(self.evaluator, "backend", "unknown"),
                    "evaluator_model_path": self.evaluator_model_path,
                    "vllm_enabled": getattr(self.evaluator, "backend", None) == "vllm",
                }
            ),
            "status": "success",
        }
        if include_summary:
            response["summary"] = self._build_evaluation_summary(records, evaluation_results, dimensions)
        return response

    def _evaluate_via_subprocess(
        self,
        file_name: str,
        text: str,
        target_dimensions: Optional[Iterable[str]],
        include_summary: bool,
        model_path: Optional[str],
        backend: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_dimensions = _normalize_dimensions(target_dimensions)
        worker_payload = {
            "file_name": file_name,
            "text": text,
            "target_dimensions": normalized_dimensions,
            "include_summary": include_summary,
            "model_path": model_path or self.evaluator_model_path,
            "evaluator_backend": backend or self.evaluator_backend or "vllm",
        }
        worker_code = """
import json
import os
import sys
payload = json.loads(sys.stdin.read())
os.environ["DATA_QUALITY_EVALUATOR_MODEL_PATH"] = payload.get("model_path") or ""
os.environ["DATA_QUALITY_EVALUATOR_BACKEND"] = payload.get("evaluator_backend") or "vllm"
os.environ["DATA_QUALITY_EVALUATOR_ISOLATED_WORKER"] = "true"
from data_quality_evaluator_service.core import DataQualityEvaluatorService
service = DataQualityEvaluatorService(evaluator_model_path=payload.get("model_path"))
result = service._evaluate_text_inprocess(
    file_name=payload["file_name"],
    text=payload["text"],
    target_dimensions=payload["target_dimensions"],
    include_summary=payload["include_summary"],
    model_path=payload.get("model_path"),
    backend=payload.get("evaluator_backend"),
)
print("__DATA_QUALITY_EVALUATOR_RESULT__" + json.dumps(result, ensure_ascii=False))
"""
        env = os.environ.copy()
        env["DATA_QUALITY_EVALUATOR_RUN_MODE"] = "inprocess"
        env["DATA_QUALITY_EVALUATOR_ISOLATED_WORKER"] = "true"
        completed = subprocess.run(
            [sys.executable, "-c", worker_code],
            input=json.dumps(worker_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            env=env,
            cwd=PROJECT_ROOT,
            check=False,
        )
        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout or "subprocess failed").strip()
            raise RuntimeError(error_text)
        return _parse_worker_stdout(completed.stdout)

    def _build_evaluation_summary(
        self,
        records: List[Dict[str, Any]],
        evaluation_results: List[Dict[str, Any]],
        dimensions: List[str],
    ) -> Dict[str, Any]:
        per_dimension: Dict[str, Dict[str, Any]] = {}
        for dim in dimensions:
            scores = []
            for item in evaluation_results:
                score = item.get("scores", {}).get(dim, {}).get("score", -1)
                if isinstance(score, int) and score >= 0:
                    scores.append(score)
            pass_count = sum(1 for score in scores if score == 1)
            total = len(scores)
            pass_rate = (pass_count / total * 100.0) if total else 0.0
            per_dimension[dim] = {
                "pass_count": pass_count,
                "total": total,
                "pass_rate_pct": pass_rate,
            }

        task_type_counts: Dict[str, int] = {}
        for record in records:
            task_type = str(record.get("type") or "QA")
            task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

        return {
            "record_count": len(records),
            "task_type_counts": task_type_counts,
            "dimensions": per_dimension,
        }
