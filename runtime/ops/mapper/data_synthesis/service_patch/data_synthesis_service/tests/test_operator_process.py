import json
import importlib.util
import os
import sys
import unittest
from unittest.mock import Mock


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
WORK_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))
if WORK_ROOT not in sys.path:
    sys.path.insert(0, WORK_ROOT)


def _load_operator_module():
    candidate_paths = [
        os.path.join(
            WORK_ROOT,
            "submit",
            "data_synthesis_delivery",
            "operator_src",
            "process.py",
        ),
        os.path.join(
            os.path.dirname(PROJECT_ROOT),
            "operator_src",
            "process.py",
        ),
        os.path.join(
            os.path.dirname(os.path.dirname(PROJECT_ROOT)),
            "operator_src",
            "process.py",
        ),
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
        self.assertEqual(mapper.timeout_sec, 300)
