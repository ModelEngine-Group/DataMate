import os
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from subprocess import CompletedProcess
from unittest.mock import patch


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_synthesis_service import core as service_core
from data_synthesis_service.core import SynthesisService


class _FakeSynthesizer:
    def generate_data_batch(self, task_type, inputs):
        text = inputs[0]
        return [
            {
                "status": "success",
                "data": {
                    "question": f"{task_type}:{text}",
                    **(
                        {"answer": "ok。"}
                        if task_type == "QA"
                        else {"rationale": "step1 -> step2", "final_answer": "ok"}
                        if task_type == "CoT"
                        else {
                            "chosen": "good",
                            "rejected": "bad",
                            "preference_reason": "better",
                        }
                    ),
                },
            }
        ]


class _FlakySynthesizer:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient init failure")
        return _FakeSynthesizer()


class _PubMedUnstableSynthesizer:
    def generate_data_batch(self, task_type, inputs):
        if task_type == "QA":
            return [
                {
                    "status": "success",
                    "data": {
                        "question": "患者的主诉和查体结果提示什么问题？",
                        "answer": "患者主诉Source style: PubMedQA，建议尽快专科评估。",
                    },
                }
            ]
        return [
            {
                "status": "failed",
                "reason": "repair_failed",
                "raw_output": "<think>meta reasoning</think> noisy output",
                "repair_raw_output": "<think>meta reasoning</think> noisy output",
            }
        ]


class _ConcurrencyTrackingSynthesizer:
    def __init__(self):
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()
        self.first_entered = threading.Event()

    def generate_data_batch(self, task_type, inputs):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.first_entered.set()
        time.sleep(0.1)
        with self.lock:
            self.active -= 1
        return [
            {
                "status": "success",
                "data": {
                    "question": f"{task_type}:{inputs[0]}",
                    "answer": "ok。",
                },
            }
        ]


class _ThreadAffinitySynthesizer:
    def __init__(self):
        self.init_thread_id = threading.get_ident()

    def generate_data_batch(self, task_type, inputs):
        if threading.get_ident() != self.init_thread_id:
            raise RuntimeError("model used from a different thread")
        return [
            {
                "status": "success",
                "data": {
                    "question": f"{task_type}:{inputs[0]}",
                    "answer": "ok。",
                },
            }
        ]


class _WarmupTrackingSynthesizer:
    def __init__(self):
        self.calls = []

    def generate_data_batch(self, task_type, inputs):
        self.calls.append((task_type, list(inputs)))
        return [
            {
                "status": "success",
                "data": {
                    "question": f"{task_type}:{inputs[0]}",
                    "answer": "ok",
                },
            }
        ]


class ServiceCoreTests(unittest.TestCase):
    def test_sampling_param_reader_supports_real_vllm_attributes(self):
        class Params:
            max_tokens = 1800
            temperature = 0.0
            top_p = 1.0
            repetition_penalty = 1.05

        self.assertEqual(service_core._sampling_param_value(Params(), "max_tokens", 256, int), 1800)
        self.assertEqual(service_core._sampling_param_value(Params(), "temperature", 0.1, float), 0.0)

    def test_synthesize_text_returns_all_task_groups(self):
        service = SynthesisService(synthesizer=_FakeSynthesizer())
        result = service.synthesize_text("case.txt", "patient text")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_file"], "case.txt")
        self.assertEqual(result["task_types"], ["QA", "CoT", "Preference"])
        self.assertEqual(len(result["results"]["QA"]), 1)
        self.assertEqual(len(result["results"]["CoT"]), 1)
        self.assertEqual(len(result["results"]["Preference"]), 1)
        self.assertIn("metrics", result)

    def test_invalid_task_type_raises(self):
        service = SynthesisService(synthesizer=_FakeSynthesizer())
        with self.assertRaises(ValueError):
            service.synthesize_text("case.txt", "patient text", task_types=["BAD"])

    def test_empty_text_raises(self):
        service = SynthesisService(synthesizer=_FakeSynthesizer())
        with self.assertRaises(ValueError):
            service.synthesize_text("case.txt", "   ")

    @patch("data_synthesis_service.core.MedicalDataSynthesizer")
    def test_service_can_initialize_with_cpu_fallback(self, synthesizer_cls):
        synthesizer_cls.return_value = _FakeSynthesizer()
        with patch.dict(os.environ, {"DATA_SYNTHESIS_MODEL_PATH": "/models/demo"}, clear=False):
            service = SynthesisService()
        self.assertFalse(service.health()["ready"])
        self.assertEqual(service.synthesize_text("case.txt", "patient text")["status"], "success")
        self.assertTrue(service.health()["ready"])

    def test_constructor_does_not_initialize_npu_before_transformers_backend(self):
        with patch("data_synthesis_service.core._initialize_npu_context") as init_mock:
            service = SynthesisService(synthesizer=_FakeSynthesizer())
        self.assertIsNotNone(service)
        init_mock.assert_not_called()

    def test_health_does_not_initialize_model(self):
        builder = _FlakySynthesizer()
        with patch.object(SynthesisService, "_build_synthesizer", side_effect=builder):
            with patch.dict(os.environ, {"DATA_SYNTHESIS_MODEL_PATH": "/models/demo"}, clear=False):
                service = SynthesisService()
                first = service.health()
                self.assertFalse(first["ready"])
                self.assertIsNone(first["error"])
                self.assertEqual(builder.calls, 0)

    @patch("data_synthesis_service.core.subprocess.run")
    def test_subprocess_mode_uses_worker_process(self, run_mock):
        run_mock.return_value = CompletedProcess(
            args=["python"],
            returncode=0,
            stdout='log line\n{"status":"success","source_file":"case.txt","task_types":["QA"],"results":{"QA":[],"CoT":[],"Preference":[]},"metrics":{}}',
            stderr="",
        )
        with patch.dict(
            os.environ,
            {
                "DATA_SYNTHESIS_MODEL_PATH": "/models/demo",
                "DATA_SYNTHESIS_RUN_MODE": "subprocess",
                "DATA_SYNTHESIS_FORCE_SUBPROCESS": "true",
            },
            clear=False,
        ):
            service = SynthesisService()
            result = service.synthesize_text("case.txt", "patient text", task_types=["QA"], include_metrics=False)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_file"], "case.txt")

    def test_default_synthesis_model_path_switches_to_qwen3_4b_instruct_2507(self):
        with patch.dict(
            os.environ,
            {
                "DATA_SYNTHESIS_MODEL_PATH": "",
                "MODEL_PATH": "",
            },
            clear=False,
        ):
            service = SynthesisService()
        self.assertEqual(service.model_path, "/model/Qwen/Qwen3-4B-Instruct-2507")

    def test_synthesize_text_does_not_apply_service_level_deterministic_fallback(self):
        service = SynthesisService(synthesizer=_PubMedUnstableSynthesizer())
        text = (
            "Source style: PubMedQA (biomedical research QA)\n\n"
            "Research question: Can home blood pressure telemonitoring improve blood pressure "
            "control in patients with hypertension compared with usual care?"
        )

        result = service.synthesize_text("pubmedqa_style_case_en.txt", text)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"]["QA"][0]["status"], "success")
        self.assertNotIn("service_fallback", result["results"]["QA"][0])
        self.assertNotIn("deterministic", result["results"]["QA"][0])
        self.assertEqual(result["results"]["CoT"][0]["status"], "failed")
        self.assertEqual(result["results"]["Preference"][0]["status"], "failed")
        self.assertNotIn("service_fallback", result["results"]["CoT"][0])
        self.assertNotIn("deterministic", result["results"]["CoT"][0])
        self.assertNotIn("service_fallback", result["results"]["Preference"][0])
        self.assertNotIn("deterministic", result["results"]["Preference"][0])

    def test_synthesize_text_serializes_shared_model_requests(self):
        synthesizer = _ConcurrencyTrackingSynthesizer()
        service = SynthesisService(synthesizer=synthesizer)

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(
                service.synthesize_text,
                "case-1.txt",
                "患者出现头晕。",
                task_types=["QA"],
                include_metrics=False,
            )
            self.assertTrue(synthesizer.first_entered.wait(timeout=1))
            second = executor.submit(
                service.synthesize_text,
                "case-2.txt",
                "患者出现咳嗽。",
                task_types=["QA"],
                include_metrics=False,
            )
            self.assertEqual(first.result()["status"], "success")
            self.assertEqual(second.result()["status"], "success")

        self.assertEqual(synthesizer.max_active, 1)

    def test_warmup_initializes_model_and_runs_qa_probe(self):
        synthesizer = _WarmupTrackingSynthesizer()
        service = SynthesisService(synthesizer=synthesizer)

        warmed = service.warmup()

        self.assertTrue(warmed["ready"])
        self.assertEqual(synthesizer.calls[0][0], "QA")
        self.assertTrue(synthesizer.calls[0][1][0])

    @patch("data_synthesis_service.core.subprocess.run")
    def test_subprocess_mode_serializes_service_requests(self, run_mock):
        active = 0
        max_active = 0
        lock = threading.Lock()

        def slow_subprocess(*args, **kwargs):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.1)
            with lock:
                active -= 1
            return CompletedProcess(
                args=["python"],
                returncode=0,
                stdout='{"status":"success","source_file":"case.txt","task_types":["QA"],"results":{"QA":[],"CoT":[],"Preference":[]},"metrics":{}}',
                stderr="",
            )

        run_mock.side_effect = slow_subprocess
        with patch.dict(
            os.environ,
            {
                "DATA_SYNTHESIS_MODEL_PATH": "/models/demo",
                "DATA_SYNTHESIS_RUN_MODE": "subprocess",
                "DATA_SYNTHESIS_FORCE_SUBPROCESS": "true",
            },
            clear=False,
        ):
            service = SynthesisService()
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(
                    service.synthesize_text,
                    "case-1.txt",
                    "患者出现头晕。",
                    ["QA"],
                    False,
                )
                second = executor.submit(
                    service.synthesize_text,
                    "case-2.txt",
                    "患者出现咳嗽。",
                    ["QA"],
                    False,
                )
                self.assertEqual(first.result()["status"], "success")
                self.assertEqual(second.result()["status"], "success")

        self.assertEqual(max_active, 1)

    def test_subprocess_env_defaults_to_hot_model_mode(self):
        with patch.dict(
            os.environ,
            {
                "DATA_SYNTHESIS_MODEL_PATH": "/models/demo",
                "DATA_SYNTHESIS_RUN_MODE": "subprocess",
            },
            clear=False,
        ):
            service = SynthesisService(synthesizer=_FakeSynthesizer())

        self.assertEqual(service.run_mode, "inprocess")

    def test_model_initialization_and_generation_use_same_worker_thread(self):
        with patch.object(SynthesisService, "_build_synthesizer", side_effect=_ThreadAffinitySynthesizer):
            service = SynthesisService(model_path="/models/demo")
            first = service.synthesize_text(
                "case-1.txt",
                "患者出现头晕。",
                task_types=["QA"],
                include_metrics=False,
            )
            with ThreadPoolExecutor(max_workers=1) as executor:
                second = executor.submit(
                    service.synthesize_text,
                    "case-2.txt",
                    "患者出现咳嗽。",
                    ["QA"],
                    False,
                ).result()

        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")


if __name__ == "__main__":
    unittest.main()
