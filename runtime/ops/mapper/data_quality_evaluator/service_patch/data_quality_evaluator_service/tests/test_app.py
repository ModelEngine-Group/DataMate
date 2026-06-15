import os
import sys
import unittest

from fastapi.testclient import TestClient


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_quality_evaluator_service.app import create_app


class _FakeService:
    def __init__(self):
        self.warmup_calls = 0

    def health(self):
        return {"ready": True, "service": "data_quality_evaluator"}

    def warmup(self):
        self.warmup_calls += 1
        return self.health()

    def evaluate_text(
        self,
        file_name,
        text,
        target_dimensions=None,
        include_summary=True,
        model_path=None,
        backend=None,
    ):
        return {
            "source_file": file_name,
            "record_count": 1,
            "dimensions": target_dimensions or ["准确性", "相关性", "安全性", "多样性", "完整性"],
            "results": [{"id": 1, "scores": {"准确性": {"score": 1, "reason": "ok"}}}],
            "summary": {"record_count": 1} if include_summary else None,
            "model_path": model_path,
            "backend": backend,
            "status": "success",
        }


class DataQualityEvaluatorAppTests(unittest.TestCase):
    def test_app_warmup_runs_on_startup(self):
        fake_service = _FakeService()
        with TestClient(create_app(service=fake_service)):
            pass
        self.assertEqual(fake_service.warmup_calls, 1)

    def test_health_endpoint(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "data_quality_evaluator")

    def test_evaluate_endpoint(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post(
            "/evaluate-file",
            json={
                "file_name": "demo.json",
                "text": '{"content":"{}"}',
                "model_path": "/model/Qwen/Qwen2.5-7B-Instruct",
                "backend": "vllm",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_file"], "demo.json")
        self.assertEqual(payload["model_path"], "/model/Qwen/Qwen2.5-7B-Instruct")


if __name__ == "__main__":
    unittest.main()
