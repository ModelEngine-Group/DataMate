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
            if "preference_reason" in prompt:
                payload = {
                    "question": f"偏好问题{i}",
                    "chosen": "高质量回答：给出循证建议并提醒就医。",
                    "rejected": "低质量回答：建议忽略症状。",
                    "preference_reason": "chosen 更准确、安全、完整。",
                }
            elif "final_answer" in prompt:
                payload = {
                    "question": f"CoT问题{i}",
                    "rationale": "1. 提取症状。2. 分析病史。3. 核对检查。4. 判断风险。5. 明确诊断方向。6. 给出处置建议。",
                    "final_answer": "建议先检查再对症治疗。",
                }
            else:
                payload = {
                    "question": f"QA问题{i}",
                    "answer": "这是一个完整且相关的回答。",
                }
            results.append(_FakeResult(json.dumps(payload, ensure_ascii=False)))
        return results


class NativeTemplateSynthesizer(MedicalDataSynthesizer):
    def _load_native_chat_template(self, model_path=None):
        return (
            "{%- for message in messages %}"
            "{{- '<|im_start|>' + message.role + '\n' + message.content + '<|im_end|>\n' }}"
            "{%- endfor %}"
            "{%- if add_generation_prompt %}"
            "{{- '<|im_start|>assistant\n' }}"
            "{%- if enable_thinking is defined and enable_thinking is false %}"
            "{{- '<think>\n\n</think>\n\n' }}"
            "{%- endif %}"
            "{%- endif %}"
        )


class CountingInvalidQaLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        return [_FakeResult("not a json answer") for _ in prompts]


class InvalidThenGoodQaLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        if self.calls == 1:
            return [_FakeResult('{"question": "患者最可能的诊断是什么？", "answer": "患者可能为糖尿病酮症酸中毒，应补液、胰岛素治疗并监测')]
        return [
            _FakeResult(json.dumps({
                "question": "患者最可能的诊断和处理原则是什么？",
                "answer": "考虑糖尿病酮症酸中毒，应立即补液、静脉胰岛素、监测并纠正钾等电解质，寻找诱因。",
            }, ensure_ascii=False))
            for _ in prompts
        ]


class AlwaysInvalidLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        return [_FakeResult("not a json answer") for _ in prompts]


class InvalidThenPlainCotLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        if self.calls == 1:
            return [_FakeResult("not a json answer") for _ in prompts]
        return [
            _FakeResult(
                "1. 患者出现胸痛，需要关注急性心血管事件。"
                "2. 心电图ST段抬高提示心肌缺血损伤。"
                "3. 需要结合心肌标志物判断心肌损伤程度。"
                "4. 应尽快进行心内科急诊评估。"
                "5. 这是一段自然语言，不是受 JSON schema 约束生成的结构化结果。"
            )
            for _ in prompts
        ]


class InvalidThenBadThenGoodCotLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, prompts, sampling_params):
        self.calls += 1
        if self.calls == 1:
            return [
                _FakeResult(json.dumps({
                    "question": "患者应诊断为哪种情况？",
                    "rationale": [
                        "患者为49岁男性，右下腹痛并有腹股沟包块。",
                        "腹部X线片显示阶梯状液气平，提示肠梗阻。",
                        "超声提示腹股沟区混合回声区。",
                        "综合考虑嵌顿性腹股沟疝合并肠梗阻。",
                        "需要外科评估。",
                        "避免延误导致穿孔。",
                    ],
                    "final_answer": "嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估，避免穿孔。",
                }, ensure_ascii=False))
                for _ in prompts
            ]
        if self.calls == 2:
            return [
                _FakeResult(json.dumps({
                    "question": "患者应诊断为哪种情况？",
                    "rationale": [
                        "患者为49岁男性，右下腹痛并有腹股沟包块。",
                        "腹部X线片显示阶梯状液气平，提示肠梗阻。",
                        "超声提示腹股沟区混合回声区。",
                        "综合考虑嵌顿性腹股沟疝合并肠梗阻。",
                        "需要外科评估。",
                        "仍需避免延误导致穿孔。",
                    ],
                    "final_answer": "嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估，避免穿孔。",
                }, ensure_ascii=False))
                for _ in prompts
            ]
        return [
            _FakeResult(json.dumps({
                "question": "患者最可能的诊断是什么？",
                "rationale": [
                    "患者为49岁男性，出现右下腹痛并可触及右侧腹股沟区包块。",
                    "包块位于腹股沟韧带上内方，支持腹股沟疝相关病变。",
                    "腹部X线片显示阶梯状液气平，提示肠梗阻。",
                    "超声提示腹股沟区混合回声区，支持局部嵌顿可能。",
                    "综合腹股沟包块和肠梗阻影像，考虑嵌顿性腹股沟疝合并肠梗阻。",
                    "应尽快进行外科评估，避免延误处理嵌顿和肠梗阻。",
                ],
                "final_answer": "考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。",
            }, ensure_ascii=False))
            for _ in prompts
        ]


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

    def test_native_chat_template_renders_qa_prompt(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_qa_fast_prompt("Case: chest pain.")

        self.assertIn("<|im_start|>system\n", prompt)
        self.assertIn("<|im_start|>user\n", prompt)
        self.assertIn("<|im_start|>assistant\n<think>\n\n</think>\n\n", prompt)
        self.assertNotIn("Source text:", prompt)

    def test_native_template_flag_is_enabled(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        self.assertTrue(synth._qa_uses_native_template)

    def test_native_chat_template_renders_cot_and_preference_prompts(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        cot_prompt = synth._render_prompt("CoT", "病例A")
        pref_prompt = synth._render_prompt("Preference", "病例B")

        for prompt in [cot_prompt, pref_prompt]:
            self.assertIn("<|im_start|>system\n", prompt)
            self.assertIn("<|im_start|>user\n", prompt)
            self.assertIn("<|im_start|>assistant\n<think>\n\n</think>\n\n", prompt)
            self.assertNotIn("{{", prompt)

    def test_repair_prompt_uses_native_template_with_thinking_disabled(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_repair_prompt("Preference", "病例A", "not json")

        self.assertIn("<|im_start|>system\n", prompt)
        self.assertIn("<|im_start|>assistant\n<think>\n\n</think>\n\n", prompt)
        self.assertIn("只输出一个合法 JSON 对象", prompt)

    def test_cot_and_preference_sampling_use_json_schema_constraints(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())

        cot_params = synth._build_sampling_params("CoT")
        pref_params = synth._build_sampling_params("Preference")

        for params, field in [(cot_params, "final_answer"), (pref_params, "preference_reason")]:
            structured = getattr(params, "structured_outputs", None)
            self.assertIsNotNone(structured)
            schema = structured.get("json") if isinstance(structured, dict) else getattr(structured, "json", None)
            self.assertIsInstance(schema, dict)
            self.assertIn(field, schema["properties"])
            self.assertFalse(schema.get("additionalProperties", True))
            no_whitespace = structured.get("disable_any_whitespace") if isinstance(structured, dict) else getattr(structured, "disable_any_whitespace", False)
            self.assertTrue(no_whitespace)
        cot_schema = getattr(cot_params.structured_outputs, "json", cot_params.structured_outputs["json"])
        self.assertEqual(cot_schema["properties"]["rationale"]["type"], "string")
        self.assertGreaterEqual(cot_schema["properties"]["rationale"]["minLength"], 40)

    def test_cot_and_preference_do_not_use_deterministic_success_fallback(self):
        for task_type in ["CoT", "Preference"]:
            llm = AlwaysInvalidLLM()
            synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

            result = synth.generate_data_batch(task_type, ["病例A"])[0]

            self.assertGreaterEqual(llm.calls, 2)
            self.assertEqual(result["status"], "failed")
            self.assertNotIn("deterministic", result)

    def test_cot_repair_plain_text_is_not_promoted_to_fallback_success(self):
        llm = InvalidThenPlainCotLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch("CoT", ["患者男，58岁，胸痛伴ST段抬高。"])[0]

        self.assertGreaterEqual(llm.calls, 2)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "repair_failed")
        self.assertNotIn("fallback", result)
        self.assertNotIn("deterministic", result)

    def test_second_llm_repair_can_fix_quality_gate_failure_without_fallback(self):
        llm = InvalidThenBadThenGoodCotLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch(
            "CoT",
            ["患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"],
        )[0]

        self.assertEqual(llm.calls, 3)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["repaired"])
        self.assertNotIn("fallback", result)
        self.assertNotIn("deterministic", result)
        self.assertNotIn("穿孔", json.dumps(result["data"], ensure_ascii=False))

    def test_preference_json_with_trailing_comma_is_accepted(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = '''{
  "question": "患者是否需要心血管急诊评估？",
  "chosen": "胸痛伴ST段抬高和肌钙蛋白升高，应立即按急性心肌梗死流程评估。",
  "rejected": "胸痛可以先在家休息观察，暂时不需要检查。",
  "preference_reason": "chosen 结合胸痛、ST段抬高和肌钙蛋白升高，能避免延误再灌注治疗；rejected 忽略高危证据。",
}'''

        parsed = synth._try_parse_and_validate("Preference", raw, "患者男，58岁。心电图提示ST段抬高，肌钙蛋白升高。")

        self.assertIsNotNone(parsed)
        self.assertEqual(set(parsed.keys()), {"question", "chosen", "rejected", "preference_reason"})

    def test_cot_rejects_obvious_gender_and_case_contradictions(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块。腹部X线可见阶梯状液气平。"
        raw = json.dumps({
            "question": "患者的诊断依据是什么？",
            "rationale": "1. 患者为49岁男性。2. 有右下腹痛。3. 有腹股沟包块。4. 有压痛。5. X线有液气平。6. 需要进一步检查。",
            "final_answer": "考虑卵巢囊肿或黄体破裂，需要妇科检查。",
        }, ensure_ascii=False)

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNone(parsed)

    def test_cot_rationale_array_is_normalized_to_steps(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = json.dumps({
            "question": "患者胸痛应如何分析？",
            "rationale": [
                "主诉反复胸闷、胸痛3天，加重6小时。",
                "胸骨后压榨样疼痛，活动后加重并伴大汗、恶心。",
                "既往高血压10年，是心血管事件危险因素。",
                "心电图II、III、aVF导联ST段抬高提示下壁心肌缺血损伤。",
                "肌钙蛋白升高支持心肌损伤。",
                "需尽快启动急性心肌梗死再灌注评估。",
            ],
            "final_answer": "考虑急性下壁心肌梗死，建议立即心内科急诊处理。",
        }, ensure_ascii=False)

        parsed = synth._try_parse_and_validate("CoT", raw, "患者男，58岁。心电图提示II、III、aVF导联ST段抬高，肌钙蛋白升高。")

        self.assertIsNotNone(parsed)
        self.assertIn("1. 主诉", parsed["rationale"])
        self.assertIn("6. 需尽快", parsed["rationale"])

    def test_source_specific_medical_contradictions_are_rejected(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        st_source = "患者男，58岁。心电图提示II、III、aVF导联ST段抬高，肌钙蛋白升高。"
        st_raw = json.dumps({
            "question": "患者最可能是什么问题？",
            "chosen": "左心上室的心肌梗死。",
            "rejected": "普通疲劳。",
            "preference_reason": "ST段抬高和肌钙蛋白升高支持左心上室心肌梗死。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("Preference", st_raw, st_source))

        embolism_raw = json.dumps({
            "question": "患者胸痛应如何处理？",
            "chosen": "患者胸痛可能是冠状动脉栓塞导致，应立即抗凝治疗。",
            "rejected": "无需急诊评估。",
            "preference_reason": "ST段抬高支持冠状动脉栓塞，因此抗凝优先。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("Preference", embolism_raw, st_source))

        st_cot_raw = json.dumps({
            "question": "患者最可能是什么问题？",
            "rationale": [
                "胸痛伴大汗和恶心提示急性心血管事件。",
                "肌钙蛋白升高提示心肌损伤。",
                "心电图II、III、aVF导联ST段抬高提示STEMI。",
                "该表现支持左心室前壁心肌梗死。",
                "需要心血管急诊评估。",
                "应尽快处理。",
            ],
            "final_answer": "考虑左心室前壁心肌梗死。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("CoT", st_cot_raw, st_source))

        st_bad_repair_raw = json.dumps({
            "question": "患者最可能是什么问题？",
            "rationale": [
                "胸痛伴大汗和恶心提示急性心血管事件。",
                "肌钙蛋白升高提示心肌损伤。",
                "心电图II、III、aVF导联ST段抬高提示STEMI。",
                "该表现通常提示左心室前壁的心脏梗死。",
                "结合导联方向，应考虑左心下室或者左心室前壁心梗。",
                "需要心血管急诊处理。",
            ],
            "final_answer": "患者高度提示左心下室或左心室前壁心肌梗死。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("CoT", st_bad_repair_raw, st_source))

        st_bad_management_raw = json.dumps({
            "question": "患者胸痛应如何处理？",
            "rationale": [
                "胸痛伴大汗和恶心提示急性心血管事件。",
                "心电图II、III、aVF导联ST段抬高提示下壁STEMI。",
                "肌钙蛋白升高支持心肌损伤。",
                "需要尽快进行心电图复查。",
                "需要评估再灌注治疗窗口。",
                "不应把下壁STEMI写成心包反射问题。",
            ],
            "final_answer": "考虑下壁心肌梗死，建议立即进行心脏起搏器检查，同时处理心包反射。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("CoT", st_bad_management_raw, st_source))

        st_bad_inferior_raw = json.dumps({
            "question": "患者胸痛应如何处理？",
            "rationale": [
                "患者为男性且有高血压病史。",
                "心电图II、III、aVF导联ST段抬高伴肌钙蛋白升高。",
                "这些特征提示心尖端心肌梗死。",
                "也可能排除了心肌梗死。",
                "需要进一步确认心包以外的疾病。",
                "建议冠状动脉造影和再灌注。"
            ],
            "final_answer": "优先考虑心尖端心肌梗死或非心尖端心肌梗死。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("CoT", st_bad_inferior_raw, st_source))

        st_direct_denial_raw = json.dumps({
            "question": "患者胸痛应如何处理？",
            "rationale": [
                "患者有胸痛和大汗。",
                "心电图II、III、aVF导联ST段抬高。",
                "肌钙蛋白升高提示心肌损伤。",
                "上述证据却排除心肌梗死。",
                "需要进一步观察。",
                "暂不急诊处理。"
            ],
            "final_answer": "排除心肌梗死，建议先观察。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("CoT", st_direct_denial_raw, st_source))

        st_acceptable_ruleout_raw = json.dumps({
            "question": "该患者的症状和心电图特征提示什么？",
            "rationale": [
                "患者为58岁男性，有反复胸闷胸痛并伴大汗恶心。",
                "心电图II、III、aVF导联ST段抬高。",
                "肌钙蛋白升高提示心肌损伤。",
                "这些证据支持急性下壁STEMI或下壁心肌梗死。",
                "应急诊心内科评估并进行冠脉造影以排除其他冠脉相关原因。",
                "治疗聚焦抗栓和再灌注策略。"
            ],
            "final_answer": "考虑急性下壁心肌梗死，建议急诊心内科评估、抗栓治疗并尽快评估再灌注策略。",
        }, ensure_ascii=False)
        self.assertIsNotNone(synth._try_parse_and_validate("CoT", st_acceptable_ruleout_raw, st_source))

        groin_source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平。"
        groin_raw = json.dumps({
            "question": "患者最可能是什么问题？",
            "chosen": "阑尾炎或精索静脉曲张。",
            "rejected": "盆腔炎或卵巢囊肿。",
            "preference_reason": "这些诊断可以解释右下腹痛。",
        }, ensure_ascii=False)
        self.assertIsNone(synth._try_parse_and_validate("Preference", groin_raw, groin_source))

    def test_negated_or_rejected_wrong_diagnoses_do_not_cause_false_kill(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        groin_source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平。"
        cot_raw = json.dumps({
            "question": "患者诊断依据是什么？",
            "rationale": [
                "右侧腹股沟区可触及肿块，首先考虑腹股沟疝。",
                "肿块位于腹股沟韧带上内方，支持腹股沟疝。",
                "腹部X线阶梯状液气平提示肠梗阻。",
                "超声混合回声区提示局部包块或嵌顿改变。",
                "患者为男性，应排除卵巢囊肿或妇科疾病。",
                "综合考虑嵌顿性腹股沟疝合并肠梗阻。",
            ],
            "final_answer": "考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。",
        }, ensure_ascii=False)
        self.assertIsNotNone(synth._try_parse_and_validate("CoT", cot_raw, groin_source))

        pref_raw = json.dumps({
            "question": "患者的诊断依据是什么？",
            "chosen": "右侧腹股沟包块伴阶梯状液气平，优先考虑嵌顿性腹股沟疝合并肠梗阻。",
            "rejected": "仅建议观察，忽视阶梯状液气平提示的肠梗阻风险和外科评估。",
            "preference_reason": "chosen 结合了腹股沟包块位置和肠梗阻影像；rejected 会延误外科评估。",
        }, ensure_ascii=False)
        self.assertIsNotNone(synth._try_parse_and_validate("Preference", pref_raw, groin_source))

    def test_groin_preference_rejects_off_case_diagnoses_even_when_reason_says_unrelated(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平。"
        raw = json.dumps({
            "question": "诊断依据是什么？",
            "chosen": "嵌顿性腹股沟疝合并肠梗阻",
            "rejected": "卵巢囊肿或睾丸扭转",
            "preference_reason": "与病例实际情况无关的诊断，忽视肠梗阻的评估和处置",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_repair_prompt_includes_source_specific_guardrails(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_repair_prompt(
            "CoT",
            "患者男，58岁。心电图提示II、III、aVF导联ST段抬高，肌钙蛋白升高。",
            "左心室前壁心肌梗死",
        )

        self.assertIn("急性下壁STEMI", prompt)
        self.assertIn("急诊心内科评估", prompt)
        self.assertIn("再灌注", prompt)
        self.assertNotIn("心尖端", prompt)
        self.assertNotIn("非心尖", prompt)
        self.assertNotIn("心包", prompt)
        self.assertNotIn("起搏器", prompt)
        self.assertNotIn("妇科", prompt)

    def test_preference_prompt_for_groin_case_forbids_off_case_rejected_diagnoses(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_prompt(
            "Preference",
            "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平。",
        )

        self.assertIn("rejected 不得是疾病名", prompt)
        self.assertIn("严禁输出卵巢囊肿", prompt)
        self.assertIn("必须用同一病例的低质量处理建议作为 rejected", prompt)
        self.assertIn("每个字段保持简短", prompt)

    def test_repair_prompt_for_groin_preference_requires_exact_diagnosis_and_forbids_unsupported_terms(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_repair_prompt(
            "Preference",
            "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。",
            "chosen 写成卵巢囊肿，preference_reason 写了防止穿孔。",
        )

        self.assertIn("chosen 必须字面包含：嵌顿性腹股沟疝合并肠梗阻", prompt)
        self.assertIn("所有字段禁止出现", prompt)
        self.assertIn("穿孔", prompt)
        self.assertIn("减压", prompt)
        self.assertIn("rejected 不得是疾病名", prompt)

    def test_second_repair_prompt_for_groin_case_uses_sanitized_candidate(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"
        failed_output = "建议尽快外科评估，避免延误导致肠穿孔或其他严重并发症。"

        prompt = synth._render_second_repair_prompt("CoT", source, failed_output)

        self.assertIn("请完全重写", prompt)
        self.assertIn("不要沿用上一轮原句", prompt)
        self.assertIn("诊断和处置只写", prompt)
        self.assertIn("嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估", prompt)
        self.assertNotIn("肠穿孔或其他严重并发症", prompt)

    def test_medical_answer_starting_with_according_to_provided_info_is_allowed(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者女，65岁。反酸、烧心30年，胃镜提示反流性食管炎LA-C和混合型食管裂孔疝。"
        raw = json.dumps({
            "question": "患者病情如何分析？",
            "rationale": [
                "长期反酸和烧心提示胃食管反流病。",
                "胃镜显示反流性食管炎LA-C。",
                "胃镜提示混合型食管裂孔疝。",
                "上消化道造影支持巨大食管裂孔疝。",
                "咳嗽和喘息与反流相关。",
                "综合考虑反流性食管炎和食管裂孔疝。",
            ],
            "final_answer": "根据提供的信息，患者的病情主要由胃食管反流引发的反流性食管炎所致。",
        }, ensure_ascii=False)

        self.assertIsNotNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_cot_rejects_model_monologue_question(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者女，65岁。反酸、烧心30年，胃镜提示反流性食管炎LA-C和混合型食管裂孔疝。"
        raw = json.dumps({
            "question": "这位65岁的女性患者有长期反酸和烧心症状，这让我首先联想到慢性胃病。我需要综合这些信息来理解她的病情。",
            "rationale": [
                "长期反酸和烧心提示胃食管反流病。",
                "胃镜显示反流性食管炎LA-C。",
                "胃镜提示混合型食管裂孔疝。",
                "上消化道造影支持巨大食管裂孔疝。",
                "咳嗽和喘息与反流相关。",
                "综合考虑反流性食管炎和食管裂孔疝。",
            ],
            "final_answer": "考虑胃食管反流病合并混合型食管裂孔疝，需要控制反流并评估疝相关治疗。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_groin_cot_rejects_invented_perforation_drainage_or_reduction(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"
        raw = json.dumps({
            "question": "患者出现什么症状和体征？",
            "rationale": [
                "患者为49岁男性，右下腹痛并可触及腹股沟包块。",
                "包块位于腹股沟韧带上内方且有压痛。",
                "腹部X线阶梯状液气平提示肠梗阻。",
                "超声混合回声区提示有穿孔和引流所致的气液平面。",
                "结合腹股沟包块，高度怀疑嵌顿性腹股沟疝。",
                "应进行外科评估。",
            ],
            "final_answer": "考虑嵌顿性腹股沟疝合并肠梗阻，应避免延迟外科评估和疝推挤治疗。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_groin_cot_rejects_observation_or_delayed_surgical_evaluation(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"
        raw = json.dumps({
            "question": "患者最可能的诊断是什么？",
            "rationale": [
                "患者右侧腹股沟区可触及包块且有压痛，提示腹股沟疝相关问题。",
                "腹部X线可见阶梯状液气平，这是肠梗阻的典型表现之一。",
                "超声提示腹股沟区混合回声区，支持局部包块或嵌顿改变。",
                "结合腹股沟包块和肠梗阻表现，应考虑嵌顿性腹股沟疝合并肠梗阻。",
                "目前不应忽视肠梗阻和嵌顿风险。",
                "病例中没有迹象表明患者已延误外科评估，因此建议观察并延迟手术。",
            ],
            "final_answer": "嵌顿性腹股沟疝合并肠梗阻。建议观察并延迟外科评估以防止并发症。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_groin_cot_allows_warning_to_avoid_delayed_treatment(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"
        raw = json.dumps({
            "question": "患者最可能的诊断是什么？",
            "rationale": [
                "患者为49岁男性，右下腹痛并有腹股沟区包块。",
                "包块位于腹股沟韧带上内方，支持腹股沟疝相关病变。",
                "腹部X线片显示阶梯状液气平，提示肠梗阻。",
                "超声提示腹股沟区混合回声区，支持局部嵌顿可能。",
                "综合腹股沟包块和肠梗阻影像，考虑嵌顿性腹股沟疝合并肠梗阻。",
                "需要尽快外科评估，避免延误处理。",
            ],
            "final_answer": "考虑嵌顿性腹股沟疝合并肠梗阻，建议立即进行外科评估，以避免延误处理。",
        }, ensure_ascii=False)

        self.assertIsNotNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_groin_preference_rejects_off_case_chosen_even_if_rejected_is_same_case(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平，超声提示腹股沟区混合回声区。"
        raw = json.dumps({
            "question": "病例中的诊断是什么？",
            "chosen": "卵巢囊肿、盆腔炎等妇科疾病",
            "rejected": "仅建议观察，延误外科评估，忽视肠梗阻证据。",
            "preference_reason": "腹股沟区包块和阶梯状液气平提示肠梗阻风险，不能把妇科疾病作为正确诊断。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_preference_rejects_reversed_hiatal_hernia_preference(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者女，65岁。反酸、烧心30年，胃镜提示反流性食管炎LA-C和混合型食管裂孔疝，上消化道造影提示巨大食管裂孔疝。"
        raw = json.dumps({
            "question": "治疗方案",
            "chosen": "质子泵抑制剂治疗能够控制反流性食管炎引起的症状。",
            "rejected": "仅使用质子泵抑制剂治疗可能无法充分缓解患者的症状，需要考虑增加手术治疗的可能性。",
            "preference_reason": "胃镜和检查结果表明患者有反流性食管炎和混合型食管裂孔疝，质子泵抑制剂能够控制症状，但手术评估也有助于解决食管裂孔疝。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_source_guardrails_are_included_in_generation_prompt(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())

        prompt = synth._render_prompt(
            "Preference",
            "患者，男，49岁。右侧腹股沟区可扪及包块，腹部X线可见阶梯状液气平。",
        )

        self.assertIn("禁止输出妇科疾病", prompt)
        self.assertIn("腹股沟疝", prompt)
        self.assertIn("嵌顿性腹股沟疝合并肠梗阻", prompt)

    def test_qa_invalid_first_pass_triggers_llm_repair(self):
        llm = InvalidThenGoodQaLLM()
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=llm)

        result = synth.generate_data_batch(
            "QA",
            ["患者，女，52岁。主诉：多饮、多尿1个月，加重伴恶心呕吐1天。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"],
        )[0]

        self.assertGreaterEqual(llm.calls, 2)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["repaired"])
        self.assertIn("糖尿病酮症酸中毒", result["data"]["answer"])

    def test_qa_sampling_budget_allows_complete_chinese_json(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())

        params = synth._build_sampling_params("QA")

        self.assertGreaterEqual(params.max_tokens, 180)

    def test_dka_cot_and_preference_reject_unsafe_medical_direction(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。主诉：多饮、多尿1个月，加重伴恶心呕吐1天。查体：口唇干燥，呼吸深快，心率112次/分，血压96/60mmHg。辅助检查：随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        bad_cot = json.dumps({
            "question": "患者可能的诊断和处理原则是什么？",
            "rationale": [
                "多饮、多尿提示糖代谢异常。",
                "随机血糖28.6mmol/L明显升高。",
                "尿酮体+++提示酮体增多。",
                "血气pH 7.21和HCO3- 12mmol/L提示酸中毒。",
                "应给予抗激素治疗并排查神经系统受损原因。",
                "需要进一步处理。"
            ],
            "final_answer": "考虑糖尿病酮症酸中毒，但应优先给予抗激素治疗并排查神经系统受损原因。"
        }, ensure_ascii=False)
        bad_pref = json.dumps({
            "question": "糖尿病酮症酸中毒应如何处理？",
            "chosen": "快速静脉注射普通碳酸氢钠纠正酸中毒，并使用抗生素治疗尿路感染。",
            "rejected": "静脉胰岛素和补液处理糖尿病酮症酸中毒。",
            "preference_reason": "碳酸氢钠可以快速纠正酸中毒，抗生素可控制感染。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", bad_cot, source))
        self.assertIsNone(synth._try_parse_and_validate("Preference", bad_pref, source))

    def test_dka_cot_allows_negated_bicarbonate_and_antibiotic_mentions(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。主诉：多饮、多尿1个月，加重伴恶心呕吐1天。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "患者可能的诊断和处理原则是什么？",
            "rationale": [
                "多饮、多尿和随机血糖28.6mmol/L提示严重高血糖。",
                "尿酮体+++提示酮体生成增多。",
                "血气pH 7.21和HCO3- 12mmol/L提示代谢性酸中毒。",
                "上述证据支持糖尿病酮症酸中毒。",
                "不得把碳酸氢钠或抗生素作为常规首选治疗。",
                "处理应包括补液、静脉胰岛素和钾等电解质监测纠正。"
            ],
            "final_answer": "考虑糖尿病酮症酸中毒，应补液、静脉胰岛素、监测并纠正钾等电解质，同时寻找诱因。"
        }, ensure_ascii=False)

        self.assertIsNotNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_second_repair_prompt_for_dka_does_not_leak_groin_surgery_instruction(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"

        prompt = synth._render_second_repair_prompt("CoT", source, "not json")

        self.assertIn("糖尿病酮症酸中毒", prompt)
        self.assertNotIn("嵌顿性腹股沟疝", prompt)
        self.assertNotIn("外科评估", prompt)

    def test_dka_repair_prompt_uses_positive_constraints_without_bad_terms(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = "候选输出写了神经系统受损原因、碳酸氢钠、insulin 和依据1。"

        prompt = synth._render_second_repair_prompt("CoT", source, raw)

        self.assertIn("补液", prompt)
        self.assertIn("静脉胰岛素", prompt)
        self.assertIn("电解质", prompt)
        self.assertNotIn("神经系统受损", prompt)
        self.assertNotIn("碳酸氢钠", prompt)
        self.assertIn("不使用英文 insulin", prompt)
        self.assertNotIn("写了、、insulin", prompt.lower())
        self.assertNotIn("依据1", prompt)

    def test_acute_stroke_cot_rejects_unsupported_pathway(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。主诉：突发右侧肢体无力伴言语不清2小时。既往史：高血压20年，房颤3年。查体：右侧肢体肌力3级，NIHSS评分9分。辅助检查：头颅CT未见出血，血压170/95mmHg，血糖7.8mmol/L。"
        bad_cot = json.dumps({
            "question": "患者可能的诊断是什么？",
            "rationale": [
                "突发右侧肢体无力伴言语不清提示急性脑血管事件。",
                "NIHSS评分9分提示存在神经功能缺损。",
                "房颤和高血压是卒中危险因素。",
                "头颅CT未见出血提示缺血性卒中可能。",
                "但应优先考虑脑干梗死和血管痉挛。",
                "需要先行MRI或SPECT评估后再考虑溶栓。"
            ],
            "final_answer": "考虑脑干梗死或血管痉挛，应优先MRI或SPECT评估，溶栓需谨慎延后。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", bad_cot, source))

    def test_acute_stroke_cot_allows_warning_not_to_delay_reperfusion_for_spect(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。主诉：突发右侧肢体无力伴言语不清2小时。头颅CT未见出血，NIHSS评分9分。"
        raw = json.dumps({
            "question": "患者可能的诊断是什么？",
            "rationale": [
                "患者突发右侧肢体无力和言语不清，提示急性脑血管事件。",
                "头颅CT未见出血，支持按急性缺血性卒中路径处理。",
                "NIHSS评分9分提示存在明确神经功能缺损。",
                "发病2小时处于静脉溶栓评估时间窗内。",
                "应评估机械取栓条件并进行血压、血糖管理。",
                "避免先做MRI或SPECT而延误溶栓和再灌注评估。"
            ],
            "final_answer": "考虑急性缺血性卒中，应立即评估静脉溶栓和机械取栓条件，避免先做MRI或SPECT而延误再灌注评估。"
        }, ensure_ascii=False)

        self.assertIsNotNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_bacterial_pneumonia_preference_rejects_antiviral_first(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。主诉：发热、咳嗽3天，气促1天。查体：体温39.0℃，呼吸34次/分，右下肺可闻及湿啰音。辅助检查：白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        bad_pref = json.dumps({
            "question": "细菌感染还是病毒感染导致的肺炎？",
            "chosen": "进行抗病毒治疗，并观察是否需要使用抗生素。",
            "rejected": "立即进行经验性抗生素治疗并密切观察患儿呼吸情况。",
            "preference_reason": "抗病毒治疗可以首先缓解病毒负荷，再根据病情添加抗生素。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", bad_pref, source))

    def test_acute_stroke_qa_rejects_obvious_typo_in_core_diagnosis(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。突发右侧肢体无力伴言语不清2小时。头颅CT未见出血，NIHSS评分9分。"
        raw = json.dumps({
            "question": "患者最可能的诊断是什么？",
            "answer": "患者符合急性缺抗性卒中，因为突发偏瘫和CT未见出血。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("QA", raw, source))

    def test_dka_cot_rejects_unsupported_biochemical_or_sodium_claims(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "该患者可能的诊断是什么？",
            "rationale": [
                "多饮、多尿和恶心呕吐提示糖代谢异常。",
                "随机血糖28.6mmol/L明显升高。",
                "尿酮体+++提示酮体生成增多。",
                "血气pH 7.21和HCO3- 12mmol/L提示酸中毒。",
                "这些改变提示体内脱氢酶系统功能异常。",
                "血压降低提示脱钠，可能是低钠血症的表现。"
            ],
            "final_answer": "糖尿病酮症酸中毒，并纠正低钠血症。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_dka_cot_rejects_hco3_increase_contradiction(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "可能的诊断和处理原则是什么？",
            "rationale": "1. 多饮多尿提示糖代谢异常。2. 随机血糖明显升高。3. 尿酮体阳性支持酮症。4. 血气pH降低提示酸中毒。5. HCO3-增高提示代谢性酸中毒。6. 需补液、静脉胰岛素并监测电解质。",
            "final_answer": "考虑糖尿病酮症酸中毒，应立即补液、静脉胰岛素并监测电解质。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_cot_rejects_short_non_step_rationale_even_if_final_answer_correct(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿何种疾病可能性最大？",
            "rationale": "儿童发热咳嗽、湿啰音、白细胞及CRP升高，且胸片显示右下肺片状浸润影，优先考虑细菌性肺炎。",
            "final_answer": "细菌性肺炎是当前最可能的诊断，建议进行抗菌治疗和支持治疗。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_cot_normalizes_rich_paragraph_rationale_to_numbered_steps(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿何种疾病可能性最大？",
            "rationale": "患儿出现发热、咳嗽、气促等症状已有4天，进一步结合查体呼吸频率增加至34次/分，右下肺可闻及湿啰音；辅助检查显示白细胞计数显著升高，达到12.8×10^9/L，中性粒细胞比例高达82%，CRP升高，而胸片显示右下肺有片状浸润影。这些表现符合细菌性感染的特征，应优先考虑细菌性肺炎。",
            "final_answer": "细菌性肺炎是患儿目前最可能的诊断，建议进行抗生素治疗和支持治疗。"
        }, ensure_ascii=False)

        parsed = synth._try_parse_and_validate("CoT", raw, source)

        self.assertIsNotNone(parsed)
        self.assertIn("1.", parsed["rationale"])
        self.assertIn("3.", parsed["rationale"])
        self.assertIn("细菌性肺炎", parsed["rationale"])

    def test_pneumonia_repair_prompt_does_not_leak_groin_guardrails(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"

        prompt = synth._render_repair_prompt("CoT", source, "上一轮输出太短")

        self.assertIn("细菌性肺炎", prompt)
        self.assertNotIn("腹股沟", prompt)
        self.assertNotIn("嵌顿性", prompt)

    def test_pneumonia_cot_rejects_unrelated_groin_final_answer(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿何种疾病可能性最大？",
            "rationale": "患儿发热咳嗽和气促提示呼吸系统感染，右下肺湿啰音提示肺部病变，白细胞计数升高提示感染，中性粒细胞比例高支持细菌感染，CRP升高提示炎症反应，胸片片状浸润影支持肺炎。",
            "final_answer": "建议进行抗生素治疗和外科评估，优先考虑嵌顿性腹股沟疝并肠梗阻病例。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_cot_rejects_prompt_field_artifacts(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿最可能的诊断是什么？",
            "rationale": [
                "发热、咳嗽和气促提示呼吸道感染。",
                "右下肺湿啰音提示肺部病变。",
                "白细胞和中性粒细胞升高提示细菌感染。",
                "CRP升高支持急性炎症反应。",
                "胸片片状浸润影支持肺炎。",
                "preference 中 chosen 应支持经验性抗生素治疗，不得把抗病毒优先方案作为 chosen。"
            ],
            "final_answer": "考虑细菌性肺炎。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_pneumonia_preference_rejects_crp_contradiction(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿应如何诊断和治疗？",
            "chosen": "细菌性肺炎。白细胞升高及正常CRP支持感染，建议经验性抗生素治疗。",
            "rejected": "仅观察，不进行抗感染治疗。",
            "preference_reason": "chosen 覆盖诊断和治疗。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_cot_prompts_do_not_leak_preference_guardrails_for_pneumonia(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"

        first_prompt = synth._render_prompt("CoT", source)
        repair_prompt = synth._render_second_repair_prompt("CoT", source, "上一轮输出混入 preference 规则")

        for prompt in [first_prompt, repair_prompt]:
            self.assertIn("细菌性肺炎", prompt)
            self.assertIn("rationale", prompt)
            self.assertRegex(prompt, r"(不得|不要)使用数组")
            self.assertNotIn("Preference 中", prompt)
            self.assertNotIn("chosen", prompt)
            self.assertNotIn("rejected", prompt)

    def test_pneumonia_preference_rejects_false_no_bacterial_evidence_reason(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = json.dumps({
            "question": "患儿的发热、咳嗽和气促症状应优先考虑何种肺炎？",
            "chosen": "细菌性肺炎。发热、高白细胞计数、中性粒细胞比例高、CRP升高以及胸片发现右下肺片状浸润影均符合细菌感染的特征。",
            "rejected": "仅抗病毒方案。因为在此类无呼吸道症状或无细菌证据的病例中给予抗生素可能不适当。",
            "preference_reason": "以上指标和检查结果符合细菌感染的典型特征，优先考虑细菌性肺炎有助于指导使用抗生素或进行针对性治疗。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_chinese_medical_output_rejects_unapproved_english_tokens(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "可能的诊断和处理原则是什么？",
            "answer": "患者可能为糖尿病酮症酸中毒，应先补液以改善循环 volume，再使用静脉胰岛素并监测电解质。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("QA", raw, source))

    def test_acute_stroke_rejects_unsupported_named_signs_or_collateral_claims(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。突发右侧肢体无力伴言语不清2小时。头颅CT未见出血，NIHSS评分9分。"
        raw = json.dumps({
            "question": "患者可能的诊断是什么？",
            "answer": "患者可能是急性缺血性卒中，尤其符合阿瑟曼征和侧枝循环障碍的特征。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("QA", raw, source))

    def test_dka_cot_rejects_json_artifacts_and_neurologic_invention(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "可能的诊断是什么？",
            "rationale": "1. 血糖明显升高。2. 尿酮体+++提示酮症。3. pH降低提示酸中毒。4. 应考虑糖尿病酮症酸中毒。5. 监测电解质','寻找诱因如感染。6. 不要忽略可能由神经系统损伤引起的恶心呕吐。",
            "final_answer": "考虑糖尿病酮症酸中毒，但不要忽略可能由神经系统损伤引起的恶心呕吐。",
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_dka_cot_rejects_neurologic_invention_even_with_core_treatment(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "可能的诊断和处理原则是什么？",
            "rationale": [
                "随机血糖明显升高提示高血糖状态。",
                "尿酮体+++提示酮体增多。",
                "pH 7.21和HCO3- 12mmol/L提示酸中毒。",
                "综合考虑糖尿病酮症酸中毒。",
                "需要液体复苏、静脉胰岛素和电解质监测纠正。",
                "不要忽略可能由神经系统损伤引起的恶心呕吐。"
            ],
            "final_answer": "考虑糖尿病酮症酸中毒，应补液、静脉胰岛素并监测电解质，但不要忽略神经系统损伤。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_stroke_preference_rejects_prompt_artifacts_and_rejecting_thrombectomy_path(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。突发右侧肢体无力伴言语不清2小时。头颅CT未见出血，NIHSS评分9分。"
        raw = json.dumps({
            "question": "急性缺血性卒中应如何处置？",
            "chosen": "优先静脉溶栓，根据既往规则和证据分析急性缺血性卒中可以被诊断为准确且迅速的处理。",
            "rejected": "机械取栓或根据其他不原始的诊断建议。",
            "preference_reason": "根据时间窗和影像证据，静脉溶栓更好。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", raw, source))

    def test_pneumonia_preference_prompt_requires_same_case_rejected_answer(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"

        prompt = synth._render_repair_prompt("Preference", source, "rejected 写成不适用和妇科疾病")

        self.assertIn("仅抗病毒", prompt)
        self.assertIn("延误抗生素", prompt)
        self.assertIn("不得写不适用", prompt)
        self.assertIn("不得写无呼吸道症状", prompt)
        self.assertIn("不得写无细菌证据", prompt)

    def test_pneumonia_failed_repair_output_sanitizes_false_no_evidence_claims(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患儿，男，6岁。发热、咳嗽4天，气促1天，右下肺湿啰音，白细胞12.8×10^9/L，中性粒细胞82%，CRP升高，胸片提示右下肺片状浸润影。"
        raw = "rejected: 仅抗病毒方案。因为在此类无呼吸道症状或无细菌证据的病例中给予抗生素可能不适当。"

        sanitized = synth._sanitize_failed_repair_output(source, raw)
        prompt = synth._render_second_repair_prompt("Preference", source, raw)

        self.assertNotIn("无呼吸道症状", sanitized)
        self.assertNotIn("无细菌证据", sanitized)
        self.assertIn("忽视已有细菌感染证据", sanitized)
        self.assertIn("不得写无细菌证据", prompt)

    def test_stroke_preference_prompt_requires_same_case_rejected_answer(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，男，67岁。突发右侧肢体无力伴言语不清2小时。头颅CT未见出血，NIHSS评分9分。"

        prompt = synth._render_repair_prompt("Preference", source, "chosen 写了根据既往规则，rejected 写机械取栓")

        self.assertIn("不得写既往规则", prompt)
        self.assertIn("rejected 不得否定机械取栓", prompt)
        self.assertIn("仅观察", prompt)
        self.assertIn("延误溶栓", prompt)

    def test_rejects_obvious_garbled_or_schema_artifact_text(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        dka_source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        bad_pref = json.dumps({
            "question": "可能的糖尿病酮症酸中毒",
            "chosen": "补液和静脉 insulin 曓补充胰岛素，纠正电解质失衡",
            "rejected": "常规检查和观察，无具体治疗方向",
            "preference_reason": "chosen 提供了紧急生命体征支持。"
        }, ensure_ascii=False)
        bad_cot = json.dumps({
            "question": "可能的诊断是什么？",
            "rationale": [
                "血糖显著升高至28.6mmol/L。",
                "尿酮体检测为+++。",
                "血气分析显示pH 7.21，HCO3- 12mmol/L，提示代谢性酸中毒依据14。",
                "呼吸深快且恶心呕吐加重1天的临床表现依据25。",
                "口唇干燥及心率112次/分，血压96/60mmHg的体征分析依据36。",
                "综合考虑糖尿病酮症酸中毒。"
            ],
            "final_answer": "考虑糖尿病酮症酸中毒，应补液、静脉胰岛素并监测电解质。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("Preference", bad_pref, dka_source))
        self.assertIsNone(synth._try_parse_and_validate("CoT", bad_cot, dka_source))

    def test_qa_normalizes_chinese_answer_alias_field(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = json.dumps({
            "question": "可能的诊断和处理原则是什么？",
            "处理原则": "患者可能患有糖尿病酮症酸中毒，需补液、静脉胰岛素并监测电解质。",
        }, ensure_ascii=False)

        parsed = synth._try_parse_and_validate("QA", raw, "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21。")

        self.assertIsNotNone(parsed)
        self.assertIn("糖尿病酮症酸中毒", parsed["answer"])

    def test_dka_preference_prompt_requires_treatment_in_chosen(self):
        synth = NativeTemplateSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"

        prompt = synth._render_repair_prompt("Preference", source, "chosen 只写糖尿病酮症酸中毒")

        self.assertIn("chosen 必须同时包含诊断和处理", prompt)
        self.assertIn("补液", prompt)
        self.assertIn("静脉胰岛素", prompt)
        self.assertIn("电解质", prompt)

    def test_dka_cot_rejects_unsupported_hypertension_diagnosis(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        source = "患者，女，52岁。血压96/60mmHg，随机血糖28.6mmol/L，尿酮体+++，血气pH 7.21，HCO3- 12mmol/L。"
        raw = json.dumps({
            "question": "可能的诊断和处理原则是什么？",
            "rationale": [
                "随机血糖28.6mmol/L明显升高。",
                "尿酮体+++提示酮体增多。",
                "pH 7.21和HCO3- 12mmol/L提示代谢性酸中毒。",
                "结合症状和检查考虑糖尿病酮症酸中毒。",
                "需补液、静脉胰岛素和电解质监测纠正。",
                "需寻找诱因。"
            ],
            "final_answer": "可能是糖尿病酮症酸中毒及原发性高血压，应补液和静脉胰岛素治疗。"
        }, ensure_ascii=False)

        self.assertIsNone(synth._try_parse_and_validate("CoT", raw, source))

    def test_qa_truncates_chinese_answer_at_sentence_boundary(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = '''```json
{
  "question": "患者胸痛伴心肌酶升高最可能是什么问题？",
  "answer": "患者反复胸闷胸痛，活动后加重并休息后缓解，近6小时明显加重且伴大汗和恶心。心电图提示II、III、aVF导联ST段抬高，肌钙蛋白升高，最可能为急性下壁ST段抬高型心肌梗死。应尽快启动胸痛中心流程，完善心电监护、复查心肌标志物并评估急诊再灌注治疗。若条件允许，应结合发病时间、出血风险和导管室可及性选择PCI或溶栓，并持续评估血压、心律失常和心力衰竭风险。"
}
```'''

        parsed = synth._try_parse_and_validate("QA", raw)

        self.assertIsNotNone(parsed)
        self.assertLessEqual(len(parsed["answer"]), synth.length_limits["QA"]["answer"])
        self.assertTrue(parsed["answer"].endswith("。"))
        self.assertNotIn("若条件允许", parsed["answer"])

    def test_qa_json_with_unescaped_newline_is_recovered(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = '''```json
{
  "question": "What is the most likely cause of the patient's symptoms?",
  "answer": "The patient's symptoms are most likely caused by a myocardial infarction
given the compressive retrosternal pain and elevated troponins."
}
```'''

        parsed = synth._try_parse_and_validate("QA", raw)

        self.assertIsNotNone(parsed)
        self.assertIn("myocardial infarction", parsed["answer"])

    def test_qa_fenced_json_from_first_pass_is_accepted(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        raw = '''```json
{
  "question": "What is the clinical diagnosis for the patient's symptoms?",
  "answer": "The clinical diagnosis is acute coronary syndrome, specifically an anterior STEMI, based on ECG ST-segment elevation and elevated troponins."
}
```'''

        parsed = synth._try_parse_and_validate("QA", raw)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["question"], "What is the clinical diagnosis for the patient's symptoms?")

    def test_qa_fast_prompt_uses_real_newlines(self):
        synth = MedicalDataSynthesizer(model_path=None, llm_instance=FakeLLM())
        prompt = synth._render_qa_fast_prompt("Case: chest pain.")

        self.assertIn("<|im_start|>system\n", prompt)
        self.assertNotIn("<|im_start|>system\\n", prompt)
        self.assertIn("<|im_start|>assistant\n", prompt)

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
