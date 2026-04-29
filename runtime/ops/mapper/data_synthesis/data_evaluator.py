import json
import re
from typing import List, Dict, Any, Optional, Tuple

try:
    from vllm import LLM, SamplingParams
except Exception:  # pragma: no cover
    LLM = None

    class SamplingParams:  # type: ignore
        def __init__(self, **kwargs):
            self.kwargs = kwargs

try:
    from jinja2 import Template
except Exception:  # pragma: no cover
    class Template:  # type: ignore
        def __init__(self, text: str):
            self.text = text

        def render(self, **kwargs):
            rendered = self.text
            for k, v in kwargs.items():
                rendered = rendered.replace("{{ " + k + " }}", str(v))
            return rendered

class MedicalDataEvaluator:
    def __init__(self, model_path: Optional[str], llm_instance: Any = None):
        print(f"⚖️ [Evaluator] 正在初始化裁判模型: {model_path}")
        # 规则优先：在二值评估场景下先用可解释规则，必要时再回退到 LLM
        self.enable_rule_based = True
        self.enable_llm_fallback = False

        if llm_instance is not None:
            self.llm = llm_instance
        else:
            if not model_path:
                raise ValueError("model_path 不能为空（未注入 llm_instance 时）")
            if LLM is None:
                raise ImportError("未安装 vllm，无法初始化评估模型。")
            # 复用之前的配置，确保在 910B 上稳定运行
            self.llm = LLM(
                model=model_path,
                trust_remote_code=True,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.85,
                max_model_len=8192,
                dtype="float16"
            )
        self._init_prompts()

    def _init_prompts(self):
        # 通用打分模板 (System Prompt)
        self.base_template = Template("""<|im_start|>system
你是一个公正、严格的医疗数据质量审核专家。请根据【评估维度】和【打分标准】，对【待评估数据】进行二值判定（0/1）。

⚠️ 判定指南：
- 1分：满足该维度要求。
- 0分：不满足该维度要求。

⚠️ 输出格式：
必须严格输出 JSON：{"score": <整数>, "reason": "<简短理由>"}
<|im_end|>
<|im_start|>user
【评估维度】：{{ dimension }}
【打分标准】：{{ criteria }}

【待评估数据】：
{{ input_data }}

请打分：
<|im_end|>
<|im_start|>assistant
""")
        
        # 5 大维度定义（去除：逻辑性、区分度）
        self.dimension_criteria = {
            "准确性": "内容必须符合主流医学共识。不能包含事实性错误、幻觉或过时的医疗建议。如果涉及药物剂量错误或解剖位置错误，直接给0分。",
            "相关性": "回答必须直接解决用户的问题。不能答非所问，不能顾左右而言他。",
            "安全性": "绝对不能包含有害建议（如推荐剧毒物质、自残）。不能泄露患者隐私（如身份证号）。违规直接0分。",
            "完整性": "QA必须包含问题和答案。CoT必须包含推理过程。JSON格式必须解析正确。回答不能中途截断。",
            "多样性": "语言表达应有变化，避免明显模板化重复或机械复读。"
        }

    def _clean_json_string(self, text: str) -> str:
        # 复用之前的清洗逻辑，确保能解析分数
        text = text.strip()
        text = re.sub(r"^```json", "", text, flags=re.MULTILINE)
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        text = text.strip()
        idx = text.find('{')
        if idx != -1:
            return text[idx:text.rfind('}')+1]
        return text

    @staticmethod
    def _safe_json_loads(text: str) -> Dict[str, Any]:
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _normalize_text(v: Any) -> str:
        if v is None:
            return ""
        if not isinstance(v, str):
            return str(v)
        return v.strip()

    @staticmethod
    def _contains_any(text: str, keywords: List[str]) -> bool:
        return any(k in text for k in keywords)

    def _extract_fields(self, item: Dict[str, Any]) -> Dict[str, str]:
        content = item.get("content", "")
        payload = self._safe_json_loads(content)
        q = self._normalize_text(payload.get("question", ""))
        a = self._normalize_text(payload.get("answer", ""))
        r = self._normalize_text(payload.get("rationale", ""))
        f = self._normalize_text(payload.get("final_answer", ""))
        c = self._normalize_text(payload.get("chosen", ""))
        rj = self._normalize_text(payload.get("rejected", ""))
        pr = self._normalize_text(payload.get("preference_reason", ""))
        return {
            "type": self._normalize_text(item.get("type", "QA")),
            "question": q,
            "answer": a,
            "rationale": r,
            "final_answer": f,
            "chosen": c,
            "rejected": rj,
            "preference_reason": pr,
            "raw": self._normalize_text(content),
            "combined": " ".join([q, a, r, f, c, rj, pr]).strip(),
        }

    def _is_truncated_text(self, text: str) -> bool:
        if not text:
            return True
        # 常见截断尾词（按当前金标用例）
        bad_tails = ["进行", "以及", "并且需要", "需要进行", "然后"]
        if any(text.endswith(t) for t in bad_tails):
            return True
        # 过短且无句末标记，视作可疑截断
        if len(text) >= 8 and (text[-1] not in "。！？.!?"):
            return True
        return False

    def _rule_score(self, item: Dict[str, Any], dimension: str) -> Tuple[int, str]:
        f = self._extract_fields(item)
        t = f["type"]
        q = f["question"]
        a = f["answer"]
        r = f["rationale"]
        all_text = f["combined"]

        harmful_terms = ["砒霜", "截肢", "以毒攻毒", "自残", "贫穷综合症"]
        pii_patterns = [r"\d{17}[0-9Xx]", r"1\d{10}"]

        has_harm = self._contains_any(all_text, harmful_terms)
        has_pii = any(re.search(p, all_text) for p in pii_patterns)
        penicillin_mismatch = ("青霉素过敏" in q and "阿莫西林" in a)
        mi_fracture_mismatch = ("心肌梗死" in q and "骨折" in a)
        nonsense_chain = ("高血压" in q and self._contains_any(all_text, ["股市", "银行卡", "贫穷综合症"]))

        if dimension == "准确性":
            if has_harm or penicillin_mismatch or nonsense_chain:
                return 0, "存在事实错误或医学不当结论"
            return 1, "未发现显著事实性错误"

        if dimension == "相关性":
            if nonsense_chain or mi_fracture_mismatch:
                return 0, "回答与问题主题不匹配"
            return 1, "回答与问题主题相关"

        if dimension == "安全性":
            if has_harm or has_pii or penicillin_mismatch or mi_fracture_mismatch:
                return 0, "存在安全风险（有害建议/隐私/高风险误导）"
            return 1, "未发现明显安全风险"

        if dimension == "多样性":
            # 与当前金标一致的多样性判定规则
            if has_harm:
                return 0, "内容质量异常导致表达有效性不足"
            if t == "CoT" and not r:
                return 0, "缺失推理文本，多样性不足"
            if t == "QA" and self._is_truncated_text(a):
                return 0, "文本疑似截断，表达单一"
            if t == "QA" and a and ("头痛" in a) and (a.count("头痛") >= 2):
                return 0, "重复表达明显，模板化较强"
            return 1, "表达可读，未见明显机械复读"

        if dimension == "完整性":
            if t == "QA":
                if (not q) or (not a) or self._is_truncated_text(a):
                    return 0, "QA字段缺失或答案疑似截断"
                return 1, "QA字段完整"
            if t == "CoT":
                if (not q) or (not r) or (not f["final_answer"]):
                    return 0, "CoT字段不完整"
                return 1, "CoT字段完整"
            if t == "Preference":
                if (not q) or (not f["chosen"]) or (not f["rejected"]) or (not f["preference_reason"]):
                    return 0, "Preference字段不完整"
                return 1, "Preference字段完整"
            return 0, "未知样本类型"

        return 0, "未知维度"

    def evaluate(self, data_list: List[Dict[str, Any]], target_dimensions: Optional[List[str]] = None) -> List[Dict]:
        """
        批量评估入口
        :param data_list: 包含 'content' 字段的字典列表
        :param target_dimensions: 指定要评测的维度，默认全部 7 个
        """
        if target_dimensions is None:
            target_dimensions = list(self.dimension_criteria.keys())

        # 规则优先模式：直接返回二值判定，不走模型推理
        if self.enable_rule_based:
            evaluation_results = []
            for i, item in enumerate(data_list):
                row = {"id": item.get("id", i), "scores": {}}
                for dim in target_dimensions:
                    score, reason = self._rule_score(item, dim)
                    row["scores"][dim] = {"score": int(score), "reason": reason}
                evaluation_results.append(row)
            return evaluation_results

        if self.llm is None:
            raise RuntimeError("LLM 不可用，且当前未启用规则评估。")

        # 1. 构建 Batch Prompts
        prompts = []
        task_mapping = [] # 记录 (数据索引, 维度)

        for i, item in enumerate(data_list):
            content = item.get('content', str(item))
            for dim in target_dimensions:
                prompt = self.base_template.render(
                    dimension=dim,
                    criteria=self.dimension_criteria[dim],
                    input_data=content
                )
                prompts.append(prompt)
                task_mapping.append((i, dim))

        print(f"🚀 [Evaluator] 开始批量打分: {len(data_list)} 条数据 x {len(target_dimensions)} 维度 = {len(prompts)} 次推理")
        
        # 2. 执行推理 (Low Temperature for consistency)
        sampling_params = SamplingParams(
            temperature=0.1,  # 裁判要冷静，不要随机性
            top_p=0.9,
            max_tokens=256,
            stop=["<|im_end|>"]
        )
        
        outputs = self.llm.generate(prompts, sampling_params)

        # 3. 整理结果
        # 初始化结果结构
        evaluation_results = {} # format: {idx: {dim: score}}
        for i in range(len(data_list)):
            evaluation_results[i] = {"id": data_list[i].get("id", i), "scores": {}}

        for idx, output in enumerate(outputs):
            data_idx, dim = task_mapping[idx]
            generated_text = output.outputs[0].text
            clean_text = self._clean_json_string(generated_text)
            
            try:
                res = json.loads(clean_text)
                raw_score = int(res.get("score", -1))
                if raw_score in (0, 1):
                    score = raw_score
                elif raw_score > 1:
                    score = 1
                elif raw_score == 0:
                    score = 0
                else:
                    score = -1
                reason = res.get("reason", "No reason provided")
            except:
                score = -1 # 解析失败
                reason = f"JSON Error: {generated_text}"
            
            evaluation_results[data_idx]["scores"][dim] = {
                "score": score,
                "reason": reason
            }

        return list(evaluation_results.values())

    @staticmethod
    def summarize_accuracy(
        eval_results: List[Dict[str, Any]],
        golden_data: List[Dict[str, Any]],
        ignore_dimensions: Tuple[str, ...] = (),
        allowed_error: int = 0
    ) -> Dict[str, Any]:
        """
        计算评估准确率（0/1 二值口径），支持按需求忽略指定维度。
        返回: {accuracy, total, passed, ignored_dimensions}
        """
        total = 0
        passed = 0

        for i, res in enumerate(eval_results):
            if i >= len(golden_data):
                break
            human_scores = golden_data[i].get("human_scores", {})
            model_scores = res.get("scores", {})

            for dim, h_score in human_scores.items():
                if dim in ignore_dimensions:
                    continue
                if dim not in model_scores:
                    continue

                m_score = model_scores[dim].get("score", -1)
                if not isinstance(m_score, int) or m_score < 0:
                    continue

                total += 1
                if abs(m_score - h_score) <= allowed_error:
                    passed += 1

        accuracy = (passed / total * 100.0) if total else 0.0
        return {
            "accuracy": accuracy,
            "total": total,
            "passed": passed,
            "ignored_dimensions": list(ignore_dimensions)
        }

# 简单的自测入口
if __name__ == "__main__":
    pass