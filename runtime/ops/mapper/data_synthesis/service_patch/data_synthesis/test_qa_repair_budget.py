import json
import unittest

from data_synthesizer import MedicalDataSynthesizer


class _Candidate:
    def __init__(self, text):
        self.text = text


class _Result:
    def __init__(self, text):
        self.outputs = [_Candidate(text)]


class _BudgetAwareQALLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        if self.calls == 1:
            return [_Result("这是模型生成的问答回答，但不是 JSON。请不要自行调整药物，应由医生评估。")]

        kwargs = getattr(sampling_params, "kwargs", {})
        max_tokens = int(kwargs.get("max_tokens", getattr(sampling_params, "max_tokens", 0)))
        full_json = json.dumps(
            {
                "question": "踝部水肿和血压升高时是否需要调整用药？",
                "answer": "轻度踝部水肿和血压145/92mmHg需要结合复诊评估。请记录家庭血压和水肿变化，不要自行调整药物，应由医生评估是否调整用药方案。",
            },
            ensure_ascii=False,
        )
        if max_tokens < 500:
            return [_Result(full_json[:80])]
        return [_Result(full_json)]


class QARepairBudgetTests(unittest.TestCase):
    def test_qa_repair_budget_allows_complete_json_from_llm_repair(self):
        source = (
            "患者咨询文本：56岁，高血压多年，服用氨氯地平控制血压。"
            "最近一周轻度踝部水肿，血压145/92mmHg左右，询问是否需要调整用药。"
        )
        llm = _BudgetAwareQALLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("QA", [source])[0]

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(llm.calls, 1)
        answer = result["data"]["answer"]
        self.assertIn("不要自行调整药物", answer)
        self.assertIn("医生评估", answer)


    def test_pubmedqa_preference_long_model_json_preserves_detailed_model_output(self):
        source = (
            "Source style: PubMedQA (biomedical research QA)\n\n"
            "Research question:\n"
            "Can home blood pressure telemonitoring improve blood pressure control in patients "
            "with hypertension compared with usual care?\n\n"
            "Abstract-style context:\n"
            "Several randomized studies have evaluated home blood pressure telemonitoring for "
            "adults with hypertension. The intervention usually combines home measurements, "
            "remote transmission of readings, and clinician feedback. Reported outcomes commonly "
            "include systolic blood pressure reduction, medication adjustment, and adherence to "
            "long-term follow-up.\n\n"
            "Acceptance target:\n"
            "Generate QA, CoT, and Preference records from the text above."
        )
        raw = json.dumps(
            {
                "question": (
                    "Can home blood pressure telemonitoring improve blood pressure control in "
                    "patients with hypertension compared with usual care?"
                ),
                "chosen": (
                    "Yes, home blood pressure telemonitoring can improve blood pressure control "
                    "in patients with hypertension. Several randomized studies have shown that "
                    "this method leads to a reduction in systolic blood pressure, increased "
                    "adherence to treatment plans, and better long-term management of the "
                    "condition. The intervention typically involves home blood pressure "
                    "measurements, remote transmission of data to healthcare providers, and "
                    "personalized feedback to patients."
                ),
                "rejected": (
                    "No, home blood pressure telemonitoring does not improve blood pressure "
                    "control in patients with hypertension compared with usual care. While some "
                    "studies suggest it may help, the evidence is inconclusive, and there are no "
                    "clear indications that it provides a significant advantage over standard care."
                ),
                "preference_reason": (
                    "The chosen answer is better because it is consistent with the abstract-style "
                    "context and mentions home measurements, remote transmission, clinician "
                    "feedback, systolic blood pressure reduction, medication adjustment, and "
                    "long-term adherence. The rejected answer contradicts the source by denying "
                    "benefit without using the reported outcomes."
                ),
            },
            ensure_ascii=False,
        ) + "<|endoftext|>"
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())

        parsed = synth._try_parse_and_validate("Preference", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("home blood pressure telemonitoring", parsed["chosen"])
        self.assertIn("remote transmission of data to healthcare providers", parsed["chosen"])
        self.assertIn("clear indications that it provides a significant advantage", parsed["rejected"])
        self.assertIn("The chosen answer is better", parsed["preference_reason"])
        self.assertIn("long-term adherence", parsed["preference_reason"])

    def test_chinese_preference_reason_with_unescaped_inner_quotes_is_repaired(self):
        source = (
            "患者咨询：我今年56岁，有多年高血压病史，最近一周晨起血压多在145/92mmHg左右，"
            "偶尔头晕，没有胸痛。"
        )
        raw = (
            '{"question":"患者咨询：我今年56岁，有多年高血压病史，最近一周晨起血压多在145/92mmHg左右，偶尔头晕，没有胸痛。",'
            '"chosen":"建议记录家庭血压和头晕变化，按医嘱复诊评估是否调整降压方案。",'
            '"rejected":"信息不足，无法给出任何建议。",'
            '"preference_reason":"chosen"提供了更具体的血压监测和复诊建议，而rejected过于笼统。"}<|endoftext|>'
        )
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())

        parsed = synth._try_parse_and_validate("Preference", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("更具体", parsed["preference_reason"])
        self.assertIn("复诊", parsed["chosen"])


if __name__ == "__main__":
    unittest.main()
