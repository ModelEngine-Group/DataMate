import unittest

from data_synthesizer import MedicalDataSynthesizer


class QAPublicCaseQualityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())

    def test_diabetes_lifestyle_answer_should_not_expand_into_long_plan(self):
        source = (
            "患者咨询：2型糖尿病患者空腹血糖经常在8.2mmol/L左右，餐后血糖偏高，"
            "最近想了解饮食控制和运动安排。"
        )
        parsed = {
            "question": "该病例最需要关注什么？",
            "answer": (
                "饮食控制和运动安排是2型糖尿病管理的关键。需要制定一个合理的饮食计划，确保摄入适量的"
                "碳水化合物、蛋白质和脂肪，同时增加膳食纤维的摄入，比如全谷物和蔬菜。其次，建议进行"
                "适量的运动，如快走、游泳或骑自行车，以帮助控制血糖水平。此外，定期监测血糖是非常"
                "重要的，以便及时调整治疗方案。"
            ),
        }

        normalized = self.synth._normalize_parsed_data("QA", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertLessEqual(len(normalized["answer"]), 120)

    def test_thyroid_nodule_answer_should_not_over_elaborate(self):
        source = "患者咨询：甲状腺结节超声提示TI-RADS 4A，大小0.8cm，没有明显症状，担心是否需要穿刺。"
        parsed = {
            "question": "该情况应如何评估与处理？",
            "answer": (
                "对于TI-RADS 4A级的甲状腺结节，通常建议进行细针穿刺活检以明确诊断。如果结节大小超过"
                "1.0cm，或者有恶性征象，如血流丰富、微钙化、坏死或囊性变等，穿刺的必要性会更高。"
                "您提到的0.8cm大小，虽然接近1.0cm，但可能仍需考虑进一步检查。建议您与主治医生详细"
                "讨论，根据具体情况决定是否需要进行穿刺。"
            ),
        }

        normalized = self.synth._normalize_parsed_data("QA", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertLessEqual(len(normalized["answer"]), 120)

    def test_perimenopause_answer_should_not_expand_generic_management(self):
        source = "病例摘要：女，52岁，近半年月经紊乱、潮热盗汗、情绪波动，想了解围绝经期管理。"
        parsed = {
            "question": "该病例最需要关注什么？",
            "answer": (
                "围绝经期管理，特别是针对女性患者，需要综合考虑她的症状和整体健康状况。要评估她的"
                "月经紊乱、潮热盗汗和情绪波动等围绝经期症状，这些症状可能与激素水平变化有关。其次，"
                "根据她的具体情况，制定个性化的管理方案，可能包括激素替代疗法、非药物治疗或其他"
                "辅助疗法。最后，确保她了解这些管理措施的有效性和可能的副作用，以提高她的依从性。"
            ),
        }

        normalized = self.synth._normalize_parsed_data("QA", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertLessEqual(len(normalized["answer"]), 120)


if __name__ == "__main__":
    unittest.main()
