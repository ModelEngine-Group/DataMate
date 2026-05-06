import json
import unittest
import os
import sys
import importlib.util
from collections import Counter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from data_synthesizer import MedicalDataSynthesizer
from data_evaluator import MedicalDataEvaluator

_metrics_path = os.path.join(CURRENT_DIR, "requirement_metrics.py")
_spec = importlib.util.spec_from_file_location("requirement_metrics", _metrics_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("无法加载 requirement_metrics.py")
requirement_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(requirement_metrics)

calculate_generation_metrics = requirement_metrics.calculate_generation_metrics
check_project_targets = requirement_metrics.check_project_targets


class _FakeCandidate:
    def __init__(self, text: str):
        self.text = text


class _FakeResult:
    def __init__(self, text: str):
        self.outputs = [_FakeCandidate(text)]


class FakeLLM:
    def generate(self, prompts, sampling_params):
        results = []
        for i, prompt in enumerate(prompts):
            if "偏好学习样本" in prompt:
                payload = {
                    "question": f"偏好问题{i}",
                    "chosen": "高质量回答：给出循证建议并提醒就医。",
                    "rejected": "低质量回答：建议忽略症状。",
                    "preference_reason": "chosen 更准确、安全、完整。",
                }
            elif "思维链推理" in prompt:
                payload = {
                    "question": f"CoT问题{i}",
                    "rationale": "症状->检查->诊断->治疗，链路清晰。",
                    "final_answer": "建议先检查再对症治疗。",
                }
            else:
                payload = {
                    "question": f"QA问题{i}",
                    "answer": "这是一个完整且相关的回答。",
                }
            results.append(_FakeResult(json.dumps(payload, ensure_ascii=False)))
        return results


class ProjectRequirementTests(unittest.TestCase):
    def test_support_three_generation_templates(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())

        qa_res = synth.generate_data_batch("QA", ["病例A", "病例B"])
        cot_res = synth.generate_data_batch("CoT", ["病例C", "病例D"])
        pref_res = synth.generate_data_batch("Preference", ["病例E", "病例F"])

        for group in [qa_res, cot_res, pref_res]:
            self.assertTrue(all(x["status"] == "success" for x in group))

        self.assertIn("answer", qa_res[0]["data"])
        self.assertIn("rationale", cot_res[0]["data"])
        self.assertIn("chosen", pref_res[0]["data"])
        self.assertIn("rejected", pref_res[0]["data"])

    def test_data_augmentation_distillation_mixing_ratio(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = [f"患者{i}，主诉咳嗽3天。" for i in range(10)]

        mixed = synth.build_training_corpus(
            raw_inputs=raw,
            target_size=50,
            source_ratio={"original": 0.4, "augmented": 0.4, "distilled": 0.2},
            seed=7,
        )

        self.assertEqual(len(mixed), 50)
        source_count = Counter([x["source"] for x in mixed])
        self.assertEqual(source_count["original"], 20)
        self.assertEqual(source_count["augmented"], 20)
        self.assertEqual(source_count["distilled"], 10)

        self.assertTrue(any(x["text"].startswith("[蒸馏]") for x in mixed if x["source"] == "distilled"))

    def test_requirement_metrics_reach_targets(self):
        records = []
        for i in range(6):
            task_type = "QA" if i < 2 else ("CoT" if i < 4 else "Preference")
            if task_type == "QA":
                data = {"question": f"问题{i}", "answer": "完整回答"}
            elif task_type == "CoT":
                data = {"question": f"问题{i}", "rationale": "推理链", "final_answer": "结论"}
            else:
                data = {
                    "question": f"问题{i}",
                    "chosen": "优质答案",
                    "rejected": "劣质答案",
                    "preference_reason": "优质答案更准确",
                }

            records.append({
                "task_type": task_type,
                "status": "success",
                "latency": 2.1,
                "data": data,
            })

        evaluator_scores = [
            {
                "scores": {
                    "准确性": {"score": 1},
                    "相关性": {"score": 1},
                    "安全性": {"score": 1},
                    "多样性": {"score": 1},
                    "完整性": {"score": 1},
                }
            }
            for _ in range(6)
        ]

        metrics = calculate_generation_metrics(records, evaluator_scores)
        targets = check_project_targets(metrics)

        self.assertGreaterEqual(metrics["accuracy_pct"], 90)
        self.assertGreaterEqual(metrics["relevance_pct"], 95)
        self.assertGreaterEqual(metrics["safety_pct"], 95)
        self.assertGreaterEqual(metrics["diversity_pct"], 85)
        self.assertGreaterEqual(metrics["completeness_pct"], 85)
        self.assertLessEqual(metrics["avg_latency_sec"], 3)
        self.assertEqual(metrics["format_integrity_pct"], 100)
        self.assertTrue(all(targets.values()))

    def test_evaluator_accuracy_binary_five_dimensions(self):
        golden = [
            {
                "human_scores": {
                    "准确性": 1,
                    "相关性": 1,
                    "安全性": 1,
                    "多样性": 1,
                    "完整性": 1,
                }
            }
        ]
        eval_results = [
            {
                "scores": {
                    "准确性": {"score": 1},
                    "相关性": {"score": 1},
                    "安全性": {"score": 1},
                    "多样性": {"score": 1},
                    "完整性": {"score": 1},
                }
            }
        ]

        summary = MedicalDataEvaluator.summarize_accuracy(
            eval_results,
            golden,
            ignore_dimensions=(),
            allowed_error=0,
        )
        self.assertEqual(summary["accuracy"], 100.0)


if __name__ == "__main__":
    unittest.main()
