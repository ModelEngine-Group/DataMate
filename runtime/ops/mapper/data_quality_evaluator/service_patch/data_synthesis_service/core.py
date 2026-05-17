import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_SYNTHESIS_DIR = os.path.join(PROJECT_ROOT, "data_synthesis")
if DATA_SYNTHESIS_DIR not in sys.path:
    sys.path.insert(0, DATA_SYNTHESIS_DIR)

from data_evaluator import MedicalDataEvaluator
from data_synthesizer import MedicalDataSynthesizer
from requirement_metrics import calculate_generation_metrics, check_project_targets


SUPPORTED_TASK_TYPES = ("QA", "CoT", "Preference")
DEFAULT_EVALUATION_DIMENSIONS = ("准确性", "相关性", "安全性", "多样性", "完整性")
DEFAULT_EVALUATOR_MODEL_PATH = "/model/Qwen/Qwen2.5-7B-Instruct"


@dataclass
class _GeneratedCandidate:
    text: str


@dataclass
class _GeneratedResult:
    outputs: List[_GeneratedCandidate]


class TransformersLLMAdapter:
    def __init__(self, model_path: str) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except Exception as exc:  # pragma: no cover
            raise ImportError(f"transformers backend unavailable: {exc}") from exc

        self._torch = torch
        self._device = "cpu"
        model_dtype = torch.float32
        try:
            import torch_npu  # noqa: F401

            if hasattr(torch, "npu") and torch.npu.is_available():
                self._device = "npu:0"
                model_dtype = torch.float16
        except Exception:
            self._device = "cpu"

        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=model_dtype,
        )
        if self._device != "cpu":
            self._model = self._model.to(self._device)

        self._model.eval()

    def generate(self, prompts: List[str], sampling_params: Any) -> List[_GeneratedResult]:
        max_new_tokens = int(getattr(sampling_params, "kwargs", {}).get("max_tokens", 256))
        temperature = float(getattr(sampling_params, "kwargs", {}).get("temperature", 0.1))
        top_p = float(getattr(sampling_params, "kwargs", {}).get("top_p", 0.9))
        repetition_penalty = float(getattr(sampling_params, "kwargs", {}).get("repetition_penalty", 1.0))

        outputs: List[_GeneratedResult] = []
        for prompt in prompts:
            model_inputs = self._tokenizer(prompt, return_tensors="pt")
            if self._device != "cpu":
                model_inputs = {k: v.to(self._device) for k, v in model_inputs.items()}

            with self._torch.no_grad():
                generated_ids = self._model.generate(
                    **model_inputs,
                    do_sample=temperature > 0,
                    temperature=max(temperature, 1e-5),
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    max_new_tokens=max_new_tokens,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            prompt_len = model_inputs["input_ids"].shape[1]
            new_tokens = generated_ids[0][prompt_len:]
            text = self._tokenizer.decode(new_tokens, skip_special_tokens=False)
            outputs.append(_GeneratedResult(outputs=[_GeneratedCandidate(text=text)]))
        return outputs


def _normalize_task_types(task_types: Optional[Iterable[str]]) -> List[str]:
    if task_types is None:
        return list(SUPPORTED_TASK_TYPES)
    normalized = [task_type.strip() for task_type in task_types if str(task_type).strip()]
    invalid = [task_type for task_type in normalized if task_type not in SUPPORTED_TASK_TYPES]
    if invalid:
        raise ValueError(f"Unsupported task_types: {invalid}")
    if not normalized:
        raise ValueError("task_types must not be empty")
    return normalized


def _normalize_dimensions(target_dimensions: Optional[Iterable[str]]) -> List[str]:
    if target_dimensions is None:
        return list(DEFAULT_EVALUATION_DIMENSIONS)
    normalized = [str(dim).strip() for dim in target_dimensions if str(dim).strip()]
    invalid = [dim for dim in normalized if dim not in DEFAULT_EVALUATION_DIMENSIONS]
    if invalid:
        raise ValueError(f"Unsupported target_dimensions: {invalid}")
    if not normalized:
        raise ValueError("target_dimensions must not be empty")
    return normalized


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

    for task_type in SUPPORTED_TASK_TYPES:
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


class SynthesisService:
    def __init__(
        self,
        model_path: Optional[str] = None,
        evaluator_model_path: Optional[str] = None,
        synthesizer: Any = None,
        evaluator: Any = None,
    ) -> None:
        self.model_path = model_path or os.environ.get("DATA_SYNTHESIS_MODEL_PATH") or os.environ.get("MODEL_PATH")
        self.evaluator_model_path = (
            evaluator_model_path
            or os.environ.get("DATA_EVALUATOR_MODEL_PATH")
            or DEFAULT_EVALUATOR_MODEL_PATH
        )
        self.backend = os.environ.get("DATA_SYNTHESIS_BACKEND", "auto").lower()
        self.run_mode = os.environ.get("DATA_SYNTHESIS_RUN_MODE", "inprocess").lower()
        self._ready = False
        self._init_error: Optional[str] = "Service not initialized"
        self._synthesizer_error: Optional[str] = None
        self._evaluator_error: Optional[str] = None
        self.synthesizer = synthesizer
        self.evaluator = evaluator
        self.evaluator_backend = (
            os.environ.get("DATA_EVALUATOR_BACKEND")
            or "vllm"
        ).strip().lower()

    def _initialize_components(self) -> None:
        try:
            self.synthesizer = self.synthesizer or self._build_synthesizer()
            self._ready = True
            self._init_error = None
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)

    def _ensure_synthesizer_initialized(self) -> None:
        if self.synthesizer is not None:
            self._ready = True
            self._init_error = None
            return
        try:
            self.synthesizer = self._build_synthesizer()
            self._ready = True
            self._init_error = None
            self._synthesizer_error = None
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            self._synthesizer_error = str(exc)

    def _ensure_evaluator_initialized(self, backend: Optional[str] = None) -> None:
        requested_backend = (backend or self.evaluator_backend or "vllm").strip().lower()
        current_backend = getattr(self.evaluator, "backend", None)
        if self.evaluator is not None and current_backend in (None, requested_backend):
            self._evaluator_error = None
            return
        try:
            self.evaluator = MedicalDataEvaluator(
                self.evaluator_model_path,
                backend=requested_backend,
            )
            self._evaluator_error = None
        except Exception as exc:
            self._evaluator_error = str(exc)
            raise

    def _ensure_initialized(self) -> None:
        if self._ready and self.synthesizer is not None:
            return
        self._ensure_synthesizer_initialized()
        if not self._ready:
            self._ensure_synthesizer_initialized()

    def health(self) -> Dict[str, Any]:
        if self.run_mode != "subprocess":
            self._ensure_initialized()
        return {
            "service": "data_synthesis",
            "ready": True if self.run_mode == "subprocess" else self._ready,
            "model_path": self.model_path,
            "evaluator_model_path": self.evaluator_model_path,
            "backend": self.backend,
            "evaluator_backend": self.evaluator_backend,
            "error": None if self.run_mode == "subprocess" else self._init_error,
        }

    def _build_synthesizer(self) -> MedicalDataSynthesizer:
        if not self.model_path:
            raise ValueError("model_path is required")

        if self.backend == "transformers":
            return MedicalDataSynthesizer(
                self.model_path,
                llm_instance=TransformersLLMAdapter(self.model_path),
            )

        if self.backend == "vllm":
            return MedicalDataSynthesizer(self.model_path)

        try:
            return MedicalDataSynthesizer(self.model_path)
        except Exception:
            return MedicalDataSynthesizer(
                self.model_path,
                llm_instance=TransformersLLMAdapter(self.model_path),
            )

    def synthesize_text(
        self,
        file_name: str,
        text: str,
        task_types: Optional[Iterable[str]] = None,
        include_metrics: bool = True,
    ) -> Dict[str, Any]:
        if self.run_mode == "subprocess":
            return self._synthesize_via_subprocess(
                file_name=file_name,
                text=text,
                task_types=task_types,
                include_metrics=include_metrics,
            )

        self._ensure_initialized()
        if not self._ready or self.synthesizer is None:
            raise RuntimeError(self._init_error or "Service is not ready")

        normalized_text = (text or "").strip()
        if not normalized_text:
            raise ValueError("text must not be empty")

        normalized_task_types = _normalize_task_types(task_types)
        results: Dict[str, List[Dict[str, Any]]] = {task_type: [] for task_type in SUPPORTED_TASK_TYPES}
        records: List[Dict[str, Any]] = []
        evaluation_inputs: List[Dict[str, Any]] = []

        for task_type in normalized_task_types:
            started_at = time.time()
            batch_results = self.synthesizer.generate_data_batch(task_type, [normalized_text])
            elapsed = time.time() - started_at
            per_item_latency = elapsed / max(len(batch_results), 1)
            results[task_type] = batch_results

            for item in batch_results:
                record = {
                    "task_type": task_type,
                    "status": item.get("status", "failed"),
                    "latency": per_item_latency,
                    "data": item.get("data", {}),
                }
                records.append(record)
                if item.get("status") == "success":
                    evaluation_inputs.append(
                        {
                            "type": task_type,
                            "content": json.dumps(item.get("data", {}), ensure_ascii=False),
                        }
                    )

        metrics: Dict[str, Any] = {}
        if include_metrics:
            metrics = self._build_metrics(records, evaluation_inputs)

        return {
            "source_file": file_name,
            "task_types": normalized_task_types,
            "results": results,
            "metrics": metrics,
            "status": "success",
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
        if self.run_mode == "subprocess":
            return self._evaluate_via_subprocess(
                file_name=file_name,
                text=text,
                target_dimensions=target_dimensions,
                include_summary=include_summary,
                model_path=model_path,
                backend=backend,
            )

        if model_path and model_path != self.evaluator_model_path:
            self.evaluator_model_path = model_path
            self.evaluator = None
        try:
            self._ensure_evaluator_initialized(backend or self.evaluator_backend or "vllm")
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc
        if self.evaluator is None:
            raise RuntimeError(self._init_error or "Evaluator is not ready")

        records = _parse_evaluation_input(text)
        dimensions = _normalize_dimensions(target_dimensions)
        evaluation_results = self.evaluator.evaluate(records, target_dimensions=dimensions)

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

    def _synthesize_via_subprocess(
        self,
        file_name: str,
        text: str,
        task_types: Optional[Iterable[str]],
        include_metrics: bool,
    ) -> Dict[str, Any]:
        normalized_task_types = _normalize_task_types(task_types)
        worker_payload = {
            "file_name": file_name,
            "text": text,
            "task_types": normalized_task_types,
            "include_metrics": include_metrics,
            "model_path": self.model_path,
            "backend": self.backend,
        }
        worker_code = """
import json
import os
import sys
payload = json.loads(sys.stdin.read())
os.environ["DATA_SYNTHESIS_MODEL_PATH"] = payload["model_path"] or ""
os.environ["DATA_SYNTHESIS_BACKEND"] = payload["backend"]
from data_synthesis_service.core import SynthesisService
service = SynthesisService(model_path=payload["model_path"])
result = service.synthesize_text(
    file_name=payload["file_name"],
    text=payload["text"],
    task_types=payload["task_types"],
    include_metrics=payload["include_metrics"],
)
print(json.dumps(result, ensure_ascii=False))
"""
        env = os.environ.copy()
        env["DATA_SYNTHESIS_RUN_MODE"] = "inprocess"
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
        output_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if not output_lines:
            raise RuntimeError("subprocess returned empty output")
        return json.loads(output_lines[-1])

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
            "action": "evaluate",
            "file_name": file_name,
            "text": text,
            "target_dimensions": normalized_dimensions,
            "include_summary": include_summary,
            "model_path": model_path or self.evaluator_model_path,
            "synthesis_model_path": self.model_path,
            "backend": self.backend,
            "evaluator_backend": backend or self.evaluator_backend or "vllm",
        }
        return self._run_subprocess_worker(worker_payload)

    def _run_subprocess_worker(self, worker_payload: Dict[str, Any]) -> Dict[str, Any]:
        worker_code = """
import json
import os
import sys
payload = json.loads(sys.stdin.read())
os.environ["DATA_SYNTHESIS_MODEL_PATH"] = payload.get("synthesis_model_path") or payload.get("model_path") or ""
os.environ["DATA_EVALUATOR_MODEL_PATH"] = payload.get("model_path") or ""
os.environ["DATA_SYNTHESIS_BACKEND"] = payload.get("backend") or "auto"
os.environ["DATA_EVALUATOR_BACKEND"] = payload.get("evaluator_backend") or "vllm"
from data_synthesis_service.core import SynthesisService
service = SynthesisService(
    model_path=payload.get("synthesis_model_path"),
    evaluator_model_path=payload.get("model_path"),
)
action = payload.get("action")
if action == "synthesize":
    result = service.synthesize_text(
        file_name=payload["file_name"],
        text=payload["text"],
        task_types=payload["task_types"],
        include_metrics=payload["include_metrics"],
    )
elif action == "evaluate":
    result = service.evaluate_text(
        file_name=payload["file_name"],
        text=payload["text"],
        target_dimensions=payload["target_dimensions"],
        include_summary=payload["include_summary"],
        model_path=payload.get("model_path"),
        backend=payload.get("evaluator_backend"),
    )
else:
    raise RuntimeError(f"Unsupported action: {action}")
print(json.dumps(result, ensure_ascii=False))
"""
        env = os.environ.copy()
        env["DATA_SYNTHESIS_RUN_MODE"] = "inprocess"
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
        output_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if not output_lines:
            raise RuntimeError("subprocess returned empty output")
        return json.loads(output_lines[-1])

    def _build_metrics(
        self,
        records: List[Dict[str, Any]],
        evaluation_inputs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        try:
            self._ensure_evaluator_initialized("rule")
            evaluator_scores = self.evaluator.evaluate(evaluation_inputs) if evaluation_inputs else []
            summary = calculate_generation_metrics(records, evaluator_scores)
            return {
                "ready": True,
                "summary": summary,
                "targets": check_project_targets(summary),
            }
        except Exception as exc:
            return {"ready": False, "error": str(exc)}

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
