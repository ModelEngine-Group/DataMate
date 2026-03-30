import json
import os
import random
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from data_synthesizer import MedicalDataSynthesizer


NUM_PER_TASK = 50
BATCH_SIZE = {
    "QA": 50,          # 限时任务，尽量大 batch 提升吞吐
    "CoT": 10,         # CoT 允许更长，适中 batch 稳定
    "Preference": 50,  # 限时任务，尽量大 batch 提升吞吐
}


def resolve_model_path() -> str:
    candidates = [
        os.getenv("MODEL_PATH"),
        "/root/.cache/modelscope/hub/models/Qwen/Qwen3-4B",
        "/work/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft",
        "/mnt/nvme0n1/home/pjj/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft",
        "/data/models/Qwen/Qwen2.5-7B-Instruct",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError("未找到可用模型路径，请设置 MODEL_PATH 或检查本地目录。")


def generate_mock_inputs(num_samples: int = 50) -> List[str]:
    symptoms = ["持续性干咳", "右上腹剧痛", "胸闷气短", "双下肢水肿", "突发言语不清", "高热寒战", "乏力纳差", "夜间盗汗"]
    durations = ["3天", "2周", "5小时", "反复发作1年", "晨起加重", "夜间加重"]
    demographics = ["男性，45岁", "女性，65岁", "患儿，5岁", "老年男性，78岁", "孕妇，28岁"]
    findings = ["白细胞升高", "CT示斑片影", "B超示结石", "心电图ST段抬高", "MRI示脑梗死", "尿蛋白+++", "CRP升高"]

    return [
        f"{random.choice(demographics)}。主诉：{random.choice(symptoms)}{random.choice(durations)}。查体及辅助检查：{random.choice(findings)}。"
        for _ in range(num_samples)
    ]


def batched(items: List[str], batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def percentile(sorted_values: List[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def main():
    random.seed(42)

    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    model_path = resolve_model_path()
    print(f"[INFO] MODEL_PATH={model_path}")
    print(f"[INFO] OUTPUT_DIR={output_dir}")

    synth = MedicalDataSynthesizer(model_path)

    task_inputs = {
        "QA": generate_mock_inputs(NUM_PER_TASK),
        "CoT": generate_mock_inputs(NUM_PER_TASK),
        "Preference": generate_mock_inputs(NUM_PER_TASK),
    }

    all_records: List[Dict[str, Any]] = []
    task_summary: Dict[str, Dict[str, Any]] = {}

    wall_start = time.time()

    for task_type, inputs in task_inputs.items():
        bs = BATCH_SIZE[task_type]
        task_start = time.time()

        success_data = []
        failed_data = []
        latencies = []
        fallback_count = 0

        for chunk in batched(inputs, bs):
            t0 = time.time()
            outs = synth.generate_data_batch(task_type, chunk)
            t1 = time.time()

            per_item_latency = (t1 - t0) / max(len(chunk), 1)

            for inp, out in zip(chunk, outs):
                rec = {
                    "task_type": task_type,
                    "input": inp,
                    "status": out.get("status", "failed"),
                    "latency": per_item_latency,
                    "fallback": bool(out.get("fallback", False)),
                    "data": out.get("data", {}),
                    "reason": out.get("reason", ""),
                }
                all_records.append(rec)
                latencies.append(per_item_latency)

                if rec["fallback"]:
                    fallback_count += 1

                if rec["status"] == "success":
                    success_data.append(rec["data"])
                else:
                    failed_data.append({
                        "input": inp,
                        "reason": out.get("reason", ""),
                        "raw_output": out.get("raw_output", ""),
                    })

        task_end = time.time()
        total = len(latencies)
        success = len(success_data)
        fail = len(failed_data)
        success_rate = (success / total) if total else 0.0

        sorted_lat = sorted(latencies)
        avg_lat = statistics.mean(latencies) if latencies else 0.0
        p50 = percentile(sorted_lat, 0.50)
        p95 = percentile(sorted_lat, 0.95)

        task_summary[task_type] = {
            "batch_size": bs,
            "total": total,
            "success": success,
            "failed": fail,
            "success_rate": success_rate,
            "fallback_count": fallback_count,
            "avg_latency_sec": avg_lat,
            "p50_latency_sec": p50,
            "p95_latency_sec": p95,
            "task_elapsed_sec": task_end - task_start,
            "throughput_item_per_sec": (total / (task_end - task_start)) if (task_end - task_start) > 0 else 0.0,
            # 时延要求：仅 QA/Preference 约束 <=3s
            "latency_requirement_pass": (avg_lat <= 3.0) if task_type in {"QA", "Preference"} else True,
        }

        (output_dir / f"generated_{task_type.lower()}.json").write_text(
            json.dumps(success_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output_dir / f"failed_{task_type.lower()}.json").write_text(
            json.dumps(failed_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    wall_end = time.time()

    overall_lat = [x["latency"] for x in all_records]
    overall_success = sum(1 for x in all_records if x["status"] == "success")
    overall_total = len(all_records)

    overall_summary = {
        "run_id": run_id,
        "model_path": model_path,
        "output_dir": str(output_dir),
        "num_per_task": NUM_PER_TASK,
        "batch_size": BATCH_SIZE,
        "overall_total": overall_total,
        "overall_success": overall_success,
        "overall_failed": overall_total - overall_success,
        "overall_success_rate": (overall_success / overall_total) if overall_total else 0.0,
        "overall_avg_latency_sec": statistics.mean(overall_lat) if overall_lat else 0.0,
        "overall_elapsed_sec": wall_end - wall_start,
        "task_summary": task_summary,
    }

    (output_dir / "summary.json").write_text(
        json.dumps(overall_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = []
    lines.append("数据合成测试结果汇总")
    lines.append("=" * 60)
    lines.append(f"运行ID: {run_id}")
    lines.append(f"模型路径: {model_path}")
    lines.append(f"输出目录: {output_dir}")
    lines.append(f"每类样本数: {NUM_PER_TASK}")
    lines.append(f"Batch策略: {BATCH_SIZE}")
    lines.append("")
    lines.append("【总体指标】")
    lines.append(f"- 总样本: {overall_total}")
    lines.append(f"- 成功样本: {overall_success}")
    lines.append(f"- 失败样本: {overall_total - overall_success}")
    lines.append(f"- 成功率: {overall_summary['overall_success_rate']:.2%}")
    lines.append(f"- 平均分摊延迟: {overall_summary['overall_avg_latency_sec']:.3f} s/条")
    lines.append(f"- 全流程耗时: {overall_summary['overall_elapsed_sec']:.2f} s")
    lines.append("")

    lines.append("【分任务指标】")
    for task in ["QA", "CoT", "Preference"]:
        ts = task_summary[task]
        lines.append(f"- {task}")
        lines.append(f"  - batch_size: {ts['batch_size']}")
        lines.append(f"  - total/success/failed: {ts['total']}/{ts['success']}/{ts['failed']}")
        lines.append(f"  - success_rate: {ts['success_rate']:.2%}")
        lines.append(f"  - fallback_count: {ts['fallback_count']}")
        lines.append(f"  - avg_latency: {ts['avg_latency_sec']:.3f} s/条")
        lines.append(f"  - p50_latency: {ts['p50_latency_sec']:.3f} s/条")
        lines.append(f"  - p95_latency: {ts['p95_latency_sec']:.3f} s/条")
        lines.append(f"  - throughput: {ts['throughput_item_per_sec']:.3f} 条/s")
        lines.append(f"  - latency_requirement_pass: {ts['latency_requirement_pass']}")

    lines.append("")
    lines.append("【时延要求判定】")
    qa_ok = task_summary["QA"]["latency_requirement_pass"]
    pref_ok = task_summary["Preference"]["latency_requirement_pass"]
    lines.append(f"- QA 平均延迟<=3s: {qa_ok}")
    lines.append(f"- Preference 平均延迟<=3s: {pref_ok}")
    lines.append("- CoT: 按需求不限制时间（本次仅报告，不判失败）")

    (output_dir / "result.txt").write_text("\n".join(lines), encoding="utf-8")

    print("[DONE] 测试完成，结果已输出到 output 目录")
    print(json.dumps(overall_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
