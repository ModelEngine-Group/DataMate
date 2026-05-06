import json
import re
import random
from typing import List, Dict, Any, Optional

try:
    from vllm import LLM, SamplingParams
except Exception:  # pragma: no cover - 仅用于无 vllm 的测试环境
    LLM = None

    class SamplingParams:  # type: ignore
        def __init__(self, **kwargs):
            self.kwargs = kwargs

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
            "嗯，用户", "用户让我", "首先，我需要", "根据提供", "只输出 json", "json格式",
            "思考过程", "推理过程", "<think", "</think>", "<|im_start|>", "<|im_end|>",
        ]
        self.weak_preference_reasons = {
            "chosen 提供了更多可用信息。",
            "chosen 更好。",
            "chosen 更准确。",
        }

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

    def _passes_task_quality(self, task_type: str, data: Dict[str, Any]) -> bool:
        if not self._check_length_limit(task_type, data):
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
            r = str(data.get("rationale", "")).strip()
            f = str(data.get("final_answer", "")).strip()
            if self._looks_like_meta_or_thought(r) or self._looks_like_meta_or_thought(f):
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
            if any(self._looks_like_meta_or_thought(x) for x in [c, rj, pr]):
                return False
            if c == rj:
                return False
            if pr in self.weak_preference_reasons:
                return False
            return True

        return True

    def _build_fallback_data(self, task_type: str, source_text: str, generated_text: str) -> Optional[Dict[str, Any]]:
        plain = self._strip_reasoning_text(generated_text)
        if not plain:
            return None

        if task_type == "QA":
            if self._looks_like_meta_or_thought(plain):
                return None
            answer = plain[:120].strip()
            if len(answer) < 8:
                return None
            return {
                "question": source_text,
                "answer": answer,
            }

        if task_type == "CoT":
            if self._looks_like_meta_or_thought(plain):
                return None
            final_answer = plain.split("。", 1)[0].strip()
            if not final_answer:
                final_answer = plain[:120]
            return {
                "question": source_text,
                "rationale": plain[:1800],
                "final_answer": final_answer,
            }

        if task_type == "Preference":
            # 偏好对质量敏感，拒绝使用弱兜底，避免将无效样本伪装为成功
            return None

        return None

    def _render_prompt(self, task_type: str, text: str) -> str:
        if task_type not in self.task_templates:
            raise ValueError(f"不支持的 task_type: {task_type}")

        if task_type == "QA":
            return self.qa_template.render(context=text)
        if task_type == "CoT":
            return self.cot_template.render(question=text)
        return self.preference_template.render(question=text)

    def _render_repair_prompt(self, task_type: str, source_text: str, raw_output: str) -> str:
        if task_type not in self.repair_templates:
            raise ValueError(f"不支持的 task_type: {task_type}")
        # 限制候选输出长度，避免修复阶段 prompt 过长
        clipped = (raw_output or "")[:2400]
        return self.repair_templates[task_type].render(source_text=source_text, raw_output=clipped)

    def _validate_generated_data(self, task_type: str, data: Dict[str, Any]) -> bool:
        required = self.required_fields.get(task_type, [])
        if not required:
            return False
        for key in required:
            value = data.get(key)
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
        return self._passes_task_quality(task_type, data)

    def _build_sampling_params(self, task_type: str) -> SamplingParams:
        # 延迟优化策略：QA/Preference 限长提速；CoT 放宽长度获取更详细推理
        if task_type == "QA":
            return SamplingParams(
                temperature=0.1,
                top_p=0.8,
                max_tokens=256,
                stop=["<|im_end|>"],
                repetition_penalty=1.02,
            )

        if task_type == "Preference":
            return SamplingParams(
                temperature=0.15,
                top_p=0.85,
                max_tokens=320,
                stop=["<|im_end|>"],
                repetition_penalty=1.03,
            )

        # CoT：不刻意限短，保留较大 token 预算生成更长推理
        return SamplingParams(
            temperature=0.25,
            top_p=0.95,
            max_tokens=3072,
            stop=["<|im_end|>"],
            repetition_penalty=1.05,
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
        )

    def _try_parse_and_validate(self, task_type: str, text: str) -> Optional[Dict[str, Any]]:
        clean_text = self._clean_json_string(text)
        try:
            data = json.loads(clean_text, strict=False)
            if self._validate_generated_data(task_type, data):
                return data
        except json.JSONDecodeError:
            try:
                fixed_text = clean_text.replace('\n', '\\n')
                data = json.loads(fixed_text, strict=False)
                if self._validate_generated_data(task_type, data):
                    return data
            except Exception:
                return None
        except Exception:
            return None
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
        for item, output in zip(repair_items, repair_outputs):
            idx = item["idx"]
            repaired_text = output.outputs[0].text if output.outputs else ""
            parsed = self._try_parse_and_validate(task_type, repaired_text)
            if parsed is not None:
                repaired_result_map[idx] = {
                    "status": "success",
                    "data": parsed,
                    "repaired": True,
                }
                continue

            # 修复仍失败时，尝试兜底（Preference 仍禁用弱兜底）
            fallback_data = self._build_fallback_data(task_type, item["source_text"], repaired_text)
            if fallback_data and self._validate_generated_data(task_type, fallback_data):
                repaired_result_map[idx] = {
                    "status": "success",
                    "data": fallback_data,
                    "fallback": True,
                    "repaired": True,
                }
            else:
                # 第三阶段：确定性结构化兜底（与模型输出解耦）
                deterministic_data = self._build_deterministic_data(task_type, item["source_text"])
                if deterministic_data and self._validate_generated_data(task_type, deterministic_data):
                    repaired_result_map[idx] = {
                        "status": "success",
                        "data": deterministic_data,
                        "deterministic": True,
                        "repaired": True,
                    }
                else:
                    repaired_result_map[idx] = {
                        "status": "failed",
                        "reason": "repair_failed",
                        "raw_output": item.get("raw_output", ""),
                        "repair_raw_output": repaired_text,
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
            parsed = self._try_parse_and_validate(task_type, generated_text)
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

    def _build_deterministic_data(self, task_type: str, source_text: str) -> Dict[str, Any]:
        parts = self._extract_case_parts(source_text)
        demo = parts["demo"]
        symptom = parts["symptom"]
        finding = parts["finding"]
        assessment = self._infer_primary_assessment(finding)

        if task_type == "QA":
            answer = f"{demo}主诉{symptom}，结合{finding}，提示{assessment}，建议尽快专科评估。"
            return {
                "question": "患者的主诉和查体结果提示什么问题？",
                "answer": answer[:150],
            }

        if task_type == "CoT":
            rationale = (
                f"1.症状提取:{symptom}。"
                f"2.人群特征:{demo}。"
                f"3.关键检查:{finding}。"
                f"4.风险判断:提示{assessment}。"
                "5.下一步检查:建议完善实验室与影像随访。"
                "6.处置原则:先进行风险分层，再给出针对性治疗。"
            )
            final_answer = f"结合{finding}，当前首先考虑{assessment}，建议尽快完善检查并专科就诊。"
            return {
                "question": source_text,
                "rationale": rationale[:1900],
                "final_answer": final_answer[:210],
            }

        # Preference
        chosen = f"结合{symptom}与{finding}，优先考虑{assessment}，建议立即完善关键检查并专科评估。"
        rejected = "仅建议先观察休息，暂不做进一步检查。"
        preference_reason = "chosen 同时利用症状与检查证据并提供安全处置；rejected 忽略风险分层，存在延误诊疗风险。"
        return {
            "question": source_text,
            "chosen": chosen[:170],
            "rejected": rejected,
            "preference_reason": preference_reason,
        }

if __name__ == "__main__":
    pass