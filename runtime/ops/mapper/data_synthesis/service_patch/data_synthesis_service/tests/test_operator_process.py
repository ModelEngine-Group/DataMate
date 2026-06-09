import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import patch


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
WORK_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))
if WORK_ROOT not in sys.path:
    sys.path.insert(0, WORK_ROOT)


def _load_operator_module():
    candidate_paths = [
        os.path.join(WORK_ROOT, "submit", "data_synthesis_delivery", "operator_src", "process.py"),
        os.path.join(os.path.dirname(PROJECT_ROOT), "operator_src", "process.py"),
        os.path.join(os.path.dirname(os.path.dirname(PROJECT_ROOT)), "operator_src", "process.py"),
    ]
    process_path = next((path for path in candidate_paths if os.path.isfile(path)), candidate_paths[0])
    spec = importlib.util.spec_from_file_location("data_synthesis_operator_process", process_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


operator_process = _load_operator_module()
DataSynthesisMapper = operator_process.DataSynthesisMapper
build_service_payload = operator_process.build_service_payload
serialize_service_response = operator_process.serialize_service_response


class OperatorHelperTests(unittest.TestCase):
    def test_mapper_defaults_to_hot_service_container(self):
        mapper = DataSynthesisMapper()
        self.assertEqual(mapper.service_url, "http://data-synthesis-service:18103")

    def test_mapper_rotates_across_service_url_pool(self):
        mapper = DataSynthesisMapper(serviceUrls="http://svc-a:18103,http://svc-b:18104")
        self.assertEqual(mapper.service_url, "http://svc-a:18103")
        self.assertEqual(mapper._next_service_url(), "http://svc-a:18103")
        self.assertEqual(mapper._next_service_url(), "http://svc-b:18104")
        self.assertEqual(mapper._next_service_url(), "http://svc-a:18103")

    def test_build_service_payload_prefers_sample_text(self):
        sample = {"fileName": "demo.txt", "text": "hello"}
        payload = build_service_payload(sample, ["QA"], True)
        self.assertEqual(payload["file_name"], "demo.txt")
        self.assertEqual(payload["text"], "hello")
        self.assertEqual(payload["task_types"], ["QA"])

    def test_serialize_service_response_returns_json_text(self):
        response = {"status": "success", "results": {"QA": []}}
        text = serialize_service_response(response)
        parsed = json.loads(text)
        self.assertEqual(parsed["status"], "success")

    def test_mapper_uses_higher_default_timeout_for_full_task_types(self):
        mapper = DataSynthesisMapper()
        self.assertEqual(mapper.timeout_sec, 3600)

    def test_mapper_uses_batch_safe_lock_wait(self):
        mapper = DataSynthesisMapper()
        self.assertEqual(mapper.lock_wait_timeout_sec, 7200)

    def test_mapper_clamps_stale_platform_lock_wait(self):
        mapper = DataSynthesisMapper(lockWaitTimeoutSec=300)
        self.assertEqual(mapper.lock_wait_timeout_sec, 7200)

    def test_mapper_upgrades_stale_platform_service_url(self):
        mapper = DataSynthesisMapper(serviceUrl="http://data-synthesis-service:18080")
        self.assertEqual(mapper.service_url, "http://data-synthesis-service:18103")

    def test_mapper_clamps_stale_platform_timeout(self):
        mapper = DataSynthesisMapper(timeoutSec=300)
        self.assertEqual(mapper.timeout_sec, 3600)

    def test_mapper_uses_service_specific_lock_path(self):
        mapper = DataSynthesisMapper()
        self.assertIn("18103", mapper.lock_path)
        self.assertNotEqual(mapper.lock_path, operator_process.DEFAULT_LOCK_PATH)
        self.assertFalse(mapper.use_service_lock)

    def test_mapper_disables_metrics_by_default_for_platform_batch(self):
        mapper = DataSynthesisMapper()
        sample = {"fileName": "demo.txt", "text": "sample text"}

        with patch.object(operator_process.requests, "post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"status": "success", "results": {"QA": []}}
            mapper.execute(sample)

        self.assertEqual(post.call_args.kwargs["json"]["include_metrics"], False)

    def test_mapper_uses_file_lock_for_service_call_when_explicitly_enabled(self):
        mapper = DataSynthesisMapper(useServiceLock=True)
        sample = {"fileName": "demo.txt", "text": "sample text"}

        with patch.object(operator_process, "service_call_lock") as lock_factory, patch.object(operator_process.requests, "post") as post:
            lock = lock_factory.return_value
            lock.__enter__.return_value = None
            lock.__exit__.return_value = None
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"status": "success", "results": {"QA": []}}
            mapper.execute(sample)

        lock_factory.assert_called_once_with(lock_path=mapper.lock_path, max_wait_sec=7200)
        lock.__enter__.assert_called_once()
        lock.__exit__.assert_called_once()

    def test_mapper_does_not_use_file_lock_by_default(self):
        mapper = DataSynthesisMapper()
        sample = {"fileName": "demo.txt", "text": "sample text"}

        with patch.object(operator_process, "service_call_lock") as lock_factory, patch.object(operator_process.requests, "post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"status": "success", "results": {"QA": []}}
            mapper.execute(sample)

        lock_factory.assert_not_called()

    def test_mapper_can_disable_file_lock_explicitly(self):
        mapper = DataSynthesisMapper(useServiceLock=False)
        sample = {"fileName": "demo.txt", "text": "sample text"}

        with patch.object(operator_process, "service_call_lock") as lock_factory, patch.object(operator_process.requests, "post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"status": "success", "results": {"QA": []}}
            mapper.execute(sample)

        lock_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
