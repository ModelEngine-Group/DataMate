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

from data_quality_evaluator_service.core import DataQualityEvaluatorService


class _FakeEvaluator:
    backend = "vllm"

    def evaluate(self, data_list, target_dimensions=None):
        dimensions = list(target_dimensions or ["准确性"])
        return [
            {
                "id": 1,
                "scores": {dimension: {"score": 1, "reason": "ok"} for dimension in dimensions},
            }
        ]

    def runtime_metadata(self):
        return {
            "evaluator_backend": self.backend,
            "evaluator_model_path": "/model/Qwen/Qwen2.5-7B-Instruct",
            "vllm_enabled": True,
            "visible_npus": "6",
        }


class DataQualityEvaluatorCoreTests(unittest.TestCase):
    @patch("data_quality_evaluator_service.core.subprocess.run")
    def test_vllm_evaluation_routes_to_isolated_worker(self, run_mock):
        run_mock.return_value = CompletedProcess(
            args=["python"],
            returncode=0,
            stdout='__DATA_QUALITY_EVALUATOR_RESULT__{"status":"success","runtime":{"evaluator_backend":"vllm","vllm_enabled":true}}',
            stderr="",
        )
        service = DataQualityEvaluatorService()

        result = service.evaluate_text(
            "records.json",
            json.dumps([{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}]),
        )

        run_mock.assert_called_once()
        self.assertEqual(result["runtime"]["evaluator_backend"], "vllm")
        self.assertTrue(result["runtime"]["vllm_enabled"])

    def test_rule_backend_can_evaluate_inprocess(self):
        service = DataQualityEvaluatorService(evaluator=_FakeEvaluator())

        result = service.evaluate_text(
            "records.json",
            json.dumps([{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}]),
            backend="rule",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["record_count"], 1)
        self.assertIn("准确性", result["summary"]["dimensions"])


if __name__ == "__main__":
    unittest.main()
