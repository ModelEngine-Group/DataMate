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
            "QA": {"question": 220, "answer": 160},
            "CoT": {"question": 220, "rationale": 2000, "final_answer": 220},
            "Preference": {"question": 220, "chosen": 180, "rejected": 180, "preference_reason": 220},
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

    def _clean_json_string(self, text: str) -> str:
        text = text.strip()

        # 移除 Qwen 系列常见的思考段，避免污染 JSON
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        # 兼容未闭合 think 标签
        text = re.sub(r"<think>[\s\S]*$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<\|im_start\|>think[\s\S]*?<\|im_end\|>", "", text, flags=re.IGNORECASE)

        # 移除 Markdown 标记
        text = re.sub(r"^```json", "", text, flags=re.MULTILINE)
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        text = text.strip()
        
        # 🟢 增强：处理模型输出真实换行符的情况
        # 将 JSON 值里的真实换行符替换为空格，防止 json.loads 失败
        # (这是一个简单的 trick，防止 "rationale": "第一行\n第二行" 报错)
        # text = text.replace('\n', ' ') 
        # 上面这行太暴力，可能会破坏 JSON 结构，改用 strict=False 并在失败时尝试修复
        
        extracted = self._extract_first_json_object(text)
        return extracted if extracted else text

    def _repair_json_syntax_only(self, text: str) -> str:
        """Only fix common JSON syntax issues; never invent missing content."""
        repaired = text.strip()
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
        repaired = repaired.replace("，}", "}").replace("，]", "]")
        repaired = repaired.replace("“", '"').replace("”", '"')
        return repaired

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

    def _strip_reasoning_text(self, text: str) -> str:
        t = text.strip()
        t = re.sub(r"<think>[\s\S]*?</think>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"<think>[\s\S]*$", "", t, flags=re.IGNORECASE)
        t = re.sub(r"<\|im_start\|>think[\s\S]*?<\|im_end\|>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"^```json", "", t, flags=re.MULTILINE)
        t = re.sub(r"^```", "", t, flags=re.MULTILINE)
        t = re.sub(r"\s+", " ", t).strip()
        return t

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

        if source_text and self._has_obvious_source_contradiction(source_text, data):
            return False

        if task_type == "QA":
            q = str(data.get("question", "")).strip()
            a = str(data.get("answer", "")).strip()
            if self._looks_like_meta_or_thought(q) or self._looks_like_meta_or_thought(a):
                return False
            if len(a) < 8:
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
            # 简单步骤判定，避免输出成口语段落
            step_hits = len(re.findall(r"(\d+[\.、]|步骤\d+|->)", r))
            if step_hits < 3:
                return False
            return True

        if task_type == "Preference":
            c = str(data.get("chosen", "")).strip()
            rj = str(data.get("rejected", "")).strip()
            pr = str(data.get("preference_reason", "")).strip()
            if any(self._looks_like_meta_or_thought(x) or self._looks_like_model_monologue(x) for x in [c, rj, pr]):
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
                if any(marker in prefix for marker in ["不", "无", "无需", "不需", "忽视", "拒绝", "暂不", "不能", "避免", "慎用", "除非", "仅在"]):
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
            if any(has_forbidden_without_negation(term) for term in unrelated):
                return True
            if any(term in generated for term in ["穿孔", "引流", "推挤", "减压"]):
                return True
            if final_answer:
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
            if "缺抗性卒中" in generated:
                return True
            if any(term in generated for term in ["脑干梗死", "血管痉挛", "阿瑟曼征", "侧枝循环障碍"]):
                return True
            if has_forbidden_without_negation("SPECT"):
                return True
            if data.keys() >= {"chosen", "rejected", "preference_reason"}:
                rejected = str(data.get("rejected", ""))
                if self._contains_positive_recommendation(rejected, ["机械取栓", "取栓", "再灌注"]):
                    return True
            if re.search(r"(先行|优先|先做|先完善).{0,12}(MRI|磁共振).{0,18}(再|后).{0,8}(溶栓|取栓|再灌注)", generated):
                return True
            if re.search(r"(延后|延迟|暂缓|推迟).{0,10}(溶栓|取栓|再灌注)", generated):
                return True
            if "CT未见出血" in source and "溶栓" in generated and re.search(r"(不应|不能|无需|不推荐).{0,8}溶栓", generated):
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
        if "男" in source:
            rules.append("病例为男性。")
        if "女" in source:
            rules.append("病例为女性。")
        if "腹股沟" in source and "包块" in source:
            rules.append("腹股沟包块合并阶梯状液气平时，应围绕嵌顿性腹股沟疝合并肠梗阻分析。")
            rules.append("所有字段禁止出现穿孔、引流、推挤、减压等原文未给出的并发症或处置。")
            rules.append("CoT 任务中，final_answer 必须建议尽快外科或急诊外科评估，不得建议观察、延迟外科评估或延迟手术。")
            rules.append("Preference 任务中，chosen 必须字面包含：嵌顿性腹股沟疝合并肠梗阻，并建议尽快外科评估；不得把卵巢囊肿、盆腔炎、睾丸扭转、阑尾肿瘤等作为 chosen。")
            rules.append("Preference 任务中，rejected 不得是疾病名，严禁输出卵巢囊肿、盆腔炎、睾丸扭转等其他诊断名称；必须用同一病例的低质量处理建议作为 rejected，例如仅建议观察、延误外科评估、忽视肠梗阻证据或未及时处理嵌顿疝。")
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
        if rules:
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
        compact = text.strip()
        guardrail = self._build_source_guardrail(compact, "QA")
        if self._qa_uses_native_template:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Generate one medical QA JSON object from the source text. "
                        "Output JSON only. Do not output explanations or <think>. "
                        "Use exactly two fields: question and answer. "
                        "Keep answer concise and grounded in the source text. "
                        f"{guardrail}"
                    ),
                },
                {
                    "role": "user",
                    "content": compact,
                },
            ]
            return self._render_native_chat_template(messages, enable_thinking=False)

        return (
            "<|im_start|>system\n"
            "Generate one medical QA JSON object from the source text. "
            "Output JSON only. Do not output explanations or <think>. "
            "Use exactly two fields: question and answer. "
            "Keep answer concise and grounded in the source text. "
            f"{guardrail}\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{compact}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>\n\n</think>\n\n"
        )

    def _render_cot_native_prompt(self, text: str) -> str:
        compact = text.strip()
        guardrail = self._build_source_guardrail(compact, "CoT")
        if self._qa_uses_native_template:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是资深临床医生。请基于用户给出的中文病例生成一个 CoT JSON 对象。"
                        "只能输出 JSON，不要输出解释或 <think>。"
                        "字段固定为 question、rationale、final_answer。"
                        "question 必须是一个简短的临床问题，不得写模型自述、推理过程、'我需要'或'这让我'。"
                        "rationale 必须是一个中文字符串，不要使用数组；必须包含六个编号：1. 2. 3. 4. 5. 6.。"
                        "每个编号步骤必须引用输入病例中的症状、检查或处置依据，每步尽量不超过35字。"
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
            groin_repair_rules = ""
            if "腹股沟" in (source_text or "") and "阶梯状液气平" in (source_text or ""):
                groin_repair_rules = (
                    "腹股沟包块合并阶梯状液气平时，chosen 必须写嵌顿性腹股沟疝合并肠梗阻并建议尽快外科评估。"
                    "腹股沟包块合并阶梯状液气平的 Preference 修复中，chosen 必须字面包含：嵌顿性腹股沟疝合并肠梗阻；rejected 不得是疾病名，只能写同一病例下的低质量处置。"
                    "腹股沟包块合并阶梯状液气平时，所有字段禁止出现穿孔、引流、推挤、减压等原文未给出的并发症或处置。"
                    "腹股沟包块合并肠梗阻风险时，CoT 的 final_answer 不得建议观察、延迟外科评估或延迟手术。"
                )
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"你是严格的 JSON 修复器。只输出一个合法 JSON 对象，字段固定为 {fields}。"
                        "不要输出解释、markdown 或 <think>。"
                        "只能基于原始输入和候选输出修复结构，不得编造原文不存在的诊断、症状或检查。"
                        "CoT 的 rationale 必须写成单个编号字符串，不得使用数组；必须包含六个编号：1. 2. 3. 4. 5. 6.；final_answer 必须存在且简短。"
                        "Preference 的 rejected 必须是同一病例下的低质量回答，不得用与病例性别或部位冲突的其他疾病凑数。"
                        "如果 Preference 候选 rejected 是离题疾病或其他诊断名称，必须改写为同病例低质量处置建议，例如仅建议观察、延误外科评估、忽视关键检查或遗漏高危证据。"
                        "如果 Preference 候选 chosen 是离题疾病或其他错误诊断，必须改写为原始输入支持的正确答案。"
                        f"{groin_repair_rules}"
                        "CoT 的 final_answer 必须是安全处置建议，不得输出明显错误的首要处理。"
                        f"{guardrail}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"原始输入：{source_text}\n"
                        f"候选输出：{clipped}\n"
                        f"{note}\n"
                        "请修复为目标 JSON。"
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
            groin_instruction = ""
            if "腹股沟" in source and "阶梯状液气平" in source:
                groin_instruction = "腹股沟包块合并阶梯状液气平时，诊断和处置只写：嵌顿性腹股沟疝合并肠梗阻，建议尽快外科评估。"
            content = (
                f"你是严格的 JSON 二次修复器。只输出一个合法 JSON 对象，字段固定为 {fields}。"
                "请完全重写，不要沿用上一轮原句，不要输出解释、markdown 或 <think>。"
                "必须只根据原始输入和允许的医学结论生成，不能扩展原文未给出的并发症或处置。"
                "CoT 的 rationale 必须写成单个编号字符串，不得使用数组；必须包含六个编号：1. 2. 3. 4. 5. 6.；final_answer 必须存在。"
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

    def _normalize_parsed_data(self, task_type: str, data: Any) -> Optional[Dict[str, Any]]:
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
        elif task_type == "CoT" and isinstance(normalized.get("rationale"), str):
            normalized["rationale"] = self._normalize_cot_rationale_text(normalized["rationale"])

        return normalized

    def _normalize_cot_rationale_text(self, rationale: str) -> str:
        text = re.sub(r"\s+", " ", rationale or "").strip()
        if not text:
            return text
        if len(re.findall(r"(\d+[\.、]|步骤\d+|->)", text)) >= 3:
            return text

        parts = [p.strip(" ；;。") for p in re.split(r"[。；;]", text) if p.strip(" ；;。")]
        if len(parts) < 3:
            comma_parts = [p.strip(" ，,") for p in re.split(r"[，,]", text) if p.strip(" ，,")]
            if len(comma_parts) >= 4:
                parts = comma_parts

        if len(parts) < 3:
            return text

        steps = parts[:6]
        return "".join(f"{i + 1}. {step}。" for i, step in enumerate(steps))

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
                top_p=0.8,
                max_tokens=220,
                stop=["<|im_end|>"],
                repetition_penalty=1.0,
            )

        if task_type == "Preference":
            return SamplingParams(
                temperature=0.0,
                top_p=1.0,
                max_tokens=320,
                stop=["<|im_end|>"],
                repetition_penalty=1.03,
                structured_outputs=self._structured_json_params("Preference"),
            )

        # CoT：不刻意限短，保留较大 token 预算生成更长推理
        return SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=900,
            stop=["<|im_end|>"],
            repetition_penalty=1.05,
            structured_outputs=self._structured_json_params("CoT"),
        )

    def _build_repair_sampling_params(self, task_type: str) -> SamplingParams:
        # 修复阶段使用更低随机性，优先稳定产出结构化 JSON
        if task_type == "QA":
            max_tokens = 220
        elif task_type == "CoT":
            max_tokens = 1400
        else:
            max_tokens = 360

        return SamplingParams(
            temperature=0.0,
            top_p=0.9,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            repetition_penalty=1.0,
            structured_outputs=self._structured_json_params(task_type) if task_type in ["CoT", "Preference"] else None,
        )

    def _structured_json_params(self, task_type: str) -> Any:
        schema = self._json_schema_for_task(task_type)
        if StructuredOutputsParams is not None:
            return StructuredOutputsParams(json=schema, disable_any_whitespace=True)
        return {"json": schema, "disable_any_whitespace": True}

    def _json_schema_for_task(self, task_type: str) -> Dict[str, Any]:
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
                        "maxLength": 900,
                    },
                    "final_answer": {"type": "string", "minLength": 8, "maxLength": 220},
                },
            }
        if task_type == "Preference":
            return {
                "type": "object",
                "additionalProperties": False,
                "required": ["question", "chosen", "rejected", "preference_reason"],
                "properties": {
                    "question": {"type": "string", "minLength": 4, "maxLength": 220},
                    "chosen": {"type": "string", "minLength": 8, "maxLength": 180},
                    "rejected": {"type": "string", "minLength": 8, "maxLength": 180},
                    "preference_reason": {"type": "string", "minLength": 12, "maxLength": 220},
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
        normalized = dict(data)
        question = str(normalized.get("question", "")).strip()
        answer = str(normalized.get("answer", "")).strip()

        q_limit = self.length_limits["QA"]["question"]
        a_limit = self.length_limits["QA"]["answer"]

        normalized["question"] = self._truncate_text_at_boundary(question, q_limit)
        normalized["answer"] = self._truncate_text_at_boundary(answer, a_limit)

        return normalized

    def _try_parse_and_validate(
        self,
        task_type: str,
        text: str,
        source_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        clean_text = self._clean_json_string(text)
        candidates = [
            clean_text,
            self._repair_json_syntax_only(clean_text),
            clean_text.replace('\n', '\\n'),
            self._repair_json_syntax_only(clean_text).replace('\n', '\\n'),
        ]

        for candidate in candidates:
            try:
                data = json.loads(candidate, strict=False)
                data = self._normalize_parsed_data(task_type, data)
                if data is None:
                    continue
                if task_type == "QA":
                    data = self._truncate_qa_fields(data)
                if self._validate_generated_data(task_type, data, source_text):
                    return data
            except Exception:
                continue
        return None

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
            parsed = self._try_parse_and_validate(task_type, repaired_text, item["source_text"])
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
                "repair_raw_output": repaired_text,
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
                parsed = self._try_parse_and_validate(task_type, retry_text, item["source_text"])
                if parsed is not None:
                    repaired_result_map[idx] = {
                        "status": "success",
                        "data": parsed,
                        "repaired": True,
                        "repair_attempts": 2,
                    }
                    continue

                repaired_result_map[idx] = {
                    "status": "failed",
                    "reason": "repair_failed",
                    "raw_output": item.get("raw_output", ""),
                    "repair_raw_output": item.get("repair_raw_output", ""),
                    "second_repair_raw_output": retry_text,
                }

        for item in retry_items:
            idx = item["idx"]
            if idx in repaired_result_map:
                continue
            repaired_result_map[idx] = {
                "status": "failed",
                "reason": "repair_failed",
                "raw_output": item.get("raw_output", ""),
                "repair_raw_output": item.get("repair_raw_output", ""),
            }

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
            parsed = self._try_parse_and_validate(task_type, generated_text, inputs[i])
            if parsed is not None:
                results[i] = {"status": "success", "data": parsed}
                continue

            # 首轮直接失败，进入修复阶段
            repair_items.append({
                "idx": i,
                "source_text": inputs[i],
                "raw_output": generated_text,
            })

        repaired_map = self._repair_failed_batch(task_type, repair_items)
        for item in repair_items:
            idx = item["idx"]
            if idx in repaired_map:
                results[idx] = repaired_map[idx]
            else:
                results[idx] = {
                    "status": "failed",
                    "reason": "repair_missing",
                    "raw_output": item.get("raw_output", ""),
                }

        # 理论上不应存在 None，这里兜底
        for i, r in enumerate(results):
            if r is None:
                results[i] = {
                    "status": "failed",
                    "reason": "internal_empty_result",
                    "raw_output": "",
                }

        
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
