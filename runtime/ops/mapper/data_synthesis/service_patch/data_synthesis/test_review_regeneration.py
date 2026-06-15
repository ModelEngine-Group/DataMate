import json
import unittest

from data_synthesizer import MedicalDataSynthesizer


class _Candidate:
    def __init__(self, text):
        self.text = text


class _Result:
    def __init__(self, text):
        self.outputs = [_Candidate(text)]


class _InvalidTwiceThenValidCotLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        if self.calls == 1:
            return [_Result("not json")]
        if self.calls == 2:
            return [_Result(json.dumps({"question": "患者应如何处理？", "rationale": "1. 信息不足。"}, ensure_ascii=False))]
        if self.calls == 3:
            return [_Result(json.dumps({"question": "患者应如何处理？", "final_answer": "继续观察。"}, ensure_ascii=False))]
        return [
            _Result(json.dumps({
                "question": "患者出现胸痛时应如何评估和处理？",
                "rationale": (
                    "1. 患者出现胸痛，需要首先识别急性心血管事件风险。"
                    "2. 需要结合发作时间、疼痛性质和伴随症状判断紧急程度。"
                    "3. 应尽快完善生命体征、心电图和必要的心肌损伤标志物检查。"
                    "4. 若存在持续胸痛或检查异常，应及时进入急诊或专科评估流程。"
                    "5. 在病因未明确前，不建议患者自行调整或追加药物治疗。"
                    "6. 后续处理应依据检查结果和医生评估选择观察、药物或进一步介入评估。"
                ),
                "final_answer": "建议先进行急诊或心内科评估，结合心电图和相关检查明确原因后再制定处理方案。",
            }, ensure_ascii=False))
        ]


class _AlwaysInvalidLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        return [_Result("not json")]


class _GroinCotSuffixLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        suffix = (
            "1. 患者49岁男性，解大便后突发右下腹疼痛3小时，提示急性腹部外科问题。"
            "2. 右侧腹股沟区可触及4cm包块，说明病变集中在腹股沟疝相关区域。"
            "3. 腹股沟包块与右下腹痛同时出现，支持腹股沟疝发生嵌顿的可能。"
            "4. 腹部X线见阶梯状液气平，提示已经存在肠梗阻表现。"
            "5. 将腹股沟包块和肠梗阻影像结合，最符合嵌顿性腹股沟疝合并肠梗阻。"
            "6. 该情况存在持续嵌顿和肠梗阻风险，需要及时处理。"
            "7. 处理上需要尽快外科评估，判断是否需要急诊处理。"
            "8. 处置建议应聚焦及时外科评估，避免延误。"
            '","final_answer":"考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"}'
        )
        return [_Result(suffix) for _ in prompts]


class ReviewRegenerationTests(unittest.TestCase):
    def test_groin_cot_accepts_model_completion_after_prefilled_json_prefix(self):
        source = (
            "病例摘要：49岁男性，解大便后突发右下腹疼痛3小时，"
            "右侧腹股沟区可触及4cm包块，腹部X线见阶梯状液气平。"
        )
        llm = _GroinCotSuffixLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("CoT", [source])[0]

        self.assertEqual(result["status"], "success")
        self.assertIn("嵌顿性腹股沟疝", result["data"]["final_answer"])
        self.assertIn("外科评估", result["data"]["final_answer"])

    def test_cot_review_regeneration_after_two_failed_repairs_returns_success(self):
        llm = _InvalidTwiceThenValidCotLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("CoT", ["患者男，58岁，突发胸痛，需要生成临床推理数据。"])[0]

        self.assertGreaterEqual(llm.calls, 4)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["repaired"])
        self.assertTrue(result["review_regenerated"])
        self.assertNotIn("failed", json.dumps(result, ensure_ascii=False).lower())

    def test_exhausted_review_regeneration_raises_instead_of_emitting_failed_record(self):
        llm = _AlwaysInvalidLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        with self.assertRaises(RuntimeError):
            synth.generate_data_batch("CoT", ["患者男，58岁，突发胸痛，需要生成临床推理数据。"])


if __name__ == "__main__":
    unittest.main()
