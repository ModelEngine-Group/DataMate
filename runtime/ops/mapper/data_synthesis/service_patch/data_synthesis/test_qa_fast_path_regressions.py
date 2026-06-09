import unittest

from data_synthesizer import MedicalDataSynthesizer


class _Candidate:
    def __init__(self, text):
        self.text = text


class _Result:
    def __init__(self, text):
        self.outputs = [_Candidate(text)]


class _TruncatedQALLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        return [
            _Result(
                '{"question":"患者反复上腹痛半年最需要考虑什么？",'
                '"answer":"考虑胃窦溃疡合并幽门螺杆菌感染，建议规范根除治疗并复诊评估'
            )
        ]


class _GroinQALLM:
    def __init__(self):
        self.calls = 0
        self.last_prompt = None

    def generate(self, prompts, sampling_params):
        self.calls += 1
        self.last_prompt = prompts[0]
        return [
            _Result(
                '{"question":"该病例最可能的诊断和紧急处理是什么？",'
                '"answer":"考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"}'
            )
        ]


class QAFastPathRegressionTests(unittest.TestCase):
    def test_qa_prompt_omits_scaffolding_lines(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "测试编号：DS-10\n"
            "数据来源风格：中文临床病例公开样式\n\n"
            "病例摘要：女，45岁，反复上腹痛半年，餐后加重，胃镜提示胃窦溃疡，幽门螺杆菌阳性。"
            "请生成诊疗思路相关的合成数据。\n\n"
            "生成要求：请输出结构化中文结果，覆盖 QA、CoT、Preference 三类数据。"
        )

        prompt = synth._render_prompt("QA", source)

        self.assertIn("女，45岁，反复上腹痛半年", prompt)
        self.assertNotIn("测试编号", prompt)
        self.assertNotIn("数据来源风格", prompt)
        self.assertNotIn("生成要求", prompt)
        self.assertIn("Do not restate the full case in question.", prompt)

    def test_truncated_qa_json_is_salvaged_without_repair_roundtrip(self):
        source = (
            "测试编号：DS-10\n"
            "数据来源风格：中文临床病例公开样式\n\n"
            "病例摘要：女，45岁，反复上腹痛半年，餐后加重，胃镜提示胃窦溃疡，幽门螺杆菌阳性。"
            "请生成诊疗思路相关的合成数据。\n\n"
            "生成要求：请输出结构化中文结果，覆盖 QA、CoT、Preference 三类数据。"
        )
        llm = _TruncatedQALLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("QA", [source])[0]

        self.assertEqual(result["status"], "success")
        self.assertFalse(result.get("repaired", False))
        self.assertEqual(llm.calls, 1)
        self.assertIn("胃窦溃疡", result["data"]["answer"])
        self.assertIn("幽门螺杆菌", result["data"]["answer"])

    def test_groin_obstruction_qa_prompt_uses_specialized_constraints(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "测试编号：DS-03\n"
            "数据来源风格：medical-o1-reasoning-SFT\n\n"
            "病例摘要：49岁男性，解大便后突发右下腹疼痛3小时，右侧腹股沟区可触及4cm包块，"
            "腹部X线见阶梯状液气平。请生成诊断分析相关QA、CoT和Preference数据。\n\n"
            "生成要求：请输出结构化中文结果，覆盖 QA、CoT、Preference 三类数据；"
            "问题、答案、推理说明和偏好理由均应忠实于输入文本，不要编造与原文无关的事实。"
        )

        prompt = synth._render_prompt("QA", source)

        self.assertIn("嵌顿性腹股沟疝合并肠梗阻", prompt)
        self.assertIn("建议尽快外科评估", prompt)
        self.assertIn("不要写观察随访", prompt)

    def test_groin_obstruction_qa_accepts_grounded_answer(self):
        source = (
            "49岁男性，解大便后突发右下腹疼痛3小时，右侧腹股沟区可触及4cm包块，"
            "腹部X线见阶梯状液气平。"
        )
        llm = _GroinQALLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("QA", [source])[0]

        self.assertEqual(result["status"], "success")
        self.assertEqual(llm.calls, 1)
        self.assertIn("嵌顿性腹股沟疝", result["data"]["answer"])
        self.assertIn("肠梗阻", result["data"]["answer"])
        self.assertIn("外科评估", result["data"]["answer"])

    def test_generic_qa_prompt_and_limits_stay_compact(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "测试编号：DS-05\n"
            "数据来源风格：中文临床病例公开样式\n\n"
            "患者资料：男，68岁，慢性阻塞性肺疾病10年，近日咳嗽咳痰加重，痰黄，活动后气促明显，体温38.2℃。"
            "请生成疾病判断、处理建议和偏好比较数据。\n\n"
            "生成要求：请输出结构化中文结果，覆盖 QA、CoT、Preference 三类数据。"
        )

        prompt = synth._render_prompt("QA", source)

        self.assertIn("Question should stay close to: \"最可能的处理重点是什么？\"", prompt)
        self.assertIn("Keep answer concise", prompt)
        self.assertLess(len(prompt), 560)
        self.assertEqual(synth.length_limits["QA"]["answer"], 120)

    def test_generic_qa_prompt_prefills_question_and_only_leaves_answer_for_generation(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = "患者男，68岁，慢性阻塞性肺疾病10年，近日咳嗽咳痰加重，痰黄，活动后气促明显。"

        prompt = synth._render_prompt("QA", source)

        self.assertIn('{"question":"最可能的处理重点是什么？","answer":"', prompt)


if __name__ == "__main__":
    unittest.main()
