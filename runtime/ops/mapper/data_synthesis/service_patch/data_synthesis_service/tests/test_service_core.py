import json
import os
import sys
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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


class _FakeEvaluator:
    def evaluate(self, data_list, target_dimensions=None):
        return [
            {
                "scores": {
                    "准确性": {"score": 1},
                    "相关性": {"score": 1},
                    "安全性": {"score": 1},
                    "多样性": {"score": 1},
                    "完整性": {"score": 1},
                }
            }
            for _ in data_list
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
        if task_type == "CoT":
            return [
                {
                    "status": "failed",
                    "reason": "repair_failed",
                    "raw_output": "<think>meta reasoning</think> noisy output",
                    "repair_raw_output": "<think>meta reasoning</think> noisy output",
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


class ServiceCoreTests(unittest.TestCase):
    def test_synthesize_text_returns_all_task_groups(self):
        service = SynthesisService(
            synthesizer=_FakeSynthesizer(),
            evaluator=_FakeEvaluator(),
        )
        result = service.synthesize_text("case.txt", "patient text")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_file"], "case.txt")
        self.assertEqual(result["task_types"], ["QA", "CoT", "Preference"])
        self.assertEqual(len(result["results"]["QA"]), 1)
        self.assertEqual(len(result["results"]["CoT"]), 1)
        self.assertEqual(len(result["results"]["Preference"]), 1)
        self.assertIn("metrics", result)

    def test_invalid_task_type_raises(self):
        service = SynthesisService(
            synthesizer=_FakeSynthesizer(),
            evaluator=_FakeEvaluator(),
        )
        with self.assertRaises(ValueError):
            service.synthesize_text("case.txt", "patient text", task_types=["BAD"])

    def test_empty_text_raises(self):
        service = SynthesisService(
            synthesizer=_FakeSynthesizer(),
            evaluator=_FakeEvaluator(),
        )
        with self.assertRaises(ValueError):
            service.synthesize_text("case.txt", "   ")

    @patch("data_synthesis_service.core.MedicalDataEvaluator")
    @patch("data_synthesis_service.core.MedicalDataSynthesizer")
    def test_service_can_initialize_with_cpu_fallback(self, synthesizer_cls, evaluator_cls):
        synthesizer_cls.return_value = _FakeSynthesizer()
        evaluator_cls.return_value = _FakeEvaluator()
        with patch.dict(os.environ, {"DATA_SYNTHESIS_MODEL_PATH": "/models/demo"}, clear=False):
            service = SynthesisService()
        self.assertTrue(service.health()["ready"])
        self.assertEqual(service.evaluator_model_path, "/model/Qwen/Qwen2.5-7B-Instruct")

    def test_health_retries_initialization_after_transient_failure(self):
        builder = _FlakySynthesizer()
        with patch.object(SynthesisService, "_build_synthesizer", side_effect=builder):
            with patch("data_synthesis_service.core.MedicalDataEvaluator", return_value=_FakeEvaluator()):
                with patch.dict(os.environ, {"DATA_SYNTHESIS_MODEL_PATH": "/models/demo"}, clear=False):
                    service = SynthesisService()
                    first = service.health()
                    self.assertTrue(first["ready"])
                    self.assertIsNone(first["error"])

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
            },
            clear=False,
        ):
            service = SynthesisService()
            result = service.synthesize_text("case.txt", "patient text", task_types=["QA"], include_metrics=False)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_file"], "case.txt")

    def test_evaluate_text_supports_synthesis_payload(self):
        service = SynthesisService(
            synthesizer=_FakeSynthesizer(),
            evaluator=_FakeEvaluator(),
        )
        text = """
{
  "results": {
    "QA": [
      {
        "status": "success",
        "data": {
          "question": "q",
          "answer": "a。"
        }
      }
    ],
    "CoT": [],
    "Preference": []
  }
}
"""
        result = service.evaluate_text("generated.json", text)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["summary"]["record_count"], 1)

    @patch("data_synthesis_service.core.subprocess.run")
    def test_evaluate_subprocess_uses_dedicated_evaluator_model_path(self, run_mock):
        run_mock.return_value = CompletedProcess(
            args=["python"],
            returncode=0,
            stdout='{"status":"success","source_file":"generated.json","record_count":1,"dimensions":["准确性"],"results":[],"summary":{"record_count":1}}',
            stderr="",
        )
        with patch.dict(
            os.environ,
            {
                "DATA_SYNTHESIS_MODEL_PATH": "/model/Qwen/Qwen3-1___7b-Medical-R1-sft",
                "DATA_EVALUATOR_MODEL_PATH": "/model/Qwen/Qwen2.5-7B-Instruct",
                "DATA_SYNTHESIS_RUN_MODE": "subprocess",
            },
            clear=False,
        ):
            service = SynthesisService()
            service.evaluate_text("generated.json", '[{"id":1,"type":"QA","content":"{\\"question\\":\\"q\\"}"}]')

        worker_payload = json.loads(run_mock.call_args.kwargs["input"])
        self.assertEqual(worker_payload["model_path"], "/model/Qwen/Qwen2.5-7B-Instruct")

    def test_synthesize_text_does_not_apply_service_level_deterministic_fallback(self):
        service = SynthesisService(
            synthesizer=_PubMedUnstableSynthesizer(),
            evaluator=_FakeEvaluator(),
        )
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


if __name__ == "__main__":
    unittest.main()
