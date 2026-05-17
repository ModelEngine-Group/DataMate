import json
import os
import sys
import unittest


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from data_evaluator import MedicalDataEvaluator


class _FakeCandidate:
    def __init__(self, text):
        self.text = text


class _FakeResult:
    def __init__(self, text):
        self.outputs = [_FakeCandidate(text)]


class EvaluatorBackendTests(unittest.TestCase):
    def test_vllm_backend_calls_llm_generate(self):
        class CountingLLM:
            def __init__(self):
                self.calls = 0
                self.prompt_count = 0
                self.prompts = []

            def generate(self, prompts, sampling_params):
                self.calls += 1
                self.prompt_count += len(prompts)
                self.prompts.extend(prompts)
                return [
                    _FakeResult(json.dumps({"score": 1, "reason": "model judged pass"}))
                    for _ in prompts
                ]

        llm = CountingLLM()
        evaluator = MedicalDataEvaluator(
            model_path=None,
            llm_instance=llm,
            backend="vllm",
        )
        dimension = next(iter(evaluator.dimension_criteria))

        results = evaluator.evaluate(
            [{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}],
            target_dimensions=[dimension],
        )

        self.assertEqual(llm.calls, 1)
        self.assertEqual(llm.prompt_count, 1)
        self.assertIn('"sample_type": "QA"', llm.prompts[0])
        self.assertIn('"question": "q"', llm.prompts[0])
        self.assertIn('"answer": "a"', llm.prompts[0])
        self.assertIn('"question_present": true', llm.prompts[0])
        self.assertIn('"answer_present": true', llm.prompts[0])
        self.assertIn("禁止把该字段判定为空", llm.prompts[0])
        self.assertNotIn('"rationale"', llm.prompts[0])
        self.assertNotIn('"raw_content"', llm.prompts[0])
        self.assertEqual(results[0]["scores"][dimension]["score"], 1)

    def test_rule_backend_does_not_call_llm_generate(self):
        class FailingLLM:
            def generate(self, prompts, sampling_params):
                raise AssertionError("rule backend must not call LLM.generate")

        evaluator = MedicalDataEvaluator(
            model_path=None,
            llm_instance=FailingLLM(),
            backend="rule",
        )
        dimension = next(iter(evaluator.dimension_criteria))

        results = evaluator.evaluate(
            [{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}],
            target_dimensions=[dimension],
        )

        self.assertIn(dimension, results[0]["scores"])

    def test_vllm_backend_corrects_obvious_empty_field_misread(self):
        class EmptyFieldMisreadLLM:
            def generate(self, prompts, sampling_params):
                return [
                    _FakeResult(json.dumps({"score": 0, "reason": "问题和答案字段内容为空"}))
                    for _ in prompts
                ]

        evaluator = MedicalDataEvaluator(
            model_path=None,
            llm_instance=EmptyFieldMisreadLLM(),
            backend="vllm",
        )
        dimension = next(iter(evaluator.dimension_criteria))

        results = evaluator.evaluate(
            [{"id": 1, "type": "QA", "content": json.dumps({"question": "q", "answer": "a"})}],
            target_dimensions=[dimension],
        )

        self.assertEqual(results[0]["scores"][dimension]["score"], 1)
        self.assertIn("llm_consistency_corrected", results[0]["scores"][dimension]["reason"])


if __name__ == "__main__":
    unittest.main()
