import json
import unittest

from data_synthesizer import MedicalDataSynthesizer


class MedicationSafetyCleanupTests(unittest.TestCase):
    def test_softened_medication_advice_does_not_keep_modal_prefix(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者咨询文本：我今年 56 岁，已有多年高血压病史，平时服用氨氯地平控制血压。"
            "最近一周出现轻度踝部水肿，血压大多在 145/92 mmHg 左右。"
            "请问这种情况是否需要调整用药？日常应该如何监测血压和生活方式管理？"
        )
        raw = json.dumps(
            {
                "question": source,
                "answer": "如果确诊为高血压，医生可能会调整用药方案。请不要自行调整药物。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        answer = parsed["answer"]
        self.assertIn("应由医生评估是否调整用药方案", answer)
        self.assertNotIn("医生可能会应由医生评估", answer)
        self.assertNotIn("方案方案", answer)
        self.assertIn("不要自行调整药物", answer)

    def test_softened_medication_advice_does_not_duplicate_whether_phrase(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，高血压多年，服用氨氯地平控制血压。"
            "最近一周出现轻度踝部水肿，血压145/92mmHg左右，询问是否需要调整用药。"
        )
        raw = json.dumps(
            {
                "question": source,
                "answer": (
                    "这种情况需要结合其他因素来判断是否需要调整用药。"
                    "具体是否需要调整用药，还要看血压记录和水肿变化。"
                ),
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        answer = parsed["answer"]
        self.assertNotIn("是否应由医生评估是否调整用药方案", answer)
        self.assertNotIn("判断是否应由医生评估", answer)
        self.assertIn("由医生评估", answer)

    def test_softened_medication_advice_removes_broken_connector_and_deduplicates(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        text = (
            "轻度踝部水肿可能与高血压有关，但需要结合其他因素来应由医生评估是否调整用药方案。"
            "血压在145/92mmHg左右，具体应由医生评估是否调整用药方案，还需要考虑水肿变化。"
            "请不要自行调整药物。"
        )

        cleaned = synth._clean_medical_answer_text(text)

        self.assertNotIn("来应由医生评估", cleaned)
        self.assertEqual(cleaned.count("医生评估是否调整用药方案"), 1)
        self.assertIn("需要结合其他因素，由医生评估是否调整用药方案", cleaned)
        self.assertIn("不要自行调整药物", cleaned)

    def test_softened_medication_advice_deduplicates_equivalent_safe_phrases(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        text = (
            "需要结合其他因素，由医生评估是否调整用药方案。"
            "具体应由医生评估是否调整用药方案，还需要考虑肾功能。"
        )

        cleaned = synth._clean_medical_answer_text(text)

        self.assertEqual(cleaned.count("医生评估是否调整用药方案"), 1)
        self.assertIn("由医生进一步评估", cleaned)

    def test_cot_medication_advice_removes_possible_safe_phrase_prefix(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "rationale": (
                    "1. 患者有高血压病史。"
                    "2. 服用氨氯地平后出现踝部水肿。"
                    "3. 血压145/92mmHg仍高于目标范围。"
                    "4. 水肿可能与药物不良反应有关。"
                    "5. 这种情况可能应由医生评估是否调整用药方案。"
                    "6. 需记录血压和水肿变化后复诊。"
                ),
                "final_answer": "轻度踝部水肿可能提示应由医生评估是否调整用药方案，并定期监测血压。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNotNone(parsed)
        combined = parsed["rationale"] + parsed["final_answer"]
        self.assertNotIn("可能应由医生评估是否调整用药方案", combined)
        self.assertNotIn("可能提示应由医生评估是否调整用药方案", combined)
        self.assertIn("应由医生评估是否调整用药方案", combined)

    def test_hypertension_edema_preference_removes_hard_emergency_threshold(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "chosen": (
                    "建议监测血压和水肿变化，保持低盐饮食。"
                    "如果水肿持续或加重，或者血压超过180/110mmHg，应由医生评估是否调整用药方案。"
                ),
                "rejected": "可以自行加大降压药剂量，先不用复诊。",
                "preference_reason": "chosen强调监测和医生评估，rejected存在自行调整药物的安全风险。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("Preference", raw, source)

        self.assertIsNotNone(parsed)
        chosen = parsed["chosen"]
        self.assertNotIn("180/110mmHg", chosen)
        self.assertIn("血压持续高于目标范围", chosen)
        self.assertIn("应由医生评估是否调整用药方案", chosen)

    def test_hypertension_edema_output_stays_grounded_without_specific_complication_path(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者咨询文本：我今年 56 岁，已有多年高血压病史，平时服用氨氯地平控制血压。"
            "最近一周出现轻度踝部水肿，血压大多在 145/92 mmHg 左右。"
            "请问这种情况是否需要调整用药？日常应该如何监测血压和生活方式管理？"
        )
        raw = json.dumps(
            {
                "question": source,
                "answer": (
                    "具体由医生进一步评估，还需要考虑其他因素，比如是否有蛋白尿、肾功能不全等。"
                    "如果确诊为心脏问题，可能需要使用ACEI或ARB类药物。"
                ),
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("QA", raw, source)

        self.assertIsNotNone(parsed)
        answer = parsed["answer"]
        for bad in ["蛋白尿", "肾功能不全", "心脏问题", "ACEI", "ARB"]:
            self.assertNotIn(bad, answer)
        self.assertIn("血压记录", answer)
        self.assertIn("水肿变化", answer)

    def test_hypertension_edema_cot_removes_overexpanded_heart_kidney_route(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "rationale": (
                    "1. 患者有高血压病史。"
                    "2. 服用氨氯地平后出现踝部水肿。"
                    "3. 血压145/92mmHg仍高于目标范围。"
                    "4. 建议进行心脏功能和肾功能的评估。"
                    "5. 如果确诊为心脏问题，可能需要使用ACEI或ARB类药物。"
                    "6. 踝部水肿可能提示其他问题，如心脏或肾脏问题，需要进一步检查。"
                    "7. 同时记录血压和水肿变化，并观察是否有呼吸困难、水肿加重等。"
                ),
                "final_answer": "建议您建议结合血压记录和水肿变化复诊评估。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNotNone(parsed)
        combined = parsed["rationale"] + parsed["final_answer"]
        for bad in ["心脏功能", "心脏问题", "肾功能", "肾脏问题", "ACEI", "ARB", "呼吸困难"]:
            self.assertNotIn(bad, combined)
        self.assertNotIn("建议您建议", combined)
        self.assertNotIn("建议您尽快就医，建议", combined)
        self.assertNotRegex(combined, r"\d+\.\s*\d+\.")
        for step in ["1.", "2.", "3.", "4.", "5."]:
            self.assertIn(step, parsed["rationale"])
        self.assertIn("血压记录", combined)
        self.assertIn("水肿变化", combined)

    def test_hypertension_edema_cleanup_removes_broken_residual_fragments(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "rationale": (
                    "1. 轻度踝部水肿可能与高血压有关。"
                    "2. 如果症状持续或加重，应及时就医，排除其他潜在疾病，如或。"
                    "3. 建议记录血压变化。"
                ),
                "final_answer": "轻度踝部水肿应由医生评估是否调整用药方案。建议记录血压和水肿变化，并由医生评估是否调整用药方案。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNotNone(parsed)
        combined = parsed["rationale"] + parsed["final_answer"]
        self.assertNotIn("如或", combined)
        self.assertLessEqual(combined.count("医生评估是否调整用药方案"), 1)

    def test_hypertension_edema_preference_reason_removes_broken_other_fragment(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "chosen": "建议记录血压和水肿变化，由医生评估是否调整用药方案。",
                "rejected": "只建议继续观察或自行调整用药，未结合血压记录和水肿变化；请不要自行调整药物。",
                "preference_reason": "chosen更贴近本病例；rejected更侧重于排除其他，可能对患者造成不必要的健康风险。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("Preference", raw, source)

        self.assertIsNotNone(parsed)
        self.assertNotIn("排除其他，", parsed["preference_reason"])
        self.assertIn("泛化风险提示", parsed["preference_reason"])

    def test_hypertension_edema_cot_removes_platform_residual_kidney_route(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "rationale": (
                    "1. 根据您的描述，轻度踝部水肿可能与高血压有关，但需要进一步评估。"
                    "2. 氨氯地平是常用的降压药，但需注意其副作用，如踝部水肿、心悸等。"
                    "如果这些症状出现，可能提示药物对某些患者不适用，或者存在其他并发症。"
                    "3. 肾功能检查对于评估药物代谢很重要，因为氨氯地平主要通过肾脏排泄。"
                    "如果肾功能受损，药物可能蓄积，增加副作用风险。"
                    "4. 建议定期监测血压，记录每日血压变化。"
                    "5. 如果症状持续或加重，应及时就医，排除其他潜在疾病，如或肾脏疾病。"
                ),
                "final_answer": "建议您进行肾功能检查，并定期监测血压。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNotNone(parsed)
        combined = parsed["rationale"] + parsed["final_answer"]
        for bad in ["肾功能", "肾脏", "心悸", "并发症", "药物蓄积"]:
            self.assertNotIn(bad, combined)
        self.assertIn("血压记录", combined)
        self.assertIn("水肿变化", combined)

    def test_hypertension_edema_preference_rejected_uses_same_case_low_quality_not_hallucinated_diseases(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=object())
        source = (
            "患者56岁，有多年高血压病史，服用氨氯地平控制血压，"
            "最近一周出现轻度踝部水肿，血压多为145/92mmHg左右。"
        )
        raw = json.dumps(
            {
                "question": "患者踝部水肿和血压偏高时是否需要调整用药？",
                "chosen": (
                    "建议记录家庭血压和水肿变化，如果水肿持续或血压持续高于目标范围，"
                    "应由医生评估是否调整用药方案。"
                ),
                "rejected": (
                    "对于老年高血压患者，尤其是有慢性疾病如糖尿病、肾病等的患者，"
                    "轻度踝部水肿可能提示潜在的并发症，如心衰、肾病或下肢静脉血栓。"
                    "因此，建议您进行详细检查，包括、肾脏功能等，以排除这些可能性。"
                    "同时，应由医生评估是否调整用药方案，比如换用其他降压药或增加剂量。"
                    "请不要自行调整药物，以免造成不必要的健康风险。"
                ),
                "preference_reason": "chosen更贴近本病例，rejected扩展了过多原文没有给出的并发症。",
            },
            ensure_ascii=False,
        )

        parsed = synth._try_parse_and_validate("Preference", raw, source)

        self.assertIsNotNone(parsed)
        rejected = parsed["rejected"]
        for bad in ["糖尿病", "肾病", "心衰", "血栓", "肾脏功能", "换用其他降压药", "增加剂量"]:
            self.assertNotIn(bad, rejected)
        self.assertIn("不要自行调整药物", rejected)


if __name__ == "__main__":
    unittest.main()
