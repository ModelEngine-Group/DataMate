import os
import sys
import unittest

from fastapi.testclient import TestClient


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_synthesis_service.app import create_app


class _FakeService:
    def health(self):
        return {"ready": True, "model_path": "/models/demo", "service": "data_synthesis"}

    def synthesize_text(self, file_name, text, task_types=None, include_metrics=True):
        return {
            "source_file": file_name,
            "task_types": task_types or ["QA", "CoT", "Preference"],
            "results": {"QA": [], "CoT": [], "Preference": []},
            "metrics": {} if include_metrics else None,
            "status": "success",
        }

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
            "status": "success",
        }


class AppTests(unittest.TestCase):
    def test_health_endpoint(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post("/health", json={})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ready"])

    def test_health_endpoint_supports_get(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ready"])

    def test_synthesize_endpoint(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post(
            "/synthesize-file",
            json={"file_name": "demo.txt", "text": "abc"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_file"], "demo.txt")
        self.assertEqual(payload["status"], "success")

    def test_evaluate_endpoint(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post(
            "/evaluate-file",
            json={"file_name": "demo.json", "text": '{"content":"{}"}'},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_file"], "demo.json")
        self.assertEqual(payload["status"], "success")

    def test_evaluate_endpoint_accepts_dedicated_model_path(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post(
            "/evaluate-file",
            json={
                "file_name": "demo.json",
                "text": '{"content":"{}"}',
                "model_path": "/model/Qwen/Qwen2.5-7B-Instruct",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model_path"], "/model/Qwen/Qwen2.5-7B-Instruct")
