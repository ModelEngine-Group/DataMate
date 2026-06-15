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
    def __init__(self):
        self.last_include_metrics = None
        self.warmup_calls = 0

    def health(self):
        return {"ready": True, "model_path": "/models/demo", "service": "data_synthesis"}

    def warmup(self):
        self.warmup_calls += 1
        return self.health()

    def synthesize_text(self, file_name, text, task_types=None, include_metrics=True):
        self.last_include_metrics = include_metrics
        return {
            "source_file": file_name,
            "task_types": task_types or ["QA", "CoT", "Preference"],
            "results": {"QA": [], "CoT": [], "Preference": []},
            "metrics": {} if include_metrics else None,
            "status": "success",
        }


class AppTests(unittest.TestCase):
    def test_app_warmup_runs_on_startup(self):
        fake_service = _FakeService()
        with TestClient(create_app(service=fake_service)):
            pass
        self.assertEqual(fake_service.warmup_calls, 1)

    def test_app_can_skip_warmup_via_env(self):
        fake_service = _FakeService()
        original = os.environ.get("DATA_SYNTHESIS_SKIP_WARMUP")
        os.environ["DATA_SYNTHESIS_SKIP_WARMUP"] = "true"
        try:
            with TestClient(create_app(service=fake_service)):
                pass
        finally:
            if original is None:
                os.environ.pop("DATA_SYNTHESIS_SKIP_WARMUP", None)
            else:
                os.environ["DATA_SYNTHESIS_SKIP_WARMUP"] = original
        self.assertEqual(fake_service.warmup_calls, 0)

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
        fake_service = _FakeService()
        client = TestClient(create_app(service=fake_service))
        response = client.post(
            "/synthesize-file",
            json={"file_name": "demo.txt", "text": "abc"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_file"], "demo.txt")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(fake_service.last_include_metrics, False)

    def test_evaluate_endpoint_is_not_exposed_by_synthesis_service(self):
        client = TestClient(create_app(service=_FakeService()))
        response = client.post(
            "/evaluate-file",
            json={"file_name": "demo.json", "text": '{"content":"{}"}'},
        )
        self.assertEqual(response.status_code, 404)
