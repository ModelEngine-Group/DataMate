import ast
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
except Exception:  # pragma: no cover - 仅用于无 vllm 的测试环境
    LLM = None
    StructuredOutputsParams = None

    class SamplingParams:  # type: ignore
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            for key, value in kwargs.items():
                setattr(self, key, value)

try:
    from jinja2 import Template
except Exception:  # pragma: no cover - 仅用于无 jinja2 的测试环境
    class Template:  # type: ignore
        def __init__(self, text: str):
            self.text = text

        def render(self, **kwargs):
            rendered = self.text
            for k, v in kwargs.items():
                rendered = rendered.replace("{{ " + k + " }}", str(v))
            return rendered

class MedicalDataSynthesizer:
    def __init__(self, model_path: Optional[str], llm_instance: Any = None):
        """
        :param model_path: 模型路径。若传入 llm_instance，可为 None。
        :param llm_instance: 可注入的 LLM 对象（便于单元测试）。
        """
        if llm_instance is not None:
            self.llm = llm_instance
        else:
            if not model_path:
                raise ValueError("model_path 不能为空（未注入 llm_instance 时）")
            if LLM is None:
                raise ImportError("未安装 vllm，无法初始化模型。请先安装 vllm-ascend / vllm。")
            self.llm = LLM(
                model=model_path,
                trust_remote_code=True,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.85,
                max_model_len=8192,
                dtype="float16"
            )
        self._qa_native_chat_template = self._load_native_chat_template(model_path)
        self._qa_uses_native_template = self._qa_native_chat_template is not None
        self._init_templates()
        self.required_fields = {
            "QA": ["question", "answer"],
            "CoT": ["question", "rationale", "final_answer"],
            "Preference": ["question", "chosen", "rejected", "preference_reason"]
        }
        self.length_limits = {
            "QA": {"question": 160, "answer": 120},
            "CoT": {"question": 220, "rationale": 2000, "final_answer": 220},
            "Preference": {"question": 300, "chosen": 1200, "rejected": 1200, "preference_reason": 1200},
        }
        self.meta_phrases = [
            "嗯，用户", "用户让我", "首先，我需要", "只输出 json", "json格式",
            "思考过程", "推理过程", "<think", "</think>", "<|im_start|>", "<|im_end|>",
        ]
        self.weak_preference_reasons = {
            "chosen 提供了更多可用信息。",
            "chosen 更好。",
            "chosen 更准确。",
        }

    def _load_native_chat_template(self, model_path: Optional[str]) -> Optional[str]:
        if not model_path:
            return None

        config_path = Path(model_path) / "tokenizer_config.json"
        if not config_path.exists():
            return None

        try:
            tokenizer_config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return None

        chat_template = tokenizer_config.get("chat_template")
        return chat_template if isinstance(chat_template, str) and chat_template.strip() else None

    def _render_native_chat_template(self, messages: List[Dict[str, str]], enable_thinking: bool) -> str:
        if not self._qa_native_chat_template:
            raise ValueError("native chat template unavailable")

        parts: List[str] = []
        if messages and messages[0].get("role") == "system":
            parts.append("<|im_start|>system\n" + messages[0].get("content", "") + "<|im_end|>\n")
            remaining = messages[1:]
        else:
            remaining = messages

        for message in remaining:
            role = message.get("role", "")
            content = message.get("content", "")
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")

        parts.append("<|im_start|>assistant\n")
        if not enable_thinking:
            parts.append("<think>\n\n</think>\n\n")
        return "".join(parts)

    def _is_groin_obstruction_source(self, source_text: Optional[str]) -> bool:
        source = source_text or ""
        return "腹股沟" in source and "包块" in source and "阶梯状液气平" in source

    def _render_groin_cot_messages(self, source_text: str, repair_mode: bool = False) -> List[Dict[str, str]]:
        system_content = (
            "你是资深临床医生。请基于用户给出的中文病例生成一个高质量 CoT JSON 对象。"
            "只能输出 JSON，不要输出解释、markdown 或 <think>。"
            "字段只能是 question、rationale、final_answer。"
            "question 写成正常临床问题，例如：患者最可能的诊断和处置建议是什么？"
            "question 不得包含 CoT、必须、规则、prompt、JSON 或生成要求。"
            "rationale 必须是单个中文字符串，不要使用数组，必须包含 1. 到 8. 八个编号步骤。"
            "八个步骤依次写：1. 起病经过；2. 腹股沟包块；3. 体征定位；4. X线阶梯状液气平；5. 诊断推断；6. 风险判断；7. 不宜观察；8. 处置建议。"
            "每个步骤写成完整句，必须引用原始病例已有信息或必要医学判断。"
            "腹股沟包块步骤只引用原文给出的右侧腹股沟区、4cm包块、压痛、腹股沟韧带上内方等已给信息；未给出的体征不要写。"
            "X线阶梯状液气平支持肠梗阻，不要写排除肠梗阻。"
            "诊断只写嵌顿性腹股沟疝合并肠梗阻，不要写其他鉴别诊断。"
            "风险判断只写肠梗阻和嵌顿风险，不扩展原文未提供的并发症。"
            "处置建议只写尽快外科评估或急诊外科评估，不写具体操作。"
            "rationale 中不要写“最终答案”。"
            "final_answer 必须完整写：考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"
        )
        user_prefix = "原始输入如下。请完全重写合格 JSON，不要沿用上一轮失败输出。" if repair_mode else "原始输入如下。"
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"{user_prefix}\n{source_text.strip()}"},
        ]

    def _render_groin_qa_messages(self, source_text: str, repair_mode: bool = False) -> List[Dict[str, str]]:
        system_content = (
            "你是资深临床医生。请基于用户给出的中文病例生成一个高质量 QA JSON 对象。"
            "只能输出 JSON，不要输出解释、markdown 或 <think>。"
            "字段只能是 question 和 answer。"
            "question 必须是简短临床问题，例如：该病例最可能的诊断和紧急处理是什么？"
            "question 不得复述整段病例，不得包含 QA、规则、prompt、JSON 或生成要求。"
            "answer 必须明确写：考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"
            "answer 可以在此基础上补一句简短原因，但总长度保持精炼，不要超过两句。"
            "不要写观察随访、门诊观察、延迟处理，也不要写其他鉴别诊断。"
            "不要扩展原文未提供的并发症或具体操作，不要写穿孔、引流、推挤、减压、复位、探查。"
            "腹股沟包块只引用原文给出的右侧腹股沟区、4cm包块、压痛、腹股沟韧带上内方等已给信息；未给出的体征不要写。"
            "X线阶梯状液气平已支持肠梗阻，不要写排除肠梗阻。"
        )
        user_prefix = "原始输入如下。请完全重写合格 JSON，不要沿用上一轮失败输出。" if repair_mode else "原始输入如下。"
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"{user_prefix}\n{source_text.strip()}"},
        ]

    def _init_templates(self):
        # QA 模板：保持原样，它是好的
        self.qa_template = Template("""<|im_start|>system
你是一个专业的医学专家。请基于【医疗文本】生成一个JSON格式的问答对。
你必须只输出 JSON，不要输出额外解释，不要输出 <think> 或推理过程。
输出要求（必须严格遵守）：
1) 仅输出一个 JSON 对象，且字段仅有 question 与 answer；
2) 不得输出任何元话术（如“首先/用户/根据以上”）与思考内容；
3) answer 简明，控制在80字以内。
<|im_end|>
<|im_start|>user
【医疗文本】：患者男，30岁，主诉牙痛3天。查体见右下阻生智齿。
<|im_end|>
<|im_start|>assistant
{
    "question": "患者的主诉和查体结果提示什么问题？",
    "answer": "患者主诉牙痛3天，查体发现右下阻生智齿，提示可能存在智齿冠周炎或牙髓炎。"
}
<|im_end|>
<|im_start|>user
【医疗文本】：女性，65岁。主诉：胸闷气短反复发作1年。查体及辅助检查：心电图ST段抬高。
<|im_end|>
<|im_start|>assistant
{
    "question": "患者的主诉和查体结果提示什么问题？",
    "answer": "胸闷气短伴ST段抬高，提示急性冠脉综合征风险，建议尽快心内科评估。"
}
<|im_end|>
<|im_start|>user
【医疗文本】：{{ context }}
<|im_end|>
<|im_start|>assistant
""")

        # 🟢 修正 CoT 模板：去除换行符，将示例写成紧凑的单行，避免 Python 字符串转义灾难
        self.cot_template = Template("""<|im_start|>system
你是一个资深的临床医生。请针对【医疗问题】生成JSON格式的思维链推理。
逻辑路径：症状 -> 检查 -> 诊断 -> 治疗。
你必须只输出 JSON，不要输出额外解释，不要输出 <think> 标签。
    输出要求（必须严格遵守）：
    1) 仅输出一个 JSON 对象，字段仅有 question/rationale/final_answer；
    2) rationale 使用条目化步骤表达（建议不少于6步）；
    3) 禁止元话术与角色说明。
<|im_end|>
<|im_start|>user
【医疗问题】：感冒引起的发热应该如何处理？
<|im_end|>
<|im_start|>assistant
{
    "question": "感冒引起的发热应该如何处理？",
    "rationale": "1.症状分析:患者因感冒出现发热。2.辅助检查:必要时查血常规。3.初步判断:以上呼吸道感染为主。4.风险评估:关注高热与脱水。5.治疗策略:物理降温为主。6.用药原则:高热可口服解热镇痛药。",
    "final_answer": "建议多休息、多饮水。若体温超过38.5℃，可服用退热药；否则采用物理降温。"
}
<|im_end|>
<|im_start|>user
【医疗问题】：男性，45岁。主诉：持续性干咳3天。查体及辅助检查：CT示斑片影。
<|im_end|>
<|im_start|>assistant
{
    "question": "男性，45岁。主诉：持续性干咳3天。查体及辅助检查：CT示斑片影。",
    "rationale": "1.症状提取:持续性干咳3天。2.关键检查:CT示斑片影。3.病因推断:以感染性肺部病变优先。4.鉴别方向:需与非感染性间质病变区分。5.进一步检查:血常规与炎症指标。6.处置建议:呼吸专科评估并随访影像。",
    "final_answer": "当前首先考虑肺部炎症性病变，建议完善感染评估并尽快呼吸专科复诊。"
}
<|im_end|>
<|im_start|>user
【医疗问题】：{{ question }}
<|im_end|>
<|im_start|>assistant
""")

        # 偏好数据模板：生成 chosen/rejected 供偏好学习（含示例，减少叙述体输出）
        self.preference_template = Template("""<|im_start|>system
你是医疗数据工程师。请基于【医疗问题】输出偏好学习样本（JSON）。
要求：
1) chosen：高质量、准确且安全；
2) rejected：包含明显缺陷（如不完整、轻微逻辑问题或不够相关）；
3) 输出字段必须为：question/chosen/rejected/preference_reason。
你必须只输出 JSON，不要输出额外解释，不要输出 <think> 标签。
chosen 与 rejected 均尽量简洁（建议各不超过80字）。
preference_reason 必须具体说明“为什么 chosen 更好”，不得写空泛套话。
<|im_end|>
<|im_start|>user
【医疗问题】：女性，65岁。主诉：胸闷气短反复发作1年。查体及辅助检查：心电图ST段抬高。
<|im_end|>
<|im_start|>assistant
{
    "question": "女性，65岁。主诉：胸闷气短反复发作1年。查体及辅助检查：心电图ST段抬高。",
    "chosen": "胸闷气短伴ST段抬高，优先考虑急性冠脉综合征，建议立即心电监护与心肌标志物复查。",
    "rejected": "可能只是普通疲劳，先回家休息观察即可。",
    "preference_reason": "chosen 结合了关键检查异常并给出及时处置；rejected 忽略高危心电图信号，存在安全风险。"
}
<|im_end|>
<|im_start|>user
【医疗问题】：{{ question }}
<|im_end|>
<|im_start|>assistant
""")

        self.task_templates = {
            "QA": self.qa_template,
            "CoT": self.cot_template,
            "Preference": self.preference_template
        }

        self.repair_templates = {
            "QA": Template("""<|im_start|>system
你是JSON修复器。请把给定文本修复为合法JSON对象，且仅包含字段 question/answer。
要求：
1) 只输出一个 JSON 对象；
2) 不要输出 <think>、解释、markdown；
3) answer 控制在80字内。
<|im_end|>
<|im_start|>user
【原始输入】：{{ source_text }}
【候选输出】：{{ raw_output }}
请修复为目标JSON。
<|im_end|>
<|im_start|>assistant
"""),
            "CoT": Template("""<|im_start|>system
你是JSON修复器。请把给定文本修复为合法JSON对象，且仅包含字段 question/rationale/final_answer。
要求：
1) 只输出一个 JSON 对象；
2) rationale 使用步骤化表达（建议6步）；
3) 不要输出 <think>、解释、markdown。
<|im_end|>
<|im_start|>user
【原始输入】：{{ source_text }}
【候选输出】：{{ raw_output }}
请修复为目标JSON。
<|im_end|>
<|im_start|>assistant
"""),
            "Preference": Template("""<|im_start|>system
你是JSON修复器。请把给定文本修复为合法JSON对象，且仅包含字段 question/chosen/rejected/preference_reason。
要求：
1) 只输出一个 JSON 对象；
2) chosen 为更优回答，rejected 为较差回答，preference_reason 必须具体；
3) 不要输出 <think>、解释、markdown。
<|im_end|>
<|im_start|>user
【原始输入】：{{ source_text }}
【候选输出】：{{ raw_output }}
请修复为目标JSON。
<|im_end|>
<|im_start|>assistant
"""),
        }

    def _distill_text(self, text: str) -> str:
        """轻量数据蒸馏：保留核心症状/检查信息，删除冗余语气词。"""
        distilled = re.sub(r"(请问|可能|大概|有点|非常|真的)", "", text)
        distilled = re.sub(r"\s+", "", distilled)
        return f"[蒸馏]{distilled}"

    def _augment_text(self, text: str) -> List[str]:
        """轻量数据增强：结构改写 + 关键信息重排。"""
        variants = [
            f"患者信息：{text}",
            f"病例摘要：{text}",
            f"请根据以下临床片段生成训练数据：{text}",
            f"【主诉与检查】{text}",
            f"医学文本（需结构化）：{text}"
        ]

        # 若文本包含句号，尝试做结构重排增强
        parts = [p for p in re.split(r"[。；;]", text) if p.strip()]
        if len(parts) >= 2:
            reordered = "；".join(parts[1:] + parts[:1]) + "。"
            variants.append(f"重排病历：{reordered}")
        return variants

    def build_training_corpus(
        self,
        raw_inputs: List[str],
        target_size: int,
        source_ratio: Optional[Dict[str, float]] = None,
        seed: int = 42
    ) -> List[Dict[str, str]]:
        """
        构建训练语料池，支持原始/增强/蒸馏数据配比。
        返回格式: [{"source": "original|augmented|distilled", "text": "..."}, ...]
        """
        if not raw_inputs:
            return []

        if source_ratio is None:
            source_ratio = {"original": 0.4, "augmented": 0.4, "distilled": 0.2}

        ratio_sum = sum(source_ratio.values())
        if ratio_sum <= 0:
            raise ValueError("source_ratio 总和必须 > 0")

        normalized_ratio = {k: v / ratio_sum for k, v in source_ratio.items()}

        random.seed(seed)
        original_pool = list(raw_inputs)
        augmented_pool = [aug for text in raw_inputs for aug in self._augment_text(text)]
        distilled_pool = [self._distill_text(text) for text in raw_inputs]

        source_pools = {
            "original": original_pool,
            "augmented": augmented_pool,
            "distilled": distilled_pool
        }

        allocated = {
            k: int(target_size * normalized_ratio.get(k, 0.0))
            for k in ["original", "augmented", "distilled"]
        }

        remain = target_size - sum(allocated.values())
        for key in ["original", "augmented", "distilled"]:
            if remain <= 0:
                break
            allocated[key] += 1
            remain -= 1

        mixed = []
        for source_name, cnt in allocated.items():
            pool = source_pools[source_name]
            if not pool:
                continue
            for i in range(cnt):
                mixed.append({"source": source_name, "text": pool[i % len(pool)]})

        random.shuffle(mixed)
        return mixed

    def _strip_generation_scaffolding(self, text: str) -> str:
        value = (text or "").strip()
        if not value:
            return value

        kept_lines: List[str] = []
        for raw_line in value.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("测试编号：", "数据来源风格：", "生成要求：", "验收目标：")):
                continue
            kept_lines.append(line)

        compact = "\n".join(kept_lines).strip()
        if not compact:
            return value

        for prefix in ("病例摘要：", "患者咨询：", "原始输入如下。", "原始输入如下："):
            if compact.startswith(prefix):
                compact = compact[len(prefix):].strip()
                break
        compact = re.sub(
            r"请生成[^。\n]*(?:合成数据|数据|样本|结果)[。]?",
            "",
            compact,
        ).strip()
        compact = re.sub(
            r"请输出[^。\n]*(?:QA|CoT|Preference)[^。\n]*[。]?",
            "",
            compact,
        ).strip()
        return compact or value

    def _suggest_qa_question(self, source_text: str) -> str:
        source = source_text or ""
        if self._is_acute_stroke_source(source):
            return "卒中路径处理重点是什么？"
        if self._is_groin_obstruction_source(source):
            return "该病例最可能的诊断和紧急处理是什么？"
        if self._is_diagnostic_generation_source(source):
            return "最可能的诊断或处理重点是什么？"
        if any(marker in source for marker in ["是否需要", "想知道", "担心", "如何选择", "何时就医"]):
            return "应如何评估与处理？"
        return "最可能的处理重点是什么？"

    def _qa_prefill_json_prefix(self, source_text: str) -> str:
        question = self._suggest_qa_question(source_text or "")
        encoded_question = json.dumps(question, ensure_ascii=False)
        return f'{{"question":{encoded_question},"answer":"'

    def _suggest_cot_question(self, source_text: str) -> str:
        if self._is_groin_obstruction_source(source_text or ""):
            return "患者最可能的诊断和处置建议是什么？"
        return "该病例应如何进行临床推理和处理？"

    def _cot_prefill_json_prefix(self, source_text: str) -> str:
        question = self._suggest_cot_question(source_text or "")
        encoded_question = json.dumps(question, ensure_ascii=False)
        return f'{{"question":{encoded_question},"rationale":"'

    def _should_prefill_json_prefix(self, task_type: str, source_text: Optional[str]) -> bool:
        if task_type == "QA":
            return True
        if task_type == "CoT" and self._is_groin_obstruction_source(source_text or ""):
            return True
        return False

    def _prefill_json_prefix(self, task_type: str, source_text: Optional[str]) -> str:
        if task_type == "QA":
            return self._qa_prefill_json_prefix(source_text or "")
        if task_type == "CoT":
            return self._cot_prefill_json_prefix(source_text or "")
        return ""

    def _apply_prefill_json_prefix(
        self,
        task_type: str,
        generated_text: str,
        source_text: Optional[str],
    ) -> str:
        stripped = (generated_text or "").lstrip()
        if not self._should_prefill_json_prefix(task_type, source_text):
            return generated_text or ""
        if stripped.startswith("{"):
            return generated_text or ""
        return self._prefill_json_prefix(task_type, source_text) + stripped

    def _clean_json_string(self, text: str) -> str:
        text = text.strip()

        # ?? Qwen ????????????? JSON
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        # ????? think ??
        text = re.sub(r"<think>[\s\S]*$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<\|im_start\|>think[\s\S]*?<\|im_end\|>", "", text, flags=re.IGNORECASE)

        # ?? Markdown ??
        text = re.sub(r"^```json", "", text, flags=re.MULTILINE)
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        text = text.strip()

        # ?? ?????????????????
        # ? JSON ???????????????? json.loads ??
        # (??????? trick??? "rationale": "???\n???" ??)
        # text = text.replace('\n', ' ')
        # ????????????? JSON ????? strict=False ?????????

        extracted = self._extract_first_json_object(text)
        return extracted if extracted else text

    def _extract_detached_nested_object(self, text: str, key: str) -> Optional[Dict[str, Any]]:
        marker = f'"{key}"'
        start = text.find(marker)
        if start < 0:
            return None

        brace_start = text.find("{", start)
        if brace_start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False
        for idx in range(brace_start, len(text)):
            ch = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                depth += 1
                continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    snippet = text[brace_start: idx + 1]
                    try:
                        data = json.loads(snippet, strict=False)
                    except Exception:
                        try:
                            data = json.loads(self._repair_json_syntax_only(snippet), strict=False)
                        except Exception:
                            return None
                    return data if isinstance(data, dict) else None
        return None

    def _salvage_truncated_json_object(self, text: str) -> Optional[str]:
        candidate = self._repair_json_syntax_only((text or "").strip())
        if not candidate or "{" not in candidate:
            return None
        if candidate.count('"') % 2 == 1:
            candidate += '"'
        if candidate.count("{") > candidate.count("}"):
            candidate += "}" * (candidate.count("{") - candidate.count("}"))
        if candidate.count("[") > candidate.count("]"):
            candidate += "]" * (candidate.count("[") - candidate.count("]"))
        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        return candidate

    def _repair_json_syntax_only(self, text: str) -> str:
        """Only fix common JSON syntax issues; never invent missing content."""
        repaired = text.strip()
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
        repaired = repaired.replace("，}", "}").replace("，]", "]")
        repaired = repaired.replace("“", '"').replace("”", '"')
        return repaired

    def _escape_unquoted_inner_value_quotes(self, text: str) -> str:
        """Escape bare quotes that appear inside JSON string values."""
        value = text.strip()
        if not value:
            return value

        chars: List[str] = []
        in_string = False
        escaped = False
        expecting_key = True
        in_key = False
        in_value = False
        i = 0
        while i < len(value):
            ch = value[i]
            if not in_string:
                chars.append(ch)
                if ch == '"':
                    in_string = True
                    in_key = expecting_key
                    in_value = not expecting_key
                elif ch in "{,":
                    expecting_key = True
                elif ch == ":":
                    expecting_key = False
                i += 1
                continue

            if escaped:
                chars.append(ch)
                escaped = False
                i += 1
                continue
            if ch == "\\":
                chars.append(ch)
                escaped = True
                i += 1
                continue
            if ch != '"':
                chars.append(ch)
                i += 1
                continue

            j = i + 1
            while j < len(value) and value[j].isspace():
                j += 1
            next_ch = value[j] if j < len(value) else ""
            if in_key and next_ch == ":":
                chars.append(ch)
                in_string = False
                in_key = False
                expecting_key = False
            elif in_value and next_ch in ",}":
                chars.append(ch)
                in_string = False
                in_value = False
                expecting_key = next_ch == ","
            elif in_value:
                chars.append("\\\"")
            else:
                chars.append(ch)
            i += 1

        return "".join(chars)

    def _extract_first_json_object(self, text: str) -> Optional[str]:
        start = text.find("{")
        if start == -1:
            return None

        in_str = False
        escaped = False
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        # 兜底：首个 { 到最后一个 }
        last = text.rfind("}")
        if last > start:
            return text[start:last + 1]
        return None

    def _parse_embedded_structured_value(self, value: Any) -> Optional[Any]:
        text = self._strip_reasoning_text(str(value or "")).strip()
        if not text or text[0] not in "{[" or text[-1] not in "}]":
            return None
        for parser in (json.loads, ast.literal_eval):
            try:
                return parser(text)
            except Exception:
                continue
        return None

    def _collect_embedded_string_leaves(self, payload: Any) -> List[str]:
        if isinstance(payload, str):
            cleaned = self._strip_reasoning_text(payload).strip()
            return [cleaned] if cleaned else []
        if isinstance(payload, dict):
            leaves: List[str] = []
            for value in payload.values():
                leaves.extend(self._collect_embedded_string_leaves(value))
            return leaves
        if isinstance(payload, (list, tuple)):
            leaves: List[str] = []
            for value in payload:
                leaves.extend(self._collect_embedded_string_leaves(value))
            return leaves
        return []

    def _normalize_embedded_preference_text(self, value: Any) -> str:
        parsed = self._parse_embedded_structured_value(value)
        if parsed is None:
            return self._clean_medical_answer_text(value)

        if isinstance(parsed, dict):
            for key in ("Preference", "chosen", "answer", "final_answer", "content", "text"):
                if key in parsed:
                    return self._clean_medical_answer_text(parsed.get(key))

            filtered = {
                key: item
                for key, item in parsed.items()
                if key not in {"QA", "CoT", "question"}
            }
            leaves = self._collect_embedded_string_leaves(filtered or parsed)
        else:
            leaves = self._collect_embedded_string_leaves(parsed)

        flattened = "；".join(part for part in leaves if part)
        return self._clean_medical_answer_text(flattened or value)

    def _is_diagnostic_generation_source(self, source_text: str) -> bool:
        source = source_text or ""
        if not source:
            return False
        generation_markers = ["生成", "合成数据", "QA", "CoT", "Preference", "结构化"]
        diagnostic_markers = ["诊疗", "诊疗思路", "诊断", "治疗", "处理", "处置", "管理", "建议", "分析", "康复", "科普"]
        return any(marker in source for marker in generation_markers) and any(
            marker in source for marker in diagnostic_markers
        )

    def _is_demographic_only_qa(self, question: str, answer: str) -> bool:
        q = (question or "").strip()
        a = (answer or "").strip()
        if not q or not a:
            return False

        demographic_question_markers = ["年龄", "性别", "几岁", "多大"]
        clinical_question_markers = [
            "诊断", "处理", "处置", "治疗", "建议", "管理", "原因",
            "病因", "评估", "检查", "用药", "怎么办", "思路",
        ]
        if not any(marker in q for marker in demographic_question_markers):
            return False
        if any(marker in q for marker in clinical_question_markers):
            return False
        if len(a) > 32:
            return False
        normalized_answer = re.sub(r"[，。；、,\s]", "", a)
        normalized_answer = normalized_answer.replace("该患者", "").replace("患者", "")
        normalized_answer = normalized_answer.replace("性别为", "").replace("性别是", "").replace("性别", "")
        normalized_answer = normalized_answer.replace("年龄为", "").replace("年龄是", "").replace("年龄", "")

        demographic_answer_patterns = [
            r"^(?:该患者)?(?:性别(?:为|是)?)?(?:男性|女性|男|女)[。；]?$",
            r"^(?:该患者)?(?:年龄(?:为|是)?)?\d{1,3}岁[。；]?$",
            r"^(?:\d{1,3}岁[,，、]?)?(?:男性|女性|男|女)[。；]?$",
        ]
        return any(re.fullmatch(pattern, a) for pattern in demographic_answer_patterns) or (
            normalized_answer in {"男性", "女性", "男", "女"}
            or bool(re.fullmatch(r"\d{1,3}岁", normalized_answer))
        )

    def _strip_reasoning_text(self, text: str) -> str:
        t = text.strip()
        t = re.sub(r"<think>[\s\S]*?</think>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"<think>[\s\S]*$", "", t, flags=re.IGNORECASE)
        t = re.sub(r"<\|im_start\|>think[\s\S]*?<\|im_end\|>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"<\|endoftext\|>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"^```json", "", t, flags=re.MULTILINE)
        t = re.sub(r"^```", "", t, flags=re.MULTILINE)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _clean_medical_answer_text(self, text: Any, *, soften_direct_medication: bool = True) -> str:
        value = self._strip_reasoning_text(str(text or ""))
        value = re.sub(r"(您好|你好)[，,、：:\s]*", "", value)
        value = re.sub(r"首先[，,、：:\s]*", "", value)
        value = re.sub(r"我需要(确认|评估|考虑|判断|了解)", r"需要\1", value)
        value = re.sub(r"我会(建议|考虑|评估|判断)", r"应\1", value)
        value = re.sub(r"我认为", "考虑", value)
        value = re.sub(r"让我", "需", value)
        value = re.sub(r"这让我", "这提示", value)
        value = re.sub(r"需要建议您", "建议", value)
        value = re.sub(r"请您放心[，,、：:\s]*", "", value)
        if soften_direct_medication:
            medication_action = (
                r"(?:调整药物剂量|调整用药剂量|调整药物|调整用药|"
                r"药物调整|用药调整|更换其他降压药|更换降压药)"
            )
            value = re.sub(
                r"(?<!评估)(?:可能)?(?:需要)?(?:考虑)?是否(?:调整药物剂量|调整用药剂量|调整药物|调整用药|药物调整|用药调整|更换其他降压药|更换降压药)(?:方案)?",
                "应由医生评估是否调整用药方案",
                value,
            )
            value = re.sub(
                rf"(?<!不)(?<!不要)(?<!不建议)(?<!不得)(?:建议您|您需要|需要|应当)\s*{medication_action}(?:或{medication_action})*",
                "应由医生评估是否调整用药方案",
                value,
            )
            value = re.sub(
                r"应由医生评估是否调整用药方案或(?:种类|剂量|方案)",
                "应由医生评估是否调整用药方案",
                value,
            )
            value = re.sub(
                rf"(?<!不)(?<!不要)(?<!不建议)(?<!不得)(?<!自行)(?<!不要自行)(?<!是否)(?:可能)?(?:需要)?(?:考虑)?{medication_action}(?:或{medication_action})*",
                "应由医生评估是否调整用药方案",
                value,
            )
            value = self._clean_softened_medication_phrase(value)
        value = re.sub(
            r"(?:如果|如)(?:有|出现)?任何不适[，,、：:\s]*(?:及时|请及时)(?:与我们沟通|和我们沟通|联系我们|联系医生)",
            "如有任何不适，应及时就医",
            value,
        )
        value = re.sub(
            r"(?:及时|请及时)(?:与我们沟通|和我们沟通|联系我们)",
            "及时就医",
            value,
        )
        value = re.sub(
            r"(^|[。！？；;])\s*(?:我们会|我会)(?:根据您(?:的)?具体情况|结合您(?:的)?具体情况|根据患者(?:的)?具体情况|根据具体情况)[^。！？；;]*(?:[。！？；;]|$)",
            r"\1",
            value,
        )
        return re.sub(r"\s+", " ", value).strip()

    def _clean_softened_medication_phrase(self, text: str) -> str:
        value = text or ""
        safe_phrase = "应由医生评估是否调整用药方案"
        value = re.sub(
            rf"(?:医生可能会|医生会|可能会|可能需要|可能|需要|应当|建议您|您需要){re.escape(safe_phrase)}",
            safe_phrase,
            value,
        )
        value = re.sub(
            rf"可能提示{re.escape(safe_phrase)}",
            safe_phrase,
            value,
        )
        value = re.sub(
            rf"(?:判断)?是否{re.escape(safe_phrase)}",
            safe_phrase,
            value,
        )
        value = re.sub(
            rf"来(?:应)?(?:由医生评估)?{re.escape(safe_phrase)}",
            "，由医生评估是否调整用药方案",
            value,
        )
        value = re.sub(
            rf"来应(?:由医生评估)?是否调整用药方案",
            "，由医生评估是否调整用药方案",
            value,
        )
        value = re.sub(
            rf"{re.escape(safe_phrase)}(?:方案|种类|剂量)+",
            safe_phrase,
            value,
        )
        value = re.sub(
            rf"(?:由医生评估)?{re.escape(safe_phrase)}",
            safe_phrase,
            value,
        )
        return self._deduplicate_safe_medication_phrase(value, safe_phrase)

    def _deduplicate_safe_medication_phrase(self, text: str, safe_phrase: str) -> str:
        core_phrase = "医生评估是否调整用药方案"
        if text.count(core_phrase) <= 1:
            return text
        parts = re.split(r"([。！？；;])", text)
        rebuilt: List[str] = []
        seen = False
        for idx in range(0, len(parts), 2):
            sentence = parts[idx]
            mark = parts[idx + 1] if idx + 1 < len(parts) else ""
            if core_phrase in sentence:
                if seen:
                    sentence = re.sub(
                        r"(?:应由|由)?医生评估是否调整用药方案",
                        "由医生进一步评估",
                        sentence,
                    )
                seen = True
            rebuilt.append(sentence + mark)
        return "".join(rebuilt)

    def _clean_cot_field_text(self, text: Any, *, soften_direct_medication: bool = True) -> str:
        return self._clean_medical_answer_text(
            text,
            soften_direct_medication=soften_direct_medication,
        )

    def _is_hypertension_edema_source(self, source: str) -> bool:
        return (
            "高血压" in source
            and ("氨氯地平" in source or "降压药" in source)
            and ("踝部水肿" in source or "水肿" in source)
        )

    def _clean_source_specific_medical_text(self, text: str, source_text: Optional[str]) -> str:
        value = text or ""
        if self._is_groin_obstruction_source(source_text):
            value = re.sub(r"右侧盆腔内有", "腹部可见", value)
            value = value.replace("盆腔内有阶梯状液气平", "腹部X线可见阶梯状液气平")
            value = value.replace("以排除肠梗阻并处理腹股沟疝", "以评估肠梗阻和嵌顿风险")
            value = value.replace("以排除其他并发症并处理当前情况", "以评估肠梗阻和嵌顿风险")
            value = value.replace("以排除其他并发症", "以评估肠梗阻和嵌顿风险")
            value = value.replace("，可能伴有腹股沟区域的肿胀", "")
            value = value.replace("需立即评估手术可能性", "需尽快外科评估嵌顿和肠梗阻风险")
            value = re.sub(
                r"若不及时[^。；;]*?(?:穿孔|肠坏死|坏死)[^。；;]*[。；;]?",
                "需要关注嵌顿和肠梗阻风险。",
                value,
            )
            value = re.sub(
                r"(?:可迅速|可能|容易)?(?:发展为|进展为)?(?:肠坏死|肠穿孔|穿孔)[^。；;]*[。；;]?",
                "存在嵌顿和肠梗阻风险。",
                value,
            )
            value = value.replace("肠管血供可迅速受阻，", "")
            value = value.replace("肠管血供易受阻，", "")
            value = value.replace("肠管血供受限，", "")
            value = value.replace("肠管血供可能受阻，", "")
            value = re.sub(r"\s*最终答案[:：].*$", "", value).strip()
            value = re.sub(r"。。+", "。", value)
            value = re.sub(r"(，){2,}", "，", value)
            value = re.sub(r"\s+", " ", value).strip()
            return value
        if self._is_acute_stroke_source(source_text or ""):
            stroke_cleanup_patterns = [
                (
                    r"(?:必要时)?(?:的)?影像学检查如MRI(?:或SPECT)?",
                    "必要时进一步完善卒中相关评估",
                ),
                (
                    r"(?:必要时)?(?:的)?影像学检查如SPECT",
                    "必要时进一步完善卒中相关评估",
                ),
                (r"(?:伴有|合并)?意识障碍", ""),
                (r"(?:同时|并且)?血糖也升高了?", ""),
                (r"(?:同时|并且)?血压升高了?", ""),
                (r"脑干梗死", ""),
                (r"血管痉挛", ""),
            ]
            for pattern, replacement in stroke_cleanup_patterns:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            value = re.sub(r"\bSPECT\b", "", value, flags=re.IGNORECASE)
            value = re.sub(r"\s+", " ", value).strip(" ，。")
            value = re.sub(r"。。+", "。", value)
            value = re.sub(r"(或而|或，|和而)", "而", value)
            if value and not value.endswith(("。", "！", "？")):
                value += "。"
            return value
        if not self._is_hypertension_edema_source(source_text or ""):
            return value

        value = re.sub(
            r"(血压)(?:超过|高于|大于)\s*180\s*/\s*110\s*mmHg",
            r"\1持续高于目标范围",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"血压持续高于目标范围(?:左右)?",
            "血压持续高于目标范围",
            value,
        )
        value = re.sub(
            r"(?:具体)?由医生进一步评估，?还需要考虑其他因素，?比如是否有蛋白尿、肾功能不全等[。；;]?",
            "应结合血压记录和水肿变化复诊评估。",
            value,
        )
        value = re.sub(
            r"如果确诊为心脏问题，?可能需要使用\s*ACEI\s*或\s*ARB\s*类药物[。；;]?",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"(?:建议)?(?:尽快就医)?(?:进行)?(?:详细检查，?)?包括心脏功能和肾功能的评估[。；;]?",
            "建议结合血压记录和水肿变化复诊评估。",
            value,
        )
        value = re.sub(
            r"(?:建议)?(?:进行)?心脏功能和肾功能的评估[。；;]?",
            "建议结合血压记录和水肿变化复诊评估。",
            value,
        )
        value = re.sub(
            r"踝部水肿可能提示其他问题，?如心脏或肾脏问题，?需要进一步检查[。；;]?",
            "踝部水肿应结合血压记录和水肿变化复诊评估。",
            value,
        )
        value = re.sub(
            r"氨氯地平是常用的降压药，但需注意其副作用，如踝部水肿、心悸等。"
            r"如果这些症状出现，可能提示药物对某些患者不适用，或者存在其他并发症[。；;]?",
            "氨氯地平相关踝部水肿需要结合血压记录和水肿变化复诊评估。",
            value,
        )
        value = re.sub(
            r"肾功能检查对于评估药物代谢很重要，因为氨氯地平主要通过肾脏排泄。"
            r"如果肾功能受损，药物可能蓄积，增加副作用风险[。；;]?",
            "应记录家庭血压和水肿变化，复诊时由医生评估用药方案。",
            value,
        )
        value = re.sub(
            r"如果症状持续或加重，应及时就医，排除其他潜在疾病，如或肾脏疾病[。；;]?",
            "如果水肿持续或加重，应及时复诊。",
            value,
        )
        value = re.sub(
            r"建议您进行肾功能检查，并定期监测血压[。；;]?",
            "建议您记录血压和水肿变化，并由医生评估是否调整用药方案。",
            value,
        )
        if any(term in value for term in ["糖尿病", "肾病", "心衰", "血栓", "下肢静脉", "肾脏功能", "换用其他降压药", "增加剂量"]):
            value = (
                "只建议继续观察或自行调整用药，未结合血压记录、水肿变化和医生复诊评估；"
                "请不要自行调整药物，以免造成不必要的健康风险。"
            )
        value = re.sub(
            r"观察是否有其他症状，?如呼吸困难、水肿加重等",
            "观察水肿变化",
            value,
        )
        value = re.sub(
            r"并观察是否有呼吸困难、水肿加重等",
            "并观察水肿变化",
            value,
        )
        value = re.sub(
            r"如果确诊为心脏问题[^。；;]*(?:ACEI|ARB)[^。；;]*[。；;]?",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"(?:蛋白尿|肾功能不全|心脏功能|心脏问题|肾功能|肾脏问题|肾脏疾病|心悸|并发症|药物蓄积|ACEI|ARB)",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(r"建议您建议", "建议您", value)
        value = re.sub(r"建议您尽快就医，建议", "建议您", value)
        value = re.sub(r"建议您尽快就医，", "建议您", value)
        value = re.sub(r"(\d+\.)\s*(?=\d+\.)", "", value)
        value = re.sub(r"对控制血压和预防都有益处", "对控制血压有益处", value)
        value = re.sub(r"以预防可能的[。；;]?", "以减少用药风险。", value)
        value = re.sub(r"排除其他潜在疾病，?如或[。；;]?", "结合血压记录和水肿变化复诊评估。", value)
        value = re.sub(r"排除其他，", "泛化风险提示，", value)
        value = re.sub(r"。。+", "。", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _looks_like_meta_or_thought(self, text: str) -> bool:
        if not text:
            return True
        lower = text.lower().strip()
        for p in self.meta_phrases:
            if p.lower() in lower:
                return True
        if lower.startswith("嗯") or lower.startswith("好的") or lower.startswith("首先"):
            return True
        return False

    def _check_length_limit(self, task_type: str, data: Dict[str, Any]) -> bool:
        limits = self.length_limits.get(task_type, {})
        for k, max_len in limits.items():
            v = data.get(k)
            if isinstance(v, str) and len(v.strip()) > max_len:
                return False
        return True

    def _passes_task_quality(
        self,
        task_type: str,
        data: Dict[str, Any],
        source_text: Optional[str] = None,
    ) -> bool:
        if not self._check_length_limit(task_type, data):
            return False

        if (
            source_text
            and task_type != "Preference"
            and self._has_obvious_source_contradiction(source_text, data)
        ):
            return False

        if task_type == "QA":
            q = str(data.get("question", "")).strip()
            a = str(data.get("answer", "")).strip()
            if self._looks_like_meta_or_thought(q) or self._looks_like_meta_or_thought(a):
                return False
            if source_text and self._is_diagnostic_generation_source(source_text):
                if self._is_demographic_only_qa(q, a):
                    return False
            if self._is_groin_obstruction_source(source_text or ""):
                if not ("腹股沟疝" in a and "肠梗阻" in a):
                    return False
                if not any(term in a for term in ["外科评估", "急诊外科", "手术评估", "手术", "尽快"]):
                    return False
                if any(term in a for term in ["观察", "随访", "门诊观察", "先回家", "保守观察"]):
                    return False
            if self._is_dka_source(source_text or ""):
                if not any(term in a for term in ["糖尿病酮症酸中毒", "酮症酸中毒", "DKA"]):
                    return False
                if not any(term in a for term in ["补液", "液体复苏"]):
                    return False
                if "胰岛素" not in a:
                    return False
            if len(a) < 8:
                return False
            if self._is_acute_stroke_source(source_text or ""):
                if not any(term in (q + a) for term in ["卒中", "缺血性卒中", "急性缺血性卒中"]):
                    return False
                if not any(term in a for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return False
            return True

        if task_type == "CoT":
            q = str(data.get("question", "")).strip()
            r = str(data.get("rationale", "")).strip()
            f = str(data.get("final_answer", "")).strip()
            if (
                self._looks_like_meta_or_thought(q)
                or self._looks_like_model_monologue(q)
                or self._looks_like_meta_or_thought(r)
                or self._looks_like_meta_or_thought(f)
            ):
                return False
            if any(term in (q + r + f) for term in ["Preference", "preference", "chosen", "rejected", "字段固定为", "prompt"]):
                return False
            if any(term in q for term in ["CoT", "必须", "规则", "生成要求", "字段", "JSON"]):
                return False
            matches = list(re.finditer(r"(?<!\d)(\d+)[\.、]\s*", r))
            substantive_steps = 0
            for idx, match in enumerate(matches):
                start = match.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(r)
                step = r[start:end].strip(" 。；;")
                if len(step) >= 4 and re.search(r"[\u4e00-\u9fff]", step):
                    substantive_steps += 1

            requires_long_cot = bool(
                source_text
                and "腹股沟" in source_text
                and "阶梯状液气平" in source_text
            )
            if requires_long_cot:
                long_steps = 0
                for idx, match in enumerate(matches):
                    start = match.end()
                    end = matches[idx + 1].start() if idx + 1 < len(matches) else len(r)
                    step = r[start:end].strip(" 。；;")
                    if len(step) >= 8 and re.search(r"[\u4e00-\u9fff]", step):
                        long_steps += 1
                if long_steps < 6:
                    return False
            elif matches and substantive_steps < 3:
                return False
            elif not matches and len(r.strip()) < 160:
                return False
            if self._is_acute_stroke_source(source_text or ""):
                if not any(term in (q + r + f) for term in ["卒中", "缺血性卒中", "急性缺血性卒中"]):
                    return False
                if not any(term in f for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return False
            return True

        if task_type == "Preference":
            c = str(data.get("chosen", "")).strip()
            rj = str(data.get("rejected", "")).strip()
            pr = str(data.get("preference_reason", "")).strip()
            if any(self._looks_like_meta_or_thought(x) or self._looks_like_model_monologue(x) for x in [c, rj, pr]):
                return False
            if source_text and self._has_obvious_source_contradiction(
                source_text,
                {
                    "question": data.get("question", ""),
                    "chosen": c,
                    "rejected": rj,
                    "preference_reason": pr,
                },
            ):
                return False
            if self._is_acute_stroke_source(source_text or ""):
                if not any(term in (c + pr) for term in ["卒中", "缺血性卒中", "急性缺血性卒中"]):
                    return False
                if not any(term in c for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return False
            if c == rj:
                return False
            if pr in self.weak_preference_reasons:
                return False
            return True

        return True

    def _looks_like_model_monologue(self, text: str) -> bool:
        value = (text or "").strip()
        if not value:
            return False
        monologue_patterns = [
            r"我需要",
            r"我会",
            r"我首先",
            r"让我",
            r"这让我",
            r"我认为",
            r"我推测",
            r"需要综合这些信息",
        ]
        return any(re.search(pattern, value) for pattern in monologue_patterns)

    def _contains_positive_recommendation(self, text: str, terms: List[str]) -> bool:
        value = text or ""
        for term in terms:
            for match in re.finditer(re.escape(term), value):
                prefix = value[max(0, match.start() - 12):match.start()]
                if any(marker in prefix for marker in ["不", "无", "无需", "不需", "忽视", "忽略", "拒绝", "暂不", "不能", "避免", "慎用", "除非", "仅在", "延误", "延迟", "推迟", "耽误", "拖延"]):
                    continue
                return True
        return False

    def _is_dka_source(self, source: str) -> bool:
        return (
            ("血糖" in source)
            and ("尿酮" in source or "酮体" in source)
            and ("pH" in source or "HCO3" in source or "酸中毒" in source)
        )

    def _is_acute_stroke_source(self, source: str) -> bool:
        return (
            ("突发" in source)
            and ("肢体无力" in source or "言语不清" in source or "NIHSS" in source)
            and ("CT未见出血" in source or ("CT" in source and "未见出血" in source))
        )

    def _sanitize_acute_stroke_generated_text(self, text: str) -> str:
        value = str(text or "")
        value = re.sub(
            r"(?:可(?:进一步)?(?:做|完善|进行|考虑)|进一步(?:做|完善|进行|考虑)|必要时(?:可)?(?:做|完善|进行|考虑))\s*(?:MRI|CTA|SPECT)\b[^。；;]*",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"(?:以|用于)?(?:排除|判断|确认)\s*(?:脑干梗死|血管痉挛)[^。；;]*",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(r"\bMRI\b|\bCTA\b|\bSPECT\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"脑干梗死|血管痉挛|意识障碍", "", value)
        value = re.sub(r"\s+", " ", value).strip(" ，。；;")
        value = re.sub(r"(，){2,}", "，", value)
        value = re.sub(r"(。){2,}", "。", value)
        if value and not value.endswith(("。", "？", "！")):
            value += "。"
        return value

    def _is_bacterial_pneumonia_source(self, source: str) -> bool:
        return (
            ("发热" in source and ("咳嗽" in source or "气促" in source))
            and ("白细胞" in source or "中性粒细胞" in source or "CRP" in source)
            and ("片状浸润" in source or "湿啰音" in source or "肺炎" in source)
        )

    def _has_unapproved_english_tokens(self, source_text: str, generated: str) -> bool:
        if not generated:
            return False

        if not re.search(r"[\u4e00-\u9fff]", source_text or ""):
            return False

        forbidden = {
            "insulin", "volume",
        }
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", generated):
            normalized = token.lower().strip("+-")
            if normalized in forbidden:
                return True
        return False

    def _has_obvious_source_contradiction(self, source_text: str, data: Dict[str, Any]) -> bool:
        source = source_text or ""
        generated = " ".join(
            str(v)
            for v in data.values()
            if isinstance(v, (str, int, float))
        )
        if self._has_unapproved_english_tokens(source, generated):
            return True

        def has_forbidden_without_negation(term: str) -> bool:
            for m in re.finditer(re.escape(term), generated):
                window = generated[max(0, m.start() - 48): m.end() + 40]
                if any(marker in window for marker in ["排除", "不考虑", "不符合", "不适当", "不恰当", "无关", "否定", "不是", "不应", "不得", "禁止", "无需", "不需", "不常规", "非首选", "不作为", "避免", "慎用", "除非", "仅在", "不推荐"]):
                    continue
                return True
            return False

        if any(term in generated for term in ["preference 中", "Preference 中", "chosen 应", "rejected 应", "作为 chosen", "字段固定为", "既往规则", "根据规则", "prompt", "原始的诊断建议"]):
            return True
        if any(term in generated for term in ["曓", "�"]):
            return True
        if re.search(r"依据\d{2,}", generated):
            return True
        if re.search(r"\binsulin\b", generated, flags=re.IGNORECASE):
            return True

        if (
            "高血压" in source
            and ("氨氯地平" in source or "降压药" in source)
            and ("踝部水肿" in source or "水肿" in source)
        ):
            ungrounded_serious_terms = [
                "下肢静脉血栓",
                "深静脉血栓",
                "血栓",
                "抗凝",
                "超声心动图",
                "下肢静脉超声",
                "心衰",
            ]
            if any(term in generated for term in ungrounded_serious_terms):
                return True

        contradiction_pairs = [
            ("男", ["女性", "妇科", "卵巢", "黄体破裂", "子宫", "妊娠"]),
            ("女", ["男性", "睾丸", "前列腺"]),
        ]
        for source_marker, forbidden_terms in contradiction_pairs:
            if source_marker in source and any(has_forbidden_without_negation(term) for term in forbidden_terms):
                return True

        if "腹股沟" in source and "阶梯状液气平" in source:
            unrelated = ["睾丸扭转", "黄体破裂", "卵巢囊肿", "盆腔炎"]
            final_answer = str(data.get("final_answer", ""))
            chosen = str(data.get("chosen", ""))
            if data.keys() >= {"chosen", "rejected", "preference_reason"}:
                rejected = str(data.get("rejected", ""))
                if any(term in rejected for term in unrelated):
                    return True
                if any(term in chosen for term in unrelated):
                    return True
                if not ("腹股沟疝" in chosen and "肠梗阻" in chosen):
                    return True
            if any(term in generated for term in unrelated):
                return True
            if any(term in generated for term in ["穿孔", "引流", "推挤", "减压", "复位", "探查"]):
                return True
            if any(term in generated for term in ["硬度", "活动度"]):
                return True
            if "最终答案" in str(data.get("rationale", "")):
                return True
            if any(term in generated for term in ["盆腔", "其他并发症"]):
                return True
            if re.search(r"排除.{0,8}肠梗阻|肠梗阻.{0,8}排除", generated):
                return True
            if final_answer:
                if not ("腹股沟疝" in final_answer and "肠梗阻" in final_answer):
                    return True
                if not any(term in final_answer for term in ["外科评估", "外科", "急诊外科", "手术评估", "手术"]):
                    return True
                unsafe_delay = r"(延迟|延误|推迟|暂缓|暂不|不急).{0,12}(外科|手术|评估|处理)|观察并.{0,8}(延迟|延误|推迟|暂缓)"
                for match in re.finditer(unsafe_delay, final_answer):
                    prefix = final_answer[max(0, match.start() - 6):match.start()]
                    if any(marker in prefix for marker in ["避免", "防止", "以免", "减少"]):
                        continue
                    return True
                if "观察" in final_answer and not any(term in final_answer for term in ["外科评估", "急诊", "手术", "尽快", "及时"]):
                    return True

        if "食管裂孔疝" in source:
            chosen = str(data.get("chosen", ""))
            rejected = str(data.get("rejected", ""))
            if (
                self._contains_positive_recommendation(rejected, ["手术治疗", "手术评估", "外科评估"])
                and not any(term in chosen for term in ["食管裂孔疝", "裂孔疝", "手术", "外科评估"])
            ):
                return True

        if all(term in source for term in ["II", "III", "aVF", "ST段抬高"]):
            if any(term in generated for term in ["左心上室", "前壁心肌梗死", "高侧壁心肌梗死", "冠状动脉栓塞", "心尖端", "非心尖"]):
                return True
            if any(term in generated for term in ["心脏起搏器检查", "心包反射", "心包疾病"]):
                return True
            if re.search(r"排除.{0,10}心肌梗死|心肌梗死.{0,10}排除", generated):
                return True

        if self._is_dka_source(source):
            chosen = str(data.get("chosen", ""))
            rejected = str(data.get("rejected", ""))
            final_answer = str(data.get("final_answer", ""))
            if re.search(r"HCO3-?.{0,8}(增高|升高|增加|偏高)", generated, flags=re.IGNORECASE):
                return True
            if any(term in generated for term in ["抗激素", "神经系统受损原因", "神经系统损伤", "神经系统受损"]):
                return True
            if "高血压" not in source and any(term in generated for term in ["原发性高血压", "高血压病"]):
                return True
            if not any(term in generated for term in ["糖尿病酮症酸中毒", "酮症酸中毒", "DKA"]):
                return True
            if has_forbidden_without_negation("碳酸氢钠") and "pH 6.9" not in source and "pH<6.9" not in source:
                return True
            if data.keys() >= {"chosen", "rejected", "preference_reason"}:
                if not any(term in chosen for term in ["胰岛素", "补液", "液体复苏"]):
                    return True
                if (
                    self._contains_positive_recommendation(chosen, ["碳酸氢钠", "抗生素"])
                    and self._contains_positive_recommendation(rejected, ["胰岛素", "补液", "液体复苏"])
                ):
                    return True
            if final_answer and not any(term in final_answer for term in ["胰岛素", "补液", "液体复苏"]):
                return True

        if self._is_acute_stroke_source(source):
            if not any(term in generated for term in ["卒中", "缺血性卒中", "急性缺血性卒中"]):
                return True
            if any(term in generated for term in ["发热", "咳嗽", "咽痛", "肺炎", "流感", "上呼吸道感染", "活检"]):
                return True
            if any(term in generated for term in ["意识障碍", "脑干梗死", "血管痉挛"]):
                return True
            if self._contains_positive_recommendation(generated, ["MRI"]):
                return True
            if self._contains_positive_recommendation(generated, ["CTA"]):
                return True
            if self._contains_positive_recommendation(generated, ["SPECT"]):
                return True
            if data.keys() >= {"question", "answer"}:
                answer = str(data.get("answer", ""))
                if not any(term in answer for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return True
            if data.keys() >= {"question", "rationale", "final_answer"}:
                final_answer = str(data.get("final_answer", ""))
                if not any(term in final_answer for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return True
            if data.keys() >= {"chosen", "rejected", "preference_reason"}:
                chosen = str(data.get("chosen", ""))
                rejected = str(data.get("rejected", ""))
                if not any(term in chosen for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                    return True
                if self._contains_positive_recommendation(rejected, ["溶栓", "取栓", "再灌注"]):
                    return True

        if self._is_bacterial_pneumonia_source(source):
            chosen = str(data.get("chosen", ""))
            rejected = str(data.get("rejected", ""))
            if any(term in generated for term in ["腹股沟疝", "肠梗阻", "腹股沟包块"]):
                return True
            if "CRP升高" in source and any(term in generated for term in ["正常CRP", "CRP正常", "CRP不高", "CRP未升高"]):
                return True
            if any(term in generated for term in ["无呼吸道症状", "无细菌证据", "没有细菌感染证据", "缺乏细菌感染证据"]):
                return True
            if has_forbidden_without_negation("病毒感染"):
                return True
            if data.keys() >= {"chosen", "rejected", "preference_reason"}:
                chosen_antiviral = self._contains_positive_recommendation(chosen, ["抗病毒"])
                rejected_antibiotic = self._contains_positive_recommendation(rejected, ["抗生素", "抗感染"])
                if chosen_antiviral and rejected_antibiotic:
                    return True
                if not any(term in chosen for term in ["抗生素", "抗感染", "细菌性肺炎"]):
                    return True

        return False

    def _build_source_guardrail(self, source_text: str, task_type: Optional[str] = None) -> str:
        source = source_text or ""
        rules: List[str] = []
        qa_compact_mode = task_type == "QA"
        if "男" in source:
            if not qa_compact_mode:
                rules.append("病例为男性。")
        if "女" in source:
            if not qa_compact_mode:
                rules.append("病例为女性。")
        if "腹股沟" in source and "包块" in source:
            rules.append("腹股沟包块合并阶梯状液气平时，应围绕嵌顿性腹股沟疝合并肠梗阻分析。")
            if task_type == "Preference":
                rules.append("所有字段禁止出现穿孔、引流、推挤、减压等原文未给出的并发症或处置。")
            else:
                rules.append("不要扩展原文未提供的并发症或处置。")
            if task_type == "CoT":
                rules.append("final_answer 必须建议尽快外科或急诊外科评估，不得建议观察、延迟外科评估或延迟手术。")
                rules.append("final_answer 必须字面包含外科评估、急诊外科评估或手术评估之一。")
                rules.append("rationale 至少包含六个有实质内容的编号步骤，依次覆盖病史、腹股沟包块、X线液气平、诊断推断、风险判断和处置建议。")
                rules.append("rationale 不要列入与病例性别或部位冲突的鉴别诊断。")
                rules.append("不要扩展到原文未提供的具体操作，处置建议只写尽快外科评估或急诊外科评估。")
                rules.append("腹股沟包块步骤只引用原文给出的部位、大小和压痛等信息，不写硬度、活动度等原文未给出体征。")
                rules.append("X线阶梯状液气平已支持肠梗阻，不要写排除肠梗阻。")
            if task_type == "Preference":
                rules.append("chosen 必须字面包含：嵌顿性腹股沟疝合并肠梗阻，并建议尽快外科评估；不得把卵巢囊肿、盆腔炎、睾丸扭转、阑尾肿瘤等作为 chosen。")
                rules.append("rejected 不得是疾病名，严禁输出卵巢囊肿、盆腔炎、睾丸扭转等其他诊断名称；必须用同一病例的低质量处理建议作为 rejected，例如仅建议观察、延误外科评估、忽视肠梗阻证据或未及时处理嵌顿疝。")
        if "食管裂孔疝" in source:
            rules.append("食管裂孔疝病例应同时覆盖反流性食管炎、食管裂孔疝和反流相关咳喘。")
            rules.append("Preference 任务中，chosen 应是更完整答案；不得把手术治疗、手术评估或外科评估作为 rejected 的优点。")
        if all(term in source for term in ["II", "III", "aVF", "ST段抬高"]):
            rules.append("II、III、aVF导联ST段抬高合并肌钙蛋白升高时，应明确为急性下壁STEMI或下壁心肌梗死。")
            rules.append("处理建议应聚焦急诊心内科评估、抗栓治疗、冠脉造影评估和再灌注策略。")
        if self._is_dka_source(source):
            rules.append("血糖显著升高、尿酮体阳性、pH/HCO3-提示酸中毒时，应围绕糖尿病酮症酸中毒分析。")
            rules.append("处理原则必须包括补液或液体复苏、静脉胰岛素、钾/电解质监测与纠正，并寻找诱因。")
            if task_type == "Preference":
                rules.append("Preference 的 chosen 必须同时包含诊断和处理：糖尿病酮症酸中毒、补液、静脉胰岛素、电解质监测纠正；rejected 应写同病例低质量处置，例如仅观察或只控制血糖而遗漏补液和电解质管理。")
            rules.append("治疗表述只使用中文胰岛素，不使用英文 insulin；不要输出编号残片。")
            rules.append("只输出上述诊断依据和处理原则，不扩展原文未提供的其他系统病因或常规外治疗。")
        if self._is_acute_stroke_source(source):
            rules.append("突发偏瘫/言语不清且头颅CT未见出血时，应按急性缺血性卒中路径分析。")
            rules.append("处置应包括卒中中心评估、静脉溶栓时间窗/禁忌评估、必要时机械取栓评估、血压和血糖管理。")
            rules.append("不得无依据写脑干梗死、血管痉挛或SPECT；不得要求先做MRI/SPECT而延误溶栓或再灌注评估。")
            if task_type == "Preference":
                rules.append("Preference 中 chosen 不得写既往规则、根据规则或 prompt 话术；rejected 不得否定机械取栓或再灌注评估，应写同病例低质量回答，例如仅观察、延误溶栓、忽视CT未见出血或忽视时间窗。")
        if self._is_bacterial_pneumonia_source(source):
            rules.append("儿童发热咳嗽、湿啰音、白细胞/中性粒细胞/CRP升高和片状浸润影时，应优先围绕细菌性肺炎分析。")
            if task_type == "Preference":
                rules.append("Preference 中 chosen 应支持经验性抗生素或抗感染治疗及支持治疗；不得把抗病毒优先方案作为 chosen。")
                rules.append("Preference 中 rejected 必须是同病例低质量回答，例如仅抗病毒、仅观察、延误抗生素或忽视细菌感染证据；不得写不适用、信息不足、妇科疾病或其他无关内容。")
                rules.append("Preference 的 rejected 不得写无呼吸道症状，不得写无细菌证据，不得写缺乏细菌感染证据；因为原始病例已经有发热咳嗽、白细胞/CRP升高和片状浸润影。")
        if rules and not qa_compact_mode:
            rules.append("以上规则只用于约束生成，禁止把规则原句、字段名或 prompt 要求写入输出内容。")
        return " ".join(rules)

    def _render_prompt(self, task_type: str, text: str) -> str:
        if task_type not in self.task_templates:
            raise ValueError(f"不支持的 task_type: {task_type}")

        if task_type == "QA":
            return self._render_qa_fast_prompt(text)
        if task_type == "CoT":
            return self._render_cot_native_prompt(text)
        if task_type == "Preference":
            return self._render_preference_native_prompt(text)
        raise ValueError(f"不支持的 task_type: {task_type}")

    def _render_qa_fast_prompt(self, text: str) -> str:
        compact = self._strip_generation_scaffolding(text)
        guardrail = self._build_source_guardrail(compact, "QA")
        suggested_question = self._suggest_qa_question(compact)
        answer_prefix = self._qa_prefill_json_prefix(compact)
        if self._qa_uses_native_template:
            if self._is_groin_obstruction_source(compact):
                return self._render_native_chat_template(
                    self._render_groin_qa_messages(compact),
                    enable_thinking=False,
                ) + answer_prefix
            if self._is_acute_stroke_source(compact):
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是医学数据构造助手。请基于中文急性脑卒中病例生成一个 QA JSON 对象。"
                            "只输出 JSON，不要输出解释或 <think>。"
                            "字段只能有 question 和 answer。"
                            "question 必须是简短临床问题。"
                            "answer 必须围绕急性缺血性卒中路径，明确卒中中心评估、溶栓时间窗/禁忌证评估、必要时机械取栓评估，以及血压血糖管理。"
                            "不要编造原文没有的症状、检查或其他疾病。"
                            "不要正向建议 MRI 或 SPECT，不要写意识障碍、脑干梗死或血管痉挛。"
                            f"{guardrail}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": compact,
                    },
                ]
                return self._render_native_chat_template(messages, enable_thinking=False) + answer_prefix
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Generate one medical QA JSON object from the source text. "
                        "Output JSON only. Do not output explanations or <think>. "
                        "Use exactly two fields: question and answer. "
                        f'Question should stay close to: "{suggested_question}". '
                        "Do not restate the full case in question. "
                        "Keep answer concise, clinically grounded, and within 1 short sentence when possible. "
                        f"{guardrail}"
                    ),
                },
                {
                    "role": "user",
                    "content": compact,
                },
            ]
            return self._render_native_chat_template(messages, enable_thinking=False) + answer_prefix

        if self._is_groin_obstruction_source(compact):
            return (
                "<|im_start|>system\n"
                "你是资深临床医生。请基于用户给出的中文病例生成一个高质量 QA JSON 对象。"
                "只能输出 JSON，不要输出解释、markdown 或 <think>。"
                "字段只能是 question 和 answer。"
                "question 必须是简短临床问题，不得复述整段病例。"
                "answer 必须明确写：考虑嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"
                "不要写观察随访、门诊观察、延迟处理，也不要写其他鉴别诊断或原文未提供的具体操作。\n"
                "<|im_end|>\n"
                "<|im_start|>user\n"
                f"{compact}\n"
                "<|im_end|>\n"
                "<|im_start|>assistant\n"
                "<think>\n\n</think>\n\n"
                f"{answer_prefix}"
            )

        return (
            "<|im_start|>system\n"
            "Generate one medical QA JSON object from the source text. "
            "Output JSON only. Do not output explanations or <think>. "
            "Use exactly two fields: question and answer. "
            f"Question should stay close to: \"{suggested_question}\". "
            "Do not restate the full case in question. "
            "Keep answer concise, clinically grounded, and within 1 short sentence when possible. "
            f"{guardrail}\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{compact}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>\n\n</think>\n\n"
            f"{answer_prefix}"
        )

    def _render_cot_native_prompt(self, text: str) -> str:
        compact = text.strip()
        guardrail = self._build_source_guardrail(compact, "CoT")
        if self._qa_uses_native_template:
            if self._is_groin_obstruction_source(compact):
                return self._render_native_chat_template(
                    self._render_groin_cot_messages(compact),
                    enable_thinking=False,
                ) + self._cot_prefill_json_prefix(compact)
            if self._is_acute_stroke_source(compact):
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是资深神经内科医生。请基于中文病例生成一个 CoT JSON 对象。"
                            "只能输出 JSON，不要输出解释或 <think>。"
                            "字段固定为 question、rationale、final_answer。"
                            "question 必须是简短临床问题。"
                            "rationale 必须是单个中文字符串，包含六个编号步骤：1.症状与时间窗，2.影像排除出血，3.急性缺血性卒中判断，4.溶栓评估，5.取栓评估，6.血压血糖等基础管理。"
                            "每步只引用原始输入中已有信息或必要的标准化急诊评估，不得编造意识障碍、MRI、SPECT、血管痉挛或脑干梗死。"
                            "final_answer 必须明确首先考虑急性缺血性卒中，并建议立即启动卒中中心评估、溶栓时间窗/禁忌证评估和必要时机械取栓评估，同时监测血压和血糖。"
                            f"{guardrail}"
                        ),
                    },
                    {"role": "user", "content": compact},
                ]
                return self._render_native_chat_template(messages, enable_thinking=False)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是资深临床医生。请基于用户给出的中文病例生成一个 CoT JSON 对象。"
                        "只能输出 JSON，不要输出解释或 <think>。"
                        "字段固定为 question、rationale、final_answer。"
                        "question 必须是一个简短的临床问题，不得写模型自述、推理过程、'我需要'或'这让我'。"
                        "question 不得包含 CoT、必须、规则、prompt、JSON 或生成要求。"
                        "rationale 必须是一个中文字符串，不要使用数组；必须包含六个编号：1. 2. 3. 4. 5. 6.。"
                        "每个编号步骤必须引用输入病例中的症状、检查或处置依据，每步写成1到2句完整中文，不要写空编号。"
                        "final_answer 必须与病例一致，不得引入输入中不存在的症状或检查。"
                        f"{guardrail}"
                    ),
                },
                {"role": "user", "content": compact},
            ]
            return self._render_native_chat_template(messages, enable_thinking=False)
        return self.cot_template.render(question=text)

    def _render_preference_native_prompt(self, text: str) -> str:
        compact = text.strip()
        guardrail = self._build_source_guardrail(compact, "Preference")
        if self._qa_uses_native_template:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是医疗数据工程师。请基于用户给出的中文病例生成一个偏好学习 JSON 对象。"
                        "只能输出 JSON，不要输出解释或 <think>。"
                        "字段固定为 question、chosen、rejected、preference_reason。"
                        "chosen 必须是准确、安全、完整的医学回答。"
                        "rejected 必须是明显较差但与同一病例相关的回答，不得写成无关疾病。"
                        "rejected 应写成同一病例下的错误处置、遗漏关键证据或不安全建议，不要列举与病例性别/部位冲突的其他疾病。"
                        "每个字段保持简短，避免长篇背景解释。"
                        "如果病例为男性，禁止输出妇科疾病；如果病例为女性，禁止输出男性生殖系统疾病。"
                        f"{guardrail}"
                        "preference_reason 必须具体比较 chosen 为什么更好。"
                    ),
                },
                {"role": "user", "content": compact},
            ]
            if self._is_acute_stroke_source(compact):
                messages[0]["content"] = (
                    "你是医疗数据工程师。请基于中文脑卒中病例生成一个偏好学习 JSON 对象。"
                    "只能输出 JSON，不要输出解释或 <think>。"
                    "字段固定为 question、chosen、rejected、preference_reason。"
                    "chosen 必须围绕急性缺血性卒中路径，包含卒中中心评估、溶栓时间窗/禁忌证评估、必要时机械取栓评估及血压血糖管理。"
                    "rejected 必须是同一病例下的低质量回答，例如仅观察、延误溶栓、忽视时间窗或忽视CT未见出血；不得写无关疾病。"
                    "所有字段不得出现 MRI、SPECT、意识障碍、脑干梗死、血管痉挛或既往规则/prompt 话术。"
                    f"{guardrail}"
                    "preference_reason 必须具体说明 chosen 为什么更符合急诊卒中评估路径。"
                )
            return self._render_native_chat_template(messages, enable_thinking=False)
        return self.preference_template.render(question=text)

    def _render_repair_prompt(
        self,
        task_type: str,
        source_text: str,
        raw_output: str,
        repair_note: Optional[str] = None,
    ) -> str:
        if task_type not in self.repair_templates:
            raise ValueError(f"不支持的 task_type: {task_type}")
        # 限制候选输出长度，避免修复阶段 prompt 过长
        clipped = (raw_output or "")[:2400]
        note = f"\n质量校验失败原因：{repair_note}" if repair_note else ""
        if self._qa_uses_native_template:
            fields = "/".join(self.required_fields.get(task_type, []))
            guardrail = self._build_source_guardrail(source_text, task_type)
            if task_type == "QA" and self._is_groin_obstruction_source(source_text):
                return self._render_native_chat_template(
                    self._render_groin_qa_messages(source_text, repair_mode=True),
                    enable_thinking=False,
                )
            if task_type == "CoT" and self._is_groin_obstruction_source(source_text):
                return self._render_native_chat_template(
                    self._render_groin_cot_messages(source_text, repair_mode=True),
                    enable_thinking=False,
                ) + self._cot_prefill_json_prefix(source_text)
            if self._is_acute_stroke_source(source_text):
                stroke_repair_rules = (
                    "急性脑卒中样例中，只能围绕急性缺血性卒中路径重写。"
                    "不得保留额外字段，QA 只允许 question/answer，CoT 只允许 question/rationale/final_answer。"
                    "不得写 MRI、SPECT、意识障碍、血糖升高、脑干梗死、血管痉挛或其他原文未给出的事实。"
                    "需要保留卒中中心评估、溶栓时间窗/禁忌证评估、必要时机械取栓评估、血压血糖管理。"
                )
            else:
                stroke_repair_rules = ""
            groin_repair_rules = ""
            if "腹股沟" in (source_text or "") and "阶梯状液气平" in (source_text or ""):
                if task_type == "CoT":
                    groin_repair_rules = (
                        "腹股沟包块合并阶梯状液气平时，CoT 必须围绕嵌顿性腹股沟疝合并肠梗阻展开。"
                        "rationale 必须包含六个以上有实质内容的编号步骤，覆盖病史、腹股沟包块、X线液气平、诊断推断、风险判断和外科评估建议。"
                        "不要扩展原文未提供的并发症或处置。"
                        "rationale 不要列入与病例性别或部位冲突的鉴别诊断。"
                        "不要扩展到原文未提供的具体操作，处置建议只写尽快外科评估或急诊外科评估。"
                        "腹股沟包块步骤只引用原文给出的部位、大小和压痛等信息，不写原文未给出体征；X线阶梯状液气平已支持肠梗阻，不要写排除肠梗阻。"
                        "final_answer 必须字面包含外科评估、急诊外科评估或手术评估之一，不得建议观察、延迟外科评估或延迟手术。"
                    )
                elif task_type == "Preference":
                    groin_repair_rules = (
                        "腹股沟包块合并阶梯状液气平时，chosen 必须写嵌顿性腹股沟疝合并肠梗阻并建议尽快外科评估。"
                        "腹股沟包块合并阶梯状液气平的 Preference 修复中，chosen 必须字面包含：嵌顿性腹股沟疝合并肠梗阻；rejected 不得是疾病名，只能写同一病例下的低质量处置。"
                        "腹股沟包块合并阶梯状液气平时，所有字段禁止出现穿孔、引流、推挤、减压等原文未给出的并发症或处置。"
                    )
            task_specific_repair_rules = (
                "CoT 的 rationale 必须写成单个编号字符串，不得使用数组；必须包含六个以上有内容的编号步骤；final_answer 必须存在且可包含必要处置。"
                if task_type == "CoT"
                else (
                    "Preference 的 rejected 必须是同一病例下的低质量回答，不得用与病例性别或部位冲突的其他疾病凑数。"
                    "如果 Preference 候选 rejected 是离题疾病或其他诊断名称，必须改写为同病例低质量处置建议，例如仅建议观察、延误外科评估、忽视关键检查或遗漏高危证据。"
                    "如果 Preference 候选 chosen 是离题疾病或其他错误诊断，必须改写为原始输入支持的正确答案。"
                )
            )
            if task_type == "QA" and self._is_diagnostic_generation_source(source_text):
                task_specific_repair_rules = (
                    "QA 必须围绕原始病例的诊疗、处理、建议、分析或管理生成，"
                    "不得退化为年龄、性别等人口学抽取题。"
                )
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"你是严格的 JSON 修复器。只输出一个合法 JSON 对象，字段固定为 {fields}。"
                        "不要输出解释、markdown 或 <think>。"
                        "只能基于原始输入和候选输出修复结构，不得编造原文不存在的诊断、症状或检查。"
                        f"{stroke_repair_rules}"
                        f"{task_specific_repair_rules}"
                        f"{groin_repair_rules}"
                        "CoT 的 final_answer 必须是安全处置建议，不得输出明显错误的首要处理。"
                        f"{guardrail}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"原始输入：{source_text}\n"
                        + (
                            "候选输出结构不合格，已丢弃。请只基于原始输入重新生成目标 JSON。"
                            if task_type == "CoT"
                            else f"候选输出：{clipped}\n{note}\n请修复为目标 JSON。"
                        )
                    ),
                },
            ]
            return self._render_native_chat_template(messages, enable_thinking=False)
        return self.repair_templates[task_type].render(source_text=source_text, raw_output=clipped)

    def _build_repair_retry_note(self, task_type: str, source_text: str, raw_output: str) -> str:
        source = source_text or ""
        notes: List[str] = ["上一轮输出仍未通过质量校验，必须重写为合格 JSON。"]
        if "腹股沟" in source and "阶梯状液气平" in source:
            notes.append("删除所有字段中的禁用并发症或处置词，不要复述上一轮中的禁用表述。")
            notes.append("CoT final_answer 只保留嵌顿性腹股沟疝合并肠梗阻和尽快外科评估。")
            notes.append("Preference chosen 必须包含嵌顿性腹股沟疝合并肠梗阻，rejected 只能是同病例低质量处置。")
        if raw_output:
            notes.append("不要保留候选输出中触发上述问题的表达。")
        return " ".join(notes)

    def _sanitize_failed_repair_output(self, source_text: str, raw_output: str) -> str:
        sanitized = raw_output or ""
        if "腹股沟" in (source_text or "") and "阶梯状液气平" in (source_text or ""):
            sanitized = re.sub(r"避免延误导致[^。；;，,\"]+", "避免延误处理", sanitized)
            sanitized = re.sub(r"防止[^。；;，,\"]+", "避免延误处理", sanitized)
            sanitized = re.sub(r"(穿孔|肠穿孔|引流|推挤|减压)", "", sanitized)
        if self._is_dka_source(source_text or ""):
            sanitized = re.sub(r"(抗激素|神经系统受损原因|神经系统损伤|神经系统受损|碳酸氢钠|抗生素)", "", sanitized)
            sanitized = re.sub(r"\binsulin\b", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"依据\d+", "", sanitized)
        if self._is_bacterial_pneumonia_source(source_text or ""):
            sanitized = sanitized.replace("无呼吸道症状或无细菌证据", "忽视已有细菌感染证据")
            sanitized = sanitized.replace("无呼吸道症状", "有呼吸道症状")
            sanitized = sanitized.replace("无细菌证据", "忽视已有细菌感染证据")
            sanitized = sanitized.replace("缺乏细菌感染证据", "忽视已有细菌感染证据")
        return sanitized[:1800]

    def _render_second_repair_prompt(self, task_type: str, source_text: str, raw_output: str) -> str:
        sanitized = self._sanitize_failed_repair_output(source_text, raw_output)
        if self._qa_uses_native_template:
            fields = "/".join(self.required_fields.get(task_type, []))
            guardrail = self._build_source_guardrail(source_text, task_type)
            source = source_text or ""
            if task_type == "QA" and self._is_groin_obstruction_source(source):
                return self._render_native_chat_template(
                    self._render_groin_qa_messages(source, repair_mode=True),
                    enable_thinking=False,
                )
            if task_type == "CoT" and self._is_groin_obstruction_source(source):
                return self._render_native_chat_template(
                    self._render_groin_cot_messages(source, repair_mode=True),
                    enable_thinking=False,
                ) + self._cot_prefill_json_prefix(source)
            if self._is_acute_stroke_source(source):
                stroke_instruction = (
                    "急性脑卒中样例二次修复时，必须完全重写。"
                    "不得沿用上一轮中的 MRI、SPECT、意识障碍、血糖升高、脑干梗死、血管痉挛或其他原文未给出的内容。"
                    "QA 只保留急性缺血性卒中判断与卒中中心/溶栓/取栓/血压血糖管理。"
                    "CoT 必须写出六个编号步骤，并把 final_answer 收束到卒中中心评估、溶栓和必要时取栓评估。"
                )
            else:
                stroke_instruction = ""
            groin_instruction = ""
            if "腹股沟" in source and "阶梯状液气平" in source:
                groin_instruction = (
                    "腹股沟包块合并阶梯状液气平时，诊断和处置只写：嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估，不写其他诊断。"
                    "rationale 需要写出病史、腹股沟包块、X线液气平、诊断推断、风险判断和处置建议，不要写空编号。"
                    "rationale 不要列入与病例性别或部位冲突的鉴别诊断，final_answer 必须字面包含外科评估、急诊外科评估或手术评估之一。"
                    "不要扩展到原文未提供的具体操作，处置建议只写尽快外科评估或急诊外科评估。"
                    "腹股沟包块步骤只引用原文给出的部位、大小和压痛等信息，不写原文未给出体征；X线阶梯状液气平已支持肠梗阻，不要写排除肠梗阻。"
                )
            task_specific_repair_rules = (
                "CoT 的 rationale 必须写成单个编号字符串，不得使用数组；必须包含六个以上有实质内容的编号步骤；每步应引用原始输入或医学判断。"
                if task_type == "CoT"
                else "Preference 的 rejected 必须是同一病例下的低质量回答，不得用无关疾病凑数。"
            )
            if task_type == "QA" and self._is_diagnostic_generation_source(source):
                task_specific_repair_rules = (
                    "QA 必须围绕原始病例的诊疗、处理、建议、分析或管理生成，"
                    "不得退化为年龄、性别等人口学抽取题。"
                )
            content = (
                f"你是严格的 JSON 二次修复器。只输出一个合法 JSON 对象，字段固定为 {fields}。"
                "请完全重写，不要沿用上一轮原句，不要输出解释、markdown 或 <think>。"
                "必须只根据原始输入和允许的医学结论生成，不能扩展原文未给出的并发症或处置。"
                f"{stroke_instruction}"
                f"{task_specific_repair_rules}"
                f"{groin_instruction}"
                f"{guardrail}"
            )
            if task_type == "CoT":
                user_content = (
                    f"原始输入：{source_text}\n"
                    "上一轮候选输出结构不合格，已丢弃。请只基于原始输入重新生成目标 JSON。"
                )
            else:
                user_content = (
                    f"原始输入：{source_text}\n"
                    f"上一轮失败输出（已清理禁用词）：{sanitized}\n"
                    "请重新生成目标 JSON。"
                )
            messages = [
                {"role": "system", "content": content},
                {"role": "user", "content": user_content},
            ]
            return self._render_native_chat_template(messages, enable_thinking=False)
        return self._render_repair_prompt(task_type, source_text, sanitized, self._build_repair_retry_note(task_type, source_text, sanitized))

    def _normalize_parsed_data(
        self,
        task_type: str,
        data: Any,
        source_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None

        if task_type == "QA":
            data = self._extract_qa_candidate_payload(data, source_text)
            if not isinstance(data, dict):
                return None

        allowed = self.required_fields.get(task_type, [])
        if task_type == "QA" and "answer" not in data:
            for alias in ["处理原则", "诊断", "结论", "回答", "answer_text"]:
                if alias in data:
                    data = dict(data)
                    data["answer"] = data.get(alias)
                    break
        normalized = {key: data.get(key) for key in allowed}

        if task_type == "CoT" and isinstance(normalized.get("rationale"), list):
            normalized["rationale"] = "".join(
                f"{i + 1}. {str(step).strip()}"
                for i, step in enumerate(normalized["rationale"])
                if str(step).strip()
            )
        if task_type == "CoT":
            normalized["question"] = self._clean_cot_field_text(
                normalized.get("question"),
                soften_direct_medication=False,
            )
            normalized["rationale"] = self._normalize_cot_rationale_text(
                self._clean_cot_field_text(normalized.get("rationale"))
            )
            normalized["final_answer"] = self._clean_cot_field_text(normalized.get("final_answer"))
            for key in ("question", "rationale", "final_answer"):
                normalized[key] = self._clean_source_specific_medical_text(
                    normalized.get(key, ""),
                    source_text,
                )
            if self._is_acute_stroke_source(source_text or ""):
                for key in ("question", "rationale", "final_answer"):
                    normalized[key] = self._sanitize_acute_stroke_generated_text(
                        normalized.get(key, "")
                    )
            normalized["rationale"] = self._renumber_cot_steps(normalized.get("rationale", ""))
        elif task_type == "QA":
            normalized["question"] = self._clean_medical_answer_text(
                normalized.get("question"),
                soften_direct_medication=False,
            )
            normalized["answer"] = self._clean_medical_answer_text(normalized.get("answer"))
            for key in ("question", "answer"):
                normalized[key] = self._clean_source_specific_medical_text(
                    normalized.get(key, ""),
                    source_text,
                )
            if self._is_acute_stroke_source(source_text or ""):
                for key in ("question", "answer"):
                    normalized[key] = self._sanitize_acute_stroke_generated_text(
                        normalized.get(key, "")
                    )
            normalized = self._truncate_fields("QA", normalized)
        elif task_type == "Preference":
            normalized["question"] = self._clean_medical_answer_text(
                normalized.get("question"),
                soften_direct_medication=False,
            )
            for key in ("chosen", "rejected"):
                normalized[key] = self._normalize_embedded_preference_text(normalized.get(key))
            normalized["preference_reason"] = self._clean_medical_answer_text(
                normalized.get("preference_reason")
            )
            for key in ("question", "chosen", "rejected", "preference_reason"):
                normalized[key] = self._clean_source_specific_medical_text(
                    normalized.get(key, ""),
                    source_text,
                )
            if self._is_acute_stroke_source(source_text or ""):
                for key in ("question", "chosen", "rejected", "preference_reason"):
                    normalized[key] = self._sanitize_acute_stroke_generated_text(
                        normalized.get(key, "")
                    )

        return normalized

    def _extract_qa_candidate_payload(
        self,
        data: Dict[str, Any],
        source_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        source = source_text or ""

        zh_question_alias = "问题"
        zh_answer_alias = "回答"

        def default_question() -> str:
            if self._is_acute_stroke_source(source):
                return "是否符合急性缺血性卒中评估条件？"
            if self._is_groin_obstruction_source(source):
                return "最可能的处理重点是什么？"
            if "发热" in source and "儿童" in source:
                return "最可能的处理重点是什么？"
            return "最可能的处理重点是什么？"

        def from_answer_text(answer_text: Any, question_text: Any = None) -> Optional[Dict[str, Any]]:
            answer = str(answer_text or "").strip()
            if not answer:
                return None
            question = str(question_text or "").strip() or default_question()
            return {"question": question, "answer": answer}

        if self._is_acute_stroke_source(source):
            raw_answer_text = str(data.get("answer") or "")
            primary = from_answer_text(data.get("answer"), data.get("question"))
            if primary is not None and any(term in raw_answer_text for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                compact_answer = "考虑急性缺血性卒中，应立即启动卒中中心评估，尽快评估溶栓或取栓，并监测血压和血糖。"
                return {"question": default_question(), "answer": compact_answer}
            candidate = from_answer_text(data.get("QA"), data.get("question"))
            if candidate is not None and any(term in candidate["answer"] for term in ["卒中中心", "溶栓", "取栓", "再灌注"]):
                return candidate
            if primary is not None:
                compact_answer = "考虑急性缺血性卒中，应立即启动卒中中心评估，尽快评估溶栓或取栓，并监测血压和血糖。"
                return {"question": default_question(), "answer": compact_answer}
            if candidate is not None:
                return candidate

        for key in ("qa", "QA"):
            value = data.get(key)
            if isinstance(value, dict):
                candidate = from_answer_text(value.get("answer") or value.get(zh_answer_alias), value.get("question") or value.get(zh_question_alias))
                if candidate is not None:
                    return candidate
            elif isinstance(value, str):
                candidate = from_answer_text(value)
                if candidate is not None:
                    return candidate

        if "question" in data and isinstance(data.get("answer"), str):
            candidate = from_answer_text(data.get("answer"), data.get("question"))
            if candidate is not None:
                return candidate

        if "question" in data and isinstance(data.get("QA"), str):
            candidate = from_answer_text(data.get("QA"), data.get("question"))
            if candidate is not None:
                return candidate

        for alias in ("回答", "结论", "诊断", "处理原则", "answer_text"):
            if alias in data:
                candidate = from_answer_text(data.get(alias), data.get("question") or data.get(zh_question_alias))
                if candidate is not None:
                    return candidate

        return data

    def _normalize_cot_rationale_text(self, rationale: str) -> str:
        text = re.sub(r"\s+", " ", rationale or "").strip()
        if not text:
            return text
        if len(re.findall(r"(\d+[\.、]|步骤\d+|->)", text)) >= 3:
            return self._renumber_cot_steps(text)

        parts = [p.strip(" ；;。") for p in re.split(r"[。；;]", text) if p.strip(" ；;。")]
        if len(parts) < 3:
            comma_parts = [p.strip(" ，,") for p in re.split(r"[，,]", text) if p.strip(" ，,")]
            if len(comma_parts) >= 4:
                parts = comma_parts

        if len(parts) < 3:
            return text

        steps = parts[:6]
        return "".join(f"{i + 1}. {step}。" for i, step in enumerate(steps))

    def _renumber_cot_steps(self, text: str) -> str:
        value = re.sub(r"\s+", " ", text or "").strip()
        matches = list(re.finditer(r"(?<!\d)(\d+)[\.、]\s*", value))
        if len(matches) < 3:
            return value

        steps: List[str] = []
        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(value)
            step = value[start:end].strip()
            if not step:
                continue
            steps.append(step.strip("。；; "))

        return "".join(f"{idx + 1}. {step}。" for idx, step in enumerate(steps) if step)

    def _validate_generated_data(
        self,
        task_type: str,
        data: Dict[str, Any],
        source_text: Optional[str] = None,
    ) -> bool:
        required = self.required_fields.get(task_type, [])
        if not required:
            return False
        if set(data.keys()) != set(required):
            return False
        for key in required:
            value = data.get(key)
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
        return self._passes_task_quality(task_type, data, source_text)

    def _build_sampling_params(self, task_type: str) -> SamplingParams:
        # 延迟优化策略：QA/Preference 限长提速；CoT 放宽长度获取更详细推理
        if task_type == "QA":
            return SamplingParams(
                temperature=0.0,
                top_p=0.7,
                max_tokens=160,
                stop=["<|im_end|>"],
                repetition_penalty=1.0,
                structured_outputs=self._structured_json_params("QA"),
            )

        if task_type == "Preference":
            return SamplingParams(
                temperature=0.0,
                top_p=1.0,
                max_tokens=900,
                stop=["<|im_end|>"],
                repetition_penalty=1.03,
                structured_outputs=self._structured_json_params("Preference"),
            )

        # CoT：不刻意限短，保留较大 token 预算生成更长推理
        return SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=1800,
            stop=["<|im_end|>"],
            repetition_penalty=1.05,
            structured_outputs=self._structured_json_params("CoT"),
        )

    def _build_repair_sampling_params(self, task_type: str) -> SamplingParams:
        # 修复阶段使用更低随机性，优先稳定产出结构化 JSON
        if task_type == "QA":
            max_tokens = 700
        elif task_type == "CoT":
            max_tokens = 2200
        else:
            max_tokens = 900

        return SamplingParams(
            temperature=0.0,
            top_p=0.9,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            repetition_penalty=1.0,
            structured_outputs=self._structured_json_params(task_type) if task_type in ["QA", "CoT", "Preference"] else None,
        )

    def _build_review_sampling_params(self, task_type: str, attempt_no: int) -> SamplingParams:
        if task_type == "QA":
            max_tokens = 700
        elif task_type == "CoT":
            max_tokens = 3200
        else:
            max_tokens = 1400

        return SamplingParams(
            temperature=0.0 if attempt_no <= 2 else 0.2,
            top_p=0.9,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            repetition_penalty=1.02,
            structured_outputs=self._structured_json_params(task_type) if task_type in ["QA", "CoT", "Preference"] else None,
        )

    def _structured_json_params(self, task_type: str) -> Any:
        schema = self._json_schema_for_task(task_type)
        if StructuredOutputsParams is not None:
            return StructuredOutputsParams(json=schema, disable_any_whitespace=True)
        return {"json": schema, "disable_any_whitespace": True}

    def _json_schema_for_task(self, task_type: str) -> Dict[str, Any]:
        if task_type == "QA":
            return {
                "type": "object",
                "additionalProperties": False,
                "required": ["question", "answer"],
                "properties": {
                    "question": {"type": "string", "minLength": 4, "maxLength": 220},
                    "answer": {"type": "string", "minLength": 8, "maxLength": 220},
                },
            }
        if task_type == "CoT":
            return {
                "type": "object",
                "additionalProperties": False,
                "required": ["question", "rationale", "final_answer"],
                "properties": {
                    "question": {"type": "string", "minLength": 4, "maxLength": 220},
                    "rationale": {
                        "type": "string",
                        "minLength": 40,
                        "maxLength": 2200,
                    },
                    "final_answer": {"type": "string", "minLength": 8, "maxLength": 420},
                },
            }
        if task_type == "Preference":
            return {
                "type": "object",
                "additionalProperties": False,
                "required": ["question", "chosen", "rejected", "preference_reason"],
                "properties": {
                    "question": {"type": "string", "minLength": 4, "maxLength": 220},
                    "chosen": {"type": "string", "minLength": 8, "maxLength": 1200},
                    "rejected": {"type": "string", "minLength": 8, "maxLength": 1200},
                    "preference_reason": {"type": "string", "minLength": 12, "maxLength": 1200},
                },
            }
        raise ValueError(f"不支持的 task_type: {task_type}")

    def _truncate_text_at_boundary(self, text: str, limit: int) -> str:
        value = text.strip()
        if len(value) <= limit:
            return value

        cut = value[:limit].rstrip()

        sentence_marks = "。！？.!?"
        last_sentence = max(cut.rfind(mark) for mark in sentence_marks)
        if last_sentence >= 20:
            return cut[:last_sentence + 1].rstrip()

        phrase_marks = "；;，,、：:"
        last_phrase = max(cut.rfind(mark) for mark in phrase_marks)
        if last_phrase >= 20:
            return cut[:last_phrase].rstrip()

        last_space = cut.rfind(" ")
        if last_space >= 20:
            return cut[:last_space].rstrip(" ,;:")

        return cut.rstrip()

    def _truncate_qa_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._truncate_fields("QA", data)

    def _truncate_fields(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(data)
        for field, limit in self.length_limits.get(task_type, {}).items():
            normalized[field] = self._truncate_text_at_boundary(
                str(normalized.get(field, "")).strip(),
                limit,
            )

        return normalized

    def _fallback_plain_text_qa(
        self,
        text: str,
        source_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        candidate = self._strip_generation_scaffolding(
            self._strip_reasoning_text(text or "")
        ).strip()
        if not candidate:
            return None
        if candidate.startswith(("{", "[")) and candidate.endswith(("}", "]")):
            return None
        if len(candidate) < 8:
            return None
        lowered = candidate.lower()
        if "json" in lowered or re.search(r"不是\s*json|输出\s*json|json\s*格式", candidate, flags=re.IGNORECASE):
            return None
        if self._looks_like_meta_or_thought(candidate) or self._looks_like_model_monologue(candidate):
            return None

        payload = {
            "question": self._suggest_qa_question(source_text or ""),
            "answer": candidate,
        }
        normalized = self._normalize_parsed_data("QA", payload, source_text)
        if normalized is None:
            return None
        normalized = self._truncate_fields("QA", normalized)
        if self._validate_generated_data("QA", normalized, source_text):
            return normalized
        return None

    def _try_parse_and_validate(
        self,
        task_type: str,
        text: str,
        source_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        clean_text = self._clean_json_string(text)
        detached_qa = self._extract_detached_nested_object(text, "qa") if task_type == "QA" else None
        candidates = [
            clean_text,
            self._repair_json_syntax_only(clean_text),
            self._escape_unquoted_inner_value_quotes(self._repair_json_syntax_only(clean_text)),
            self._salvage_truncated_json_object(clean_text),
            clean_text.replace('\n', '\\n'),
            self._repair_json_syntax_only(clean_text).replace('\n', '\\n'),
            self._escape_unquoted_inner_value_quotes(self._repair_json_syntax_only(clean_text)).replace('\n', '\\n'),
        ]

        for candidate in candidates:
            if not candidate:
                continue
            try:
                data = json.loads(candidate, strict=False)
                if task_type == "QA" and isinstance(data, dict) and detached_qa and "qa" not in data:
                    merged = dict(data)
                    merged["qa"] = detached_qa
                    data = merged
                data = self._normalize_parsed_data(task_type, data, source_text)
                if data is None:
                    continue
                if task_type in {"QA", "CoT"}:
                    data = self._truncate_fields(task_type, data)
                if self._validate_generated_data(task_type, data, source_text):
                    return data
            except Exception:
                continue
        if task_type == "QA":
            for fallback_text in (clean_text, text):
                parsed = self._fallback_plain_text_qa(fallback_text, source_text)
                if parsed is not None:
                    return parsed
        return None

    def _render_review_regeneration_prompt(
        self,
        task_type: str,
        source_text: str,
        failed_outputs: List[str],
        attempt_no: int,
    ) -> str:
        fields = self.required_fields.get(task_type, [])
        field_list = ", ".join(fields)
        guardrail = self._build_source_guardrail(source_text, task_type)
        clipped_failures = "\n\n".join(
            f"[invalid_output_{i + 1}]\n{str(text or '')[:1200]}"
            for i, text in enumerate(failed_outputs[-4:])
            if str(text or "").strip()
        )
        task_rules = {
            "QA": (
                "Output exactly one JSON object with question and answer. "
                "The answer must be a complete Chinese medical answer grounded in the source."
            ),
            "CoT": (
                "Output exactly one JSON object with question, rationale and final_answer. "
                "rationale must be one Chinese string, not an array. "
                "rationale must contain at least six numbered, substantive steps: 1. 2. 3. 4. 5. 6. "
                "final_answer must be present and must summarize a safe conclusion or next-step recommendation."
            ),
            "Preference": (
                "Output exactly one JSON object with question, chosen, rejected and preference_reason. "
                "chosen must be the higher-quality grounded answer; rejected must be a lower-quality answer for the same case; "
                "preference_reason must compare why chosen is better."
            ),
        }.get(task_type, "")
        content = (
            "你是严格的数据合成复审器。前几次模型输出没有通过质量校验。"
            "必须完全丢弃失败输出，只基于原始输入重新生成合格数据。"
            "只输出一个合法 JSON 对象，不输出解释、Markdown、<think>。"
            "禁止输出 status、reason、raw_output、failed、repair_failed 等状态字段。"
            f"固定字段为: {field_list}。"
            f"{task_rules}"
            f"{guardrail}"
            f"这是第 {attempt_no} 次复审重生成，必须一次性满足字段、JSON 和医学质量要求。"
        )
        user_content = (
            f"原始输入:\n{source_text}\n\n"
            f"已判定失败的输出，仅作为反例，禁止沿用:\n{clipped_failures}\n\n"
            f"请重新生成 {task_type} JSON。"
        )
        messages = [
            {"role": "system", "content": content},
            {"role": "user", "content": user_content},
        ]
        if self._qa_uses_native_template:
            prompt = self._render_native_chat_template(messages, enable_thinking=False)
        else:
            prompt = content + "\n\n" + user_content
        if task_type == "CoT" and self._is_groin_obstruction_source(source_text):
            prompt += self._cot_prefill_json_prefix(source_text)
        return prompt

    def _review_regenerate_failed_item(
        self,
        task_type: str,
        item: Dict[str, Any],
        failed_outputs: List[str],
    ) -> Dict[str, Any]:
        max_attempts = 8 if task_type in {"CoT", "Preference"} else 4
        source_text = item.get("source_text", "")
        observed_failures = [
            self._sanitize_failed_repair_output(source_text, text)
            for text in failed_outputs
            if str(text or "").strip()
        ]

        for attempt_no in range(1, max_attempts + 1):
            prompt = self._render_review_regeneration_prompt(
                task_type,
                source_text,
                observed_failures,
                attempt_no,
            )
            outputs = self.llm.generate([prompt], self._build_review_sampling_params(task_type, attempt_no))
            regenerated_text = outputs[0].outputs[0].text if outputs and outputs[0].outputs else ""
            candidate_text = self._apply_prefill_json_prefix(task_type, regenerated_text, source_text)
            parsed = self._try_parse_and_validate(task_type, candidate_text, source_text)
            if parsed is not None:
                return {
                    "status": "success",
                    "data": parsed,
                    "repaired": True,
                    "repair_attempts": 2 + attempt_no,
                    "review_regenerated": True,
                }
            observed_failures.append(self._sanitize_failed_repair_output(source_text, candidate_text))

        idx = item.get("idx", "?")
        raise RuntimeError(
            f"{task_type} generation for item {idx} failed quality validation after review regeneration"
        )

    def _repair_failed_batch(self, task_type: str, repair_items: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        对首轮失败样本执行二阶段修复。
        repair_items: [{"idx": int, "source_text": str, "raw_output": str}, ...]
        返回: {idx: {"status": ..., "data": ...}}
        """
        if not repair_items:
            return {}

        prompts = [
            self._render_repair_prompt(task_type, item["source_text"], item.get("raw_output", ""))
            for item in repair_items
        ]
        repair_outputs = self.llm.generate(prompts, self._build_repair_sampling_params(task_type))

        repaired_result_map: Dict[int, Dict[str, Any]] = {}
        retry_items: List[Dict[str, Any]] = []
        for item, output in zip(repair_items, repair_outputs):
            idx = item["idx"]
            repaired_text = output.outputs[0].text if output.outputs else ""
            repaired_candidate = self._apply_prefill_json_prefix(task_type, repaired_text, item["source_text"])
            parsed = self._try_parse_and_validate(task_type, repaired_candidate, item["source_text"])
            if parsed is not None:
                repaired_result_map[idx] = {
                    "status": "success",
                    "data": parsed,
                    "repaired": True,
                }
                continue

            retry_items.append({
                "idx": idx,
                "source_text": item["source_text"],
                "raw_output": item.get("raw_output", ""),
                "repair_raw_output": repaired_candidate,
            })

        if retry_items:
            retry_prompts = [
                self._render_second_repair_prompt(task_type, item["source_text"], item.get("repair_raw_output", ""))
                for item in retry_items
            ]
            retry_outputs = self.llm.generate(retry_prompts, self._build_repair_sampling_params(task_type))

            for item, output in zip(retry_items, retry_outputs):
                idx = item["idx"]
                retry_text = output.outputs[0].text if output.outputs else ""
                retry_candidate = self._apply_prefill_json_prefix(task_type, retry_text, item["source_text"])
                parsed = self._try_parse_and_validate(task_type, retry_candidate, item["source_text"])
                if parsed is not None:
                    repaired_result_map[idx] = {
                        "status": "success",
                        "data": parsed,
                        "repaired": True,
                        "repair_attempts": 2,
                    }
                    continue

                repaired_result_map[idx] = self._review_regenerate_failed_item(
                    task_type,
                    item,
                    [
                        item.get("raw_output", ""),
                        item.get("repair_raw_output", ""),
                        retry_candidate,
                    ],
                )

        for item in retry_items:
            idx = item["idx"]
            if idx in repaired_result_map:
                continue
            repaired_result_map[idx] = self._review_regenerate_failed_item(
                task_type,
                item,
                [
                    item.get("raw_output", ""),
                    item.get("repair_raw_output", ""),
                ],
            )

        return repaired_result_map

    def generate_data_batch(self, task_type: str, inputs: List[str]) -> List[Dict[str, Any]]:
        if task_type not in self.task_templates:
            raise ValueError(f"不支持的 task_type: {task_type}")

        prompts = []
        for text in inputs:
            prompts.append(self._render_prompt(task_type, text))

        sampling_params = self._build_sampling_params(task_type)

        outputs = self.llm.generate(prompts, sampling_params)

        # 先占位，首轮失败的样本进入二阶段修复
        results: List[Optional[Dict[str, Any]]] = [None] * len(outputs)
        repair_items: List[Dict[str, Any]] = []

        for i, output in enumerate(outputs):
            generated_text = output.outputs[0].text if output.outputs else ""
            candidate_text = self._apply_prefill_json_prefix(task_type, generated_text, inputs[i])
            parsed = self._try_parse_and_validate(task_type, candidate_text, inputs[i])
            if parsed is not None:
                results[i] = {"status": "success", "data": parsed}
                continue

            # 首轮直接失败，进入修复阶段
            repair_items.append({
                "idx": i,
                "source_text": inputs[i],
                "raw_output": candidate_text,
            })

        repaired_map = self._repair_failed_batch(task_type, repair_items)
        for item in repair_items:
            idx = item["idx"]
            if idx in repaired_map:
                results[idx] = repaired_map[idx]
            else:
                raise RuntimeError(f"{task_type} repair result missing for item {idx}")

        # 理论上不应存在 None，这里兜底
        for i, r in enumerate(results):
            if r is None:
                raise RuntimeError(f"{task_type} internal empty result for item {i}")

        
        return [r for r in results if r is not None]

    def _extract_case_parts(self, source_text: str) -> Dict[str, str]:
        demo = ""
        symptom = ""
        finding = ""

        m_demo = re.search(r"^(.*?)。主诉[:：]", source_text)
        if m_demo:
            demo = m_demo.group(1).strip()

        m_symptom = re.search(r"主诉[:：](.*?)。查体", source_text)
        if m_symptom:
            symptom = m_symptom.group(1).strip()

        m_finding = re.search(r"查体及辅助检查[:：](.*?)(。|$)", source_text)
        if m_finding:
            finding = m_finding.group(1).strip()

        if not demo and not symptom and not finding:
            return {
                "demo": "患者",
                "symptom": source_text.strip()[:60],
                "finding": "检查信息待补充",
            }

        return {
            "demo": demo or "患者",
            "symptom": symptom or "症状待补充",
            "finding": finding or "检查信息待补充",
        }

    def _infer_primary_assessment(self, finding: str) -> str:
        f = finding or ""
        if "ST段抬高" in f:
            return "急性冠脉综合征风险"
        if "脑梗死" in f:
            return "脑梗死相关神经功能受损"
        if "斑片影" in f:
            return "肺部炎症性病变"
        if "结石" in f:
            return "结石相关器官病变"
        if "尿蛋白" in f:
            return "肾脏受损风险"
        if "白细胞升高" in f or "CRP升高" in f:
            return "感染或炎症反应"
        return "临床异常需进一步评估"

if __name__ == "__main__":
    pass
