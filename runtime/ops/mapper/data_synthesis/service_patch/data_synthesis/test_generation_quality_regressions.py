import unittest

from data_synthesizer import MedicalDataSynthesizer


class GenerationQualityRegressionTests(unittest.TestCase):
    def test_qa_demographic_extraction_is_invalid_for_diagnostic_source(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "测试编号：DS-10\n"
            "数据来源风格：中文临床病例公开样式\n\n"
            "病例摘要：女，45岁，反复上腹痛半年，餐后加重，胃镜提示胃窦溃疡，幽门螺杆菌阳性。"
            "请生成诊疗思路相关的合成数据。"
        )
        parsed = {
            "question": "患者性别如何？",
            "answer": "该患者性别为女性。",
        }

        normalized = synth._normalize_parsed_data("QA", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertFalse(synth._validate_generated_data("QA", normalized, source))

    def test_preference_stringified_payload_is_normalized_to_plain_text(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者咨询：孕24周，最近出现轻度贫血，血红蛋白102g/L，担心补铁影响胎儿。"
            "请围绕孕期贫血科普生成中文QA、CoT和Preference。"
        )
        parsed = {
            "question": "孕24周，最近出现轻度贫血，血红蛋白102g/L，担心补铁影响胎儿。",
            "chosen": (
                "{'QA': '孕期贫血是否需要补铁？', "
                "'CoT': '孕期贫血是指孕妇血红蛋白水平低于正常范围，可能导致胎儿生长受限、早产等风险。', "
                "'Preference': '孕期贫血确实需要关注，但轻度贫血通过合理补铁是可以控制的。'}"
            ),
            "rejected": (
                "{'QA': '孕期贫血是否会导致胎儿畸形？', "
                "'CoT': '孕期贫血可能会导致胎儿生长受限、早产等问题，但不会直接导致胎儿畸形。', "
                "'Preference': '此问题偏离了贫血的直接处理，且贫血与胎儿畸形无直接因果关系。'}"
            ),
            "preference_reason": "chosen 更贴近患者问题，rejected 偏离了贫血的直接处理。",
        }

        normalized = synth._normalize_parsed_data("Preference", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertEqual(
            normalized["chosen"],
            "孕期贫血确实需要关注，但轻度贫血通过合理补铁是可以控制的。",
        )
        self.assertEqual(
            normalized["rejected"],
            "此问题偏离了贫血的直接处理，且贫血与胎儿畸形无直接因果关系。",
        )
        self.assertTrue(synth._validate_generated_data("Preference", normalized, source))


if __name__ == "__main__":
    unittest.main()
