import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_SYNTHESIS_DIR = os.path.join(PROJECT_ROOT, "data_synthesis")
if DATA_SYNTHESIS_DIR not in sys.path:
    sys.path.insert(0, DATA_SYNTHESIS_DIR)

from data_synthesizer import MedicalDataSynthesizer


SUPPORTED_TASK_TYPES = ("QA", "CoT", "Preference")
DEFAULT_SYNTHESIS_MODEL_PATH = "/model/Qwen/Qwen3-4B-Instruct-2507"
SERVICE_REQUEST_LOCK = threading.RLock()
WORKER_RESULT_PREFIX = "__DATA_SYNTHESIS_RESULT__"


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


def _initialize_npu_context() -> Optional[str]:
    visible = (
        os.environ.get("ASCEND_VISIBLE_DEVICES")
        or os.environ.get("ASCEND_RT_VISIBLE_DEVICES")
        or os.environ.get("NPU_VISIBLE_DEVICES")
        or ""
    ).strip()
    logical_device = 0
    if visible:
        first = visible.split(",")[0].strip()
        if first.isdigit() and len(visible.split(",")) > 1:
            logical_device = 0

    try:
        import torch
        import torch_npu  # noqa: F401

        if hasattr(torch, "npu") and torch.npu.is_available():
            torch.npu.set_device(logical_device)
            return f"npu:{logical_device}"
    except Exception as exc:  # pragma: no cover - depends on Ascend runtime
        return f"npu_init_failed:{exc}"
    return None


@dataclass
class _GeneratedCandidate:
    text: str


@dataclass
class _GeneratedResult:
    outputs: List[_GeneratedCandidate]


def _sampling_param_value(sampling_params: Any, name: str, default: Any, value_type: Any) -> Any:
    kwargs = getattr(sampling_params, "kwargs", None)
    if isinstance(kwargs, dict) and name in kwargs:
        value = kwargs[name]
    else:
        value = getattr(sampling_params, name, default)
    try:
        return value_type(value)
    except (TypeError, ValueError):
        return default


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
                _initialize_npu_context()
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
        max_new_tokens = _sampling_param_value(sampling_params, "max_tokens", 256, int)
        temperature = _sampling_param_value(sampling_params, "temperature", 0.1, float)
        top_p = _sampling_param_value(sampling_params, "top_p", 0.9, float)
        repetition_penalty = _sampling_param_value(sampling_params, "repetition_penalty", 1.0, float)

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


class SynthesisService:
    def __init__(
        self,
        model_path: Optional[str] = None,
        synthesizer: Any = None,
    ) -> None:
        env_synthesis_model_path = (os.environ.get("DATA_SYNTHESIS_MODEL_PATH") or "").strip()
        env_model_path = (os.environ.get("MODEL_PATH") or "").strip()
        self.model_path = (
            (model_path or "").strip()
            or env_synthesis_model_path
            or env_model_path
            or DEFAULT_SYNTHESIS_MODEL_PATH
        )
        self.backend = os.environ.get("DATA_SYNTHESIS_BACKEND", "auto").lower()
        requested_run_mode = os.environ.get("DATA_SYNTHESIS_RUN_MODE", "inprocess").lower()
        force_subprocess = os.environ.get("DATA_SYNTHESIS_FORCE_SUBPROCESS", "").lower() == "true"
        self.run_mode = "subprocess" if requested_run_mode == "subprocess" and force_subprocess else "inprocess"
        self._ready = False
        self._init_error: Optional[str] = None
        self._synthesizer_error: Optional[str] = None
        self.synthesizer = synthesizer
        self._model_lock = threading.RLock()
        self._model_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="data-synthesis-model")
        self._npu_context: Optional[str] = None

    def _run_on_model_thread(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return self._model_executor.submit(func, *args, **kwargs).result()

    def _run_exclusive_request(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        with SERVICE_REQUEST_LOCK:
            return func(*args, **kwargs)

    def _ensure_synthesizer_initialized(self) -> None:
        if self.synthesizer is not None:
            self._ready = True
            self._init_error = None
            return
        try:
            self.synthesizer = self._run_on_model_thread(self._build_synthesizer)
            self._ready = True
            self._init_error = None
            self._synthesizer_error = None
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            self._synthesizer_error = str(exc)

    def _ensure_initialized(self) -> None:
        with self._model_lock:
            if self._ready and self.synthesizer is not None:
                return
            self._ensure_synthesizer_initialized()
            if not self._ready:
                self._ensure_synthesizer_initialized()

    def warmup(self) -> Dict[str, Any]:
        if self.run_mode == "subprocess":
            return self.health()
        self._ensure_initialized()
        if not self._ready or self.synthesizer is None:
            return self.health()
        with self._model_lock:
            self._run_on_model_thread(
                self.synthesizer.generate_data_batch,
                "QA",
                ["warmup probe"],
            )
        return self.health()

    def health(self) -> Dict[str, Any]:
        return {
            "service": "data_synthesis",
            "ready": True if self.run_mode == "subprocess" else self._ready,
            "model_path": self.model_path,
            "backend": self.backend,
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
            return self._run_exclusive_request(
                self._synthesize_via_subprocess,
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

        for task_type in normalized_task_types:
            started_at = time.time()
            with self._model_lock:
                batch_results = self._run_on_model_thread(
                    self.synthesizer.generate_data_batch,
                    task_type,
                    [normalized_text],
                )
            elapsed = time.time() - started_at
            per_item_latency = elapsed / max(len(batch_results), 1)
            results[task_type] = batch_results

            for item in batch_results:
                records.append(
                    {
                        "task_type": task_type,
                        "status": item.get("status", "failed"),
                        "latency": per_item_latency,
                        "data": item.get("data", {}),
                    }
                )

        metrics: Dict[str, Any] = {}
        if include_metrics:
            metrics = self._build_metrics(records)

        return {
            "source_file": file_name,
            "task_types": normalized_task_types,
            "results": results,
            "metrics": metrics,
            "status": "success",
        }

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
print("__DATA_SYNTHESIS_RESULT__" + json.dumps(result, ensure_ascii=False))
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
        return _parse_worker_stdout(completed.stdout)

    def _build_metrics(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        success_count = sum(1 for record in records if record.get("status") == "success")
        total = len(records)
        avg_latency = (
            sum(float(record.get("latency", 0.0)) for record in records) / total
            if total
            else 0.0
        )
        return {
            "ready": True,
            "summary": {
                "record_count": total,
                "success_count": success_count,
                "success_rate_pct": (success_count / total * 100.0) if total else 0.0,
                "avg_latency_sec": avg_latency,
            },
            "note": "Model-based quality evaluation is provided by data_quality_evaluator_service.",
        }
