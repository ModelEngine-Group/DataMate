import time
import json
import random
import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
from data_synthesizer import MedicalDataSynthesizer


def resolve_model_path() -> str:
    candidates = [
        os.getenv("MODEL_PATH"),
        "/work/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft",
        "/mnt/nvme0n1/home/pjj/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft",
        "/data/models/Qwen/Qwen2.5-7B-Instruct",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    # 兜底：优先返回显式环境变量，否则返回容器默认路径
    return os.getenv("MODEL_PATH") or "/work/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft"

def generate_mock_inputs(num_samples=50):
    # (保持原样，省略以节省篇幅)
    symptoms = ["持续性干咳", "右上腹剧痛", "胸闷气短", "双下肢水肿", "突发言语不清", "高热寒战"]
    durations = ["3天", "2周", "5小时", "反复发作1年"]
    demographics = ["男性，45岁", "女性，65岁", "患儿，5岁", "老年男性，78岁"]
    return [f"{random.choice(demographics)}。主诉：{random.choice(symptoms)}{random.choice(durations)}。" for _ in range(num_samples)]

def run_benchmark(model_path, num_samples=50):
    synthesizer = MedicalDataSynthesizer(model_path)
    inputs = generate_mock_inputs(num_samples)
    
    print(f"\n🚀 开始【Batch模式】压测：共 {num_samples} 条数据...")
    
    # 混合任务：QA/CoT/Preference
    qa_cnt = int(num_samples * 0.4)
    cot_cnt = int(num_samples * 0.4)
    pref_cnt = num_samples - qa_cnt - cot_cnt

    # 小样本保护：避免出现 0 导致分母报错
    if num_samples >= 3:
        if qa_cnt == 0:
            qa_cnt = 1
            pref_cnt = max(pref_cnt - 1, 0)
        if cot_cnt == 0:
            cot_cnt = 1
            pref_cnt = max(pref_cnt - 1, 0)

    qa_inputs = inputs[:qa_cnt]
    cot_inputs = inputs[qa_cnt: qa_cnt + cot_cnt]
    pref_inputs = inputs[qa_cnt + cot_cnt: qa_cnt + cot_cnt + pref_cnt]
    
    results = []
    
    # -------------------------------------------------
    # 1. 批量运行 QA 任务
    # -------------------------------------------------
    print(f"正在并行生成 {len(qa_inputs)} 条 QA 数据...")
    start_qa = time.time()
    qa_outputs = synthesizer.generate_data_batch("QA", qa_inputs) if qa_inputs else []
    time_qa = time.time() - start_qa
    
    # 记录 QA 结果
    for res in qa_outputs:
        results.append({
            "task_type": "QA",
            "latency": time_qa / max(len(qa_inputs), 1), # 分摊延迟
            "status": res['status']
        })

    # -------------------------------------------------
    # 2. 批量运行 CoT 任务
    # -------------------------------------------------
    print(f"正在并行生成 {len(cot_inputs)} 条 CoT 数据...")
    start_cot = time.time()
    cot_outputs = synthesizer.generate_data_batch("CoT", cot_inputs) if cot_inputs else []
    time_cot = time.time() - start_cot

    # 记录 CoT 结果
    for res in cot_outputs:
        results.append({
            "task_type": "CoT",
            "latency": time_cot / max(len(cot_inputs), 1), # 分摊延迟
            "status": res['status']
        })

    # -------------------------------------------------
    # 3. 批量运行 Preference 任务
    # -------------------------------------------------
    print(f"正在并行生成 {len(pref_inputs)} 条 Preference 数据...")
    start_pref = time.time()
    pref_outputs = synthesizer.generate_data_batch("Preference", pref_inputs) if pref_inputs else []
    time_pref = time.time() - start_pref

    for res in pref_outputs:
        results.append({
            "task_type": "Preference",
            "latency": time_pref / max(len(pref_inputs), 1),
            "status": res['status']
        })

    total_time = time_qa + time_cot + time_pref
    print(f"\n✅ 压测结束！总耗时: {total_time:.2f}s")
    print(f"QA Batch 耗时: {time_qa:.2f}s (分摊: {time_qa/max(len(qa_inputs), 1):.2f}s/条)")
    print(f"CoT Batch 耗时: {time_cot:.2f}s (分摊: {time_cot/max(len(cot_inputs), 1):.2f}s/条)")
    print(f"Preference Batch 耗时: {time_pref:.2f}s (分摊: {time_pref/max(len(pref_inputs), 1):.2f}s/条)")
    
    return pd.DataFrame(results)

def visualize_results(df):
    plt.switch_backend('agg')
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Ascend 910 Data Synthesis Benchmark (Batch Mode)', fontsize=16)

    # 图1: 延迟对比
    qa_lat = df[df['task_type']=='QA']['latency'].mean()
    cot_lat = df[df['task_type']=='CoT']['latency'].mean()
    pref_lat = df[df['task_type']=='Preference']['latency'].mean()
    axs[0].bar(['QA', 'CoT', 'Preference'], [qa_lat, cot_lat, pref_lat], color=['skyblue', 'orange', 'mediumpurple'])
    axs[0].axhline(y=3.0, color='red', linestyle='--', label='Target (3s)')
    axs[0].set_title('Average Latency per Item (Batch Mode)')
    axs[0].set_ylabel('Seconds')
    axs[0].legend()

    # 图2: 成功率
    status_counts = df['status'].value_counts()
    axs[1].pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', colors=['lightgreen', 'salmon'])
    axs[1].set_title(f'Success Rate (Repetition Penalty Enabled)\nTotal: {len(df)}')

    plt.tight_layout()
    plt.savefig("benchmark_report_batch.png")
    print(f"\n📊 报告已保存至: benchmark_report_batch.png")

if __name__ == "__main__":
    MODEL_PATH = resolve_model_path()
    
    # 运行 100 条数据 (40 QA + 40 CoT + 20 Preference)
    df = run_benchmark(MODEL_PATH, num_samples=100)
    
    avg_latency = df['latency'].mean()
    success_rate = (df['status'] == 'success').mean() * 100
    
    print("\n" + "="*40)
    print("🏆 最终验收结果")
    print("="*40)
    print(f"1. 平均分摊延迟: {avg_latency:.2f} 秒/条 \t{'✅ 通过' if avg_latency <= 3 else '⚠️ 偏高'}")
    print(f"2. 数据完整性:   {success_rate:.1f}%   \t{'✅ 通过' if success_rate >= 98 else '⚠️ 需检查'}")