import json
import os
import sys
import unittest
from unittest.mock import patch


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_synthesis_service.core import DEFAULT_EVALUATION_DIMENSIONS, SynthesisService


class _FakeSynthesizer:
    pass


class _FakeEvaluator:
    def __init__(self, backend):
        self.backend = backend
        self.model_path = "/model/evaluator"

    def evaluate(self, data_list, target_dimensions=None):
        dimensions = list(target_dimensions or DEFAULT_EVALUATION_DIMENSIONS)
        return [
            {
                "id": 1,
                "scores": {
                    dimension: {"score": 1, "reason": "ok"}
                    for dimension in dimensions
                },
            }
        ]

    def runtime_metadata(self):
        return {
            "evaluator_backend": self.backend,
            "evaluator_model_path": self.model_path,
            "vllm_enabled": self.backend == "vllm",
            "visible_npus": "6",
        }


class EvaluatorBackendServiceTests(unittest.TestCase):
    @patch("data_synthesis_service.core.MedicalDataEvaluator")
    def test_evaluate_file_initializes_evaluator_with_vllm_backend(self, evaluator_cls):
        evaluator_cls.side_effect = lambda model_path, **kwargs: _FakeEvaluator(kwargs["backend"])
        service = SynthesisService(synthesizer=_FakeSynthesizer())

        result = service.evaluate_text(
            "records.json",
            json.dumps([{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}]),
        )

        self.assertEqual(evaluator_cls.call_args.kwargs["backend"], "vllm")
        self.assertEqual(result["runtime"]["evaluator_backend"], "vllm")
        self.assertTrue(result["runtime"]["vllm_enabled"])

    @patch("data_synthesis_service.core.MedicalDataEvaluator")
    def test_metrics_initializes_rule_backend(self, evaluator_cls):
        evaluator_cls.side_effect = lambda model_path, **kwargs: _FakeEvaluator(kwargs["backend"])
        service = SynthesisService(synthesizer=_FakeSynthesizer())

        metrics = service._build_metrics(
            records=[{"task_type": "QA", "status": "success", "latency": 1.0, "data": {"question": "q", "answer": "a"}}],
            evaluation_inputs=[{"type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}],
        )

        self.assertEqual(evaluator_cls.call_args.kwargs["backend"], "rule")
        self.assertTrue(metrics["ready"])


if __name__ == "__main__":
    unittest.main()
