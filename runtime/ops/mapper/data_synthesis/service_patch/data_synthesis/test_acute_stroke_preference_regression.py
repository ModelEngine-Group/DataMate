import unittest

from data_synthesizer import MedicalDataSynthesizer


class AcuteStrokePreferenceRegressionTests(unittest.TestCase):
    def test_accepts_rejected_answer_that_omits_reperfusion_as_low_quality(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "测试编号：DS-13\n"
            "病例摘要：男，72岁，突发言语不清和右侧肢体无力2小时，"
            "高血压病史，头颅CT未见出血。请生成急性脑卒中评估相关数据。"
        )
        parsed = {
            "question": "该患者急诊卒中处理应如何判断？",
            "chosen": (
                "患者符合急性缺血性卒中可能，应立即进入卒中中心流程，"
                "评估静脉溶栓时间窗和禁忌证，必要时评估机械取栓，并同步管理血压和血糖。"
            ),
            "rejected": (
                "仅建议回家观察或普通门诊随访，未及时进行卒中中心评估，"
                "遗漏溶栓时间窗、机械取栓和再灌注治疗评估。"
            ),
            "preference_reason": (
                "chosen 结合突发神经功能缺损和CT未见出血，及时覆盖溶栓、取栓及再灌注评估；"
                "rejected 延误急性卒中处置并遗漏关键时间窗。"
            ),
        }

        normalized = synth._normalize_parsed_data("Preference", parsed, source)

        self.assertIsNotNone(normalized)
        self.assertTrue(synth._validate_generated_data("Preference", normalized, source))


if __name__ == "__main__":
    unittest.main()
