import os
import time
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict

# 引入核心合成引擎
from data_synthesizer import MedicalDataSynthesizer

# ==========================================
# 配置区域
# ==========================================
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
    return os.getenv("MODEL_PATH") or "/work/.cache/modelscope/testUser/Qwen3-1___7b-Medical-R1-sft"


MODEL_PATH = resolve_model_path()
TEST_SAMPLE_COUNT = 100  # 测试样本总数 (50 QA + 50 CoT)
OUTPUT_BASE_DIR = "outputs"
TASK_RATIO = {"QA": 0.4, "CoT": 0.4, "Preference": 0.2}
SOURCE_MIX_RATIO = {"original": 0.4, "augmented": 0.4, "distilled": 0.2}

# ==========================================
# 工具函数
# ==========================================
def generate_mock_inputs(num_samples=50):
    """生成模拟病历输入"""
    symptoms = ["持续性干咳", "右上腹剧痛", "胸闷气短", "双下肢水肿", "突发言语不清", "高热寒战", "关节红肿痛", "视力模糊"]
    durations = ["3天", "2周", "5小时", "反复发作1年", "晨起加重"]
    demographics = ["男性，45岁", "女性，65岁", "患儿，5岁", "老年男性，78岁", "孕妇，28岁"]
    findings = ["白细胞升高", "CT示斑片影", "B超示结石", "心电图ST段抬高", "MRI示脑梗死", "尿蛋白+++"]
    
    return [f"{random.choice(demographics)}。主诉：{random.choice(symptoms)}{random.choice(durations)}。查体及辅助检查：{random.choice(findings)}。" for _ in range(num_samples)]

def setup_output_dir():
    """创建带时间戳的输出目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = os.path.join(OUTPUT_BASE_DIR, timestamp)
    os.makedirs(dir_path, exist_ok=True)
    print(f"📂 [System] 输出目录已创建: {dir_path}")
    return dir_path

def save_json(data: List, filepath: str):
    """保存数据为 JSON 格式"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 [File] 已保存: {filepath} ({len(data)} 条)")

def visualize_report(df: pd.DataFrame, save_path: str):
    """生成专业的可视化验收报告"""
    plt.switch_backend('agg') # Docker 环境必备
    
    # 设置画布风格
    plt.style.use('ggplot')
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Ascend 910B Data Synthesis Acceptance Report\nTotal Samples: {len(df)}', fontsize=16)

    # 1. 延迟对比图 (Bar Chart)
    qa_lat = df[df['task_type']=='QA']['latency'].mean()
    cot_lat = df[df['task_type']=='CoT']['latency'].mean()
    
    bars = axs[0, 0].bar(['QA', 'CoT'], [qa_lat, cot_lat], color=['#3498db', '#e67e22'])
    axs[0, 0].axhline(y=3.0, color='red', linestyle='--', linewidth=2, label='Max Limit (3s)')
    axs[0, 0].set_title('Average Latency (Batch Mode)')
    axs[0, 0].set_ylabel('Seconds per Item')
    axs[0, 0].legend()
    # 在柱子上标数值
    for bar in bars:
        height = bar.get_height()
        axs[0, 0].text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s', ha='center', va='bottom')

    # 2. 成功率 (Pie Chart)
    status_counts = df['status'].value_counts()
    colors = ['#2ecc71', '#e74c3c'] if 'failed' in status_counts else ['#2ecc71']
    axs[0, 1].pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', 
                  colors=colors, startangle=90, explode=[0.1]*len(status_counts))
    axs[0, 1].set_title('Data Format Integrity')

    # 3. 延迟分布直方图 (Histogram)
    axs[1, 0].hist(df['latency'], bins=20, color='#9b59b6', alpha=0.7, edgecolor='white')
    axs[1, 0].set_title('Latency Distribution')
    axs[1, 0].set_xlabel('Latency (s)')
    axs[1, 0].set_ylabel('Count')

    # 4. 任务详情表 (Table)
    cell_text = [
        ["Model", "Qwen2.5-7B-Instruct"],
        ["Hardware", "Ascend 910B + 32G RAM"],
        ["Inference", "vLLM (Ascend) + Batching"],
        ["Total QA", len(df[df['task_type']=='QA'])],
        ["Total CoT", len(df[df['task_type']=='CoT'])],
        ["Pass Rate", f"{(df['status']=='success').mean()*100:.1f}%"]
    ]
    axs[1, 1].axis('tight')
    axs[1, 1].axis('off')
    table = axs[1, 1].table(cellText=cell_text, loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)
    axs[1, 1].set_title('Test Environment & Stats')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"📊 [Plot] 可视化报告已保存: {save_path}")

# ==========================================
# 主逻辑
# ==========================================
def main():
    # 1. 准备环境
    output_dir = setup_output_dir()
    synthesizer = MedicalDataSynthesizer(MODEL_PATH)
    
    # 2. 生成模拟输入并执行“原始/增强/蒸馏”配比
    total_inputs = generate_mock_inputs(TEST_SAMPLE_COUNT)
    mixed_pool = synthesizer.build_training_corpus(
        raw_inputs=total_inputs,
        target_size=TEST_SAMPLE_COUNT,
        source_ratio=SOURCE_MIX_RATIO,
        seed=42,
    )
    mixed_texts = [x["text"] for x in mixed_pool]

    qa_cnt = int(TEST_SAMPLE_COUNT * TASK_RATIO["QA"])
    cot_cnt = int(TEST_SAMPLE_COUNT * TASK_RATIO["CoT"])
    pref_cnt = TEST_SAMPLE_COUNT - qa_cnt - cot_cnt

    qa_inputs = mixed_texts[:qa_cnt]
    cot_inputs = mixed_texts[qa_cnt: qa_cnt + cot_cnt]
    pref_inputs = mixed_texts[qa_cnt + cot_cnt: qa_cnt + cot_cnt + pref_cnt]
    
    metrics_data = [] # 用于记录 CSV 指标
    
    print("\n" + "="*50)
    print(f"🚀 开始验收测试 (Batch Mode)")
    print(f"🎯 目标: 生成 {TEST_SAMPLE_COUNT} 条数据并归档 (QA/CoT/Preference)")
    print("="*50)

    task_inputs = {
        "QA": qa_inputs,
        "CoT": cot_inputs,
        "Preference": pref_inputs,
    }

    task_latencies = {}
    success_payload = {"QA": [], "CoT": [], "Preference": []}

    for task_type, task_items in task_inputs.items():
        print(f"Processing {len(task_items)} {task_type} items...")
        t_start = time.time()
        outputs = synthesizer.generate_data_batch(task_type, task_items)
        t_end = time.time()

        per_item_latency = (t_end - t_start) / max(len(task_items), 1)
        task_latencies[task_type] = per_item_latency

        for res in outputs:
            metrics_data.append({
                "task_type": task_type,
                "latency": per_item_latency,
                "status": res['status'],
                "raw_text_len": len(str(res.get('data', ''))),
                "data": res.get("data", {}),
            })
            if res['status'] == 'success':
                success_payload[task_type].append(res['data'])

    # ==========================================
    # 3. 保存交付件 (Artifacts)
    # ==========================================
    print("\n📦 [System] 正在保存交付件...")
    
    # 保存 1: 生成的数据文件 (JSON)
    save_json(success_payload["QA"], os.path.join(output_dir, "generated_qa.json"))
    save_json(success_payload["CoT"], os.path.join(output_dir, "generated_cot.json"))
    save_json(success_payload["Preference"], os.path.join(output_dir, "generated_preference.json"))
    
    # 保存 2: 原始指标 (CSV)
    df = pd.DataFrame(metrics_data)
    csv_path = os.path.join(output_dir, "benchmark_metrics.csv")
    df.to_csv(csv_path, index=False)
    print(f"💾 [File] 指标数据已保存: {csv_path}")
    
    # 保存 3: 可视化报告 (PNG)
    png_path = os.path.join(output_dir, "visual_report.png")
    visualize_report(df, png_path)
    
    # 保存 4: 汇总摘要 (JSON)
    summary = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_PATH,
        "total_samples": len(df),
        "task_ratio": TASK_RATIO,
        "source_mix_ratio": SOURCE_MIX_RATIO,
        "success_rate": float((df['status']=='success').mean()),
        "avg_latency_qa": task_latencies.get("QA", 0.0),
        "avg_latency_cot": task_latencies.get("CoT", 0.0),
        "avg_latency_preference": task_latencies.get("Preference", 0.0),
        "overall_latency": float(df['latency'].mean()),
        "passed_acceptance": bool(df['latency'].mean() <= 3.0 and (df['status']=='success').mean() >= 0.98)
    }
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*50)
    print("✅ 第一阶段交付流程执行完毕")
    print(f"📂 所有文件已保存在: {output_dir}")
    print("="*50)

if __name__ == "__main__":
    main()