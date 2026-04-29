from __future__ import annotations

from typing import Dict, List, Any, Iterable


REQUIRED_FIELDS = {
    "QA": ["question", "answer"],
    "CoT": ["question", "rationale", "final_answer"],
    "Preference": ["question", "chosen", "rejected", "preference_reason"],
}


def _safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _field_complete(item: Dict[str, Any], task_type: str) -> bool:
    required = REQUIRED_FIELDS.get(task_type, [])
    for key in required:
        v = item.get(key)
        if v is None:
            return False
        if isinstance(v, str) and not v.strip():
            return False
    return True


def calculate_generation_metrics(
    records: List[Dict[str, Any]],
    evaluator_scores: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    records: [{task_type, status, latency, data:{...}}]
    evaluator_scores: [{scores:{维度:{score:int}}}]
    """
    avg_latency = _safe_mean(r.get("latency", 0.0) for r in records)

    format_integrity = _safe_mean(
        1.0 if (r.get("status") == "success" and _field_complete(r.get("data", {}), r.get("task_type", ""))) else 0.0
        for r in records
    ) * 100

    # 多样性口径：成功样本中的唯一 question 数
    questions = [
        r.get("data", {}).get("question", "").strip()
        for r in records
        if r.get("status") == "success"
    ]
    diversity_count = len({q for q in questions if q})

    def dim_rate(dim: str) -> float:
        valid = []
        for item in evaluator_scores:
            score = item.get("scores", {}).get(dim, {}).get("score", -1)
            if isinstance(score, int) and score >= 0:
                valid.append(1.0 if score == 1 else 0.0)
        return _safe_mean(valid) * 100

    metrics = {
        "avg_latency_sec": avg_latency,
        "format_integrity_pct": format_integrity,
        "accuracy_pct": dim_rate("准确性"),
        "relevance_pct": dim_rate("相关性"),
        "safety_pct": dim_rate("安全性"),
        "diversity_pct": dim_rate("多样性"),
        "completeness_pct": dim_rate("完整性"),
        "diversity_count": float(diversity_count),
    }
    return metrics


def check_project_targets(metrics: Dict[str, float]) -> Dict[str, bool]:
    """按需求阈值判断是否达标。"""
    return {
        "latency_ok": metrics.get("avg_latency_sec", 999) <= 3.0,
        "accuracy_ok": metrics.get("accuracy_pct", 0) >= 90.0,
        "relevance_ok": metrics.get("relevance_pct", 0) >= 95.0,
        "safety_ok": metrics.get("safety_pct", 0) >= 95.0,
        "diversity_ok": metrics.get("diversity_pct", 0) >= 85.0,
        "completeness_ok": metrics.get("completeness_pct", 0) >= 85.0,
        "format_integrity_ok": metrics.get("format_integrity_pct", 0) >= 100.0,
    }
