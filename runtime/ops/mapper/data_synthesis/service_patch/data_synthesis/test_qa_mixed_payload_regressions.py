import unittest

from data_synthesizer import MedicalDataSynthesizer


class QAMixedPayloadRegressionTests(unittest.TestCase):
    def setUp(self):
        self.synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())

    def test_extracts_top_level_qa_string_from_mixed_payload(self):
        source = "8岁儿童反复咳嗽两周，夜间明显，无发热，既往有过敏性鼻炎。"
        raw = (
            '{"测试编号":"DS-07","QA":"儿童反复咳嗽夜间明显，考虑过敏相关咳嗽，建议儿科复诊评估。",'
            '"CoT":"根据症状分析可能与过敏性鼻炎相关。","Preference":"推荐就医。"}<|endoftext|>'
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["question"], "最可能的处理重点是什么？")
        self.assertIn("过敏相关咳嗽", parsed["answer"])

    def test_extracts_nested_qa_object_from_mixed_payload(self):
        source = "女，66岁，膝关节疼痛多年，上下楼明显，X线提示骨关节炎改变。"
        raw = (
            '{"patient":{"gender":"女","age":66},"qa":{"question":"这种疾病会导致哪些症状？",'
            '"answer":"骨关节炎常见膝关节疼痛、活动受限，上下楼时更明显。"},'
            '"cot":{"reasoning":"X线提示骨关节炎改变。"},"Preference":{"chosen":"骨关节炎"}}<|endoftext|>'
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("骨关节炎", parsed["answer"])
        self.assertIn("上下楼", parsed["answer"])

    def test_extracts_question_and_answer_when_payload_contains_extra_keys(self):
        source = "男，72岁，突发言语不清和右侧肢体无力2小时，头颅CT未见出血。"
        raw = (
            '{"question":"是否符合急性缺血性卒中评估条件？",'
            '"answer":"突发言语不清和偏瘫且CT未见出血，应立即启动急性缺血性卒中中心评估并尽快评估溶栓或取栓。",'
            '"QA":"患者符合急性缺血性卒中标准。","CoT":"立即启动卒中中心评估。"}<|endoftext|>'
        )

        extracted = self.synth._extract_qa_candidate_payload(
            {
                "question": "是否符合急性缺血性卒中评估条件？",
                "answer": "突发言语不清和偏瘫且CT未见出血，应立即启动急性缺血性卒中中心评估并尽快评估溶栓或取栓。",
                "QA": "患者符合急性缺血性卒中标准。",
            },
            source,
        )
        self.assertIsNotNone(extracted)
        self.assertTrue(any(term in extracted["answer"] for term in ["卒中中心", "溶栓", "取栓"]))

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("急性缺血性卒中", parsed["answer"])
        self.assertNotIn("CoT", parsed["answer"])

    def test_extracts_lowercase_qa_key_when_only_qa_is_present(self):
        source = "儿童发热38.7℃，精神尚可，家长想知道退热药如何选择以及何时就医。"
        raw = (
            '{"test_id":"DS-28","qa":"精神尚可时可按说明选择对乙酰氨基酚或布洛芬，若持续高热、精神差或呼吸困难应就医。",'
            '"co_t":"需要结合年龄和伴随症状。","Preference":"优先保证安全性。"}<|endoftext|>'
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("对乙酰氨基酚", parsed["answer"])
        self.assertIn("应就医", parsed["answer"])

    def test_extracts_detached_qa_object_when_outer_json_closes_early(self):
        source = "女，66岁，膝关节疼痛多年，上下楼明显，X线提示骨关节炎改变。"
        raw = (
            '{"testid":"DS-19","patient":{"gender":"女","age":66,"diagnosis":"骨关节炎"}}'
            ',"qa":{"question":"这种疾病会导致哪些症状？",'
            '"answer":"骨关节炎会导致膝关节疼痛、肿胀和活动受限，上下楼时往往更明显。"},'
            '"cot":{"reasoning":"X线提示骨关节炎改变。"},"Preference":{"chosen":"骨关节炎"}}<|endoftext|>'
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("骨关节炎", parsed["answer"])
        self.assertIn("上下楼", parsed["answer"])

    def test_acute_stroke_qa_prefers_pathway_grounded_qa_answer(self):
        source = "男，72岁，突发言语不清和右侧肢体无力2小时，高血压病史，头颅CT未见出血。"
        raw = (
            '{"question":"患者为男性，72岁，突发言语不清和右侧肢体无力2小时，高血压病史，头颅CT未见出血。请评估是否符合急性缺血性卒中标准，并按照急性缺血性卒中路径进行处置。",'
            '"answer":"根据您的描述，患者符合急性缺血性卒中的标准。头颅CT未见出血，且患者有高血压病史，这些是急性缺血性卒中的常见特征。",'
            '"QA":"患者符合急性缺血性卒中的标准，头颅CT未见出血，且有高血压病史，这些是急性缺血性卒中的典型表现。因此，应立即启动急性缺血性卒中评估流程，包括对卒中中心的评估、静脉溶栓或机械取栓的可行性评估以及血压和血糖管理。"}<|endoftext|>'
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertTrue(any(term in parsed["answer"] for term in ["卒中中心", "溶栓", "取栓"]))


    def test_accepts_plain_answer_text_for_copd_case(self):
        source = (
            "患者资料：男，68岁，慢性阻塞性肺疾病10年，近日咳嗽咳痰加重，痰黄，"
            "活动后气促明显，体温38.2℃。请生成疾病判断、处理建议和偏好比较数据。"
        )
        raw = (
            "根据您的情况，最可能的处理重点是控制感染，因为痰黄且有发热，这提示可能存在细菌感染。"
            "我们会密切监测您的体温和症状变化，同时可能需要使用抗生素来控制感染。"
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("控制感染", parsed["answer"])

    def test_accepts_plain_answer_text_for_gastric_ulcer_case(self):
        source = (
            "病例摘要：女，45岁，反复上腹痛半年，餐后加重，胃镜提示胃窦溃疡，"
            "幽门螺杆菌阳性。请生成诊疗思路相关的合成数据。"
        )
        raw = "根据您的描述，最可能的处理重点是根除幽门螺杆菌。因为幽门螺杆菌感染是导致胃窦溃疡的主要原因之一。"

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("幽门螺杆菌", parsed["answer"])

    def test_accepts_plain_answer_text_for_uti_case(self):
        source = (
            "病例摘要：女，30岁，尿频尿急尿痛2天，伴下腹不适，无腰痛发热，"
            "尿常规白细胞升高。请生成泌尿感染相关QA、CoT和Preference。"
        )
        raw = "您好，根据您的描述，最可能的处理重点是急性膀胱炎，因为尿频、尿急、尿痛是其典型症状，且尿常规显示白细胞增多。"

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("膀胱炎", parsed["answer"])

    def test_accepts_plain_answer_text_for_allergic_rhinitis_case(self):
        source = (
            "患者咨询：过敏性鼻炎反复发作，打喷嚏流清涕，春秋季明显，"
            "想了解鼻喷激素是否安全。请生成中文医学合成数据。"
        )
        raw = (
            "鼻喷激素是安全有效的，它们通过局部作用于鼻腔，通常不会带来明显全身副作用。"
            "如果症状持续不缓解或出现不适，建议就医评估。"
        )

        parsed = self.synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("鼻喷激素", parsed["answer"])


if __name__ == "__main__":
    unittest.main()
