import json
from data_evaluator import MedicalDataEvaluator

# 配置
MODEL_PATH = "/data/models/Qwen/Qwen2.5-7B-Instruct"
GOLDEN_DATA_PATH = "golden_dataset.json"

def calculate_metrics(eval_results, golden_data):
    total_checks = 0
    passed_checks = 0
    
    details = []

    print("\n" + "="*60)
    print(f"{'ID':<4} | {'维度':<6} | {'人工分':<6} | {'模型分':<6} | {'判定':<10} | {'理由片段'}")
    print("-" * 60)

    for i, res in enumerate(eval_results):
        golden_item = golden_data[i]
        human_scores = golden_item['human_scores']
        model_scores = res['scores']
        
        for dim, h_score in human_scores.items():
            if dim not in model_scores: continue
            
            m_score_obj = model_scores[dim]
            m_score = m_score_obj['score']
            reason = m_score_obj['reason']
            
            # 过滤掉解析失败的情况
            if m_score == -1:
                print(f"⚠️ ID {golden_item['id']} {dim} 解析失败")
                continue

            total_checks += 1
            diff = abs(m_score - h_score)
            
            # 二值判定（0/1），按精确一致统计
            is_match = (diff == 0)
            if is_match:
                passed_checks += 1
            
            status = "✅ PASS" if is_match else "❌ FAIL"
            
            print(f"{golden_item['id']:<4} | {dim:<6} | {h_score:<6} | {m_score:<6} | {status:<10} | {reason[:20]}...")
            
            details.append({
                "id": golden_item['id'],
                "dimension": dim,
                "human": h_score,
                "model": m_score,
                "pass": is_match
            })

    accuracy = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    return accuracy, details

def main():
    # 1. 加载金标准数据
    try:
        with open(GOLDEN_DATA_PATH, 'r') as f:
            golden_data = json.load(f)
        print(f"📂 已加载金标准数据: {len(golden_data)} 条")
    except FileNotFoundError:
        print("❌ 未找到 golden_dataset.json，请先运行 prepare_golden_data.py")
        return

    # 2. 初始化评估器
    evaluator = MedicalDataEvaluator(MODEL_PATH)
    
    # 3. 运行评估
    # 我们只评测金标准中包含的维度
    # 为了简化，我们让评估器跑完所有维度，后续只取需要的
    print("🧠 正在进行模型打分...")
    eval_results = evaluator.evaluate(golden_data)
    
    # 4. 计算一致性指标
    acc, _ = calculate_metrics(eval_results, golden_data)

    # 按需求口径：5维度、二值准确率
    requirement_acc = MedicalDataEvaluator.summarize_accuracy(
        eval_results,
        golden_data,
        ignore_dimensions=(),
        allowed_error=0,
    )
    
    # 5. 输出验收结论
    print("\n" + "="*60)
    print("🏆 评估模型验收报告 (Evaluation Model Acceptance Report)")
    print("="*60)
    print(f"1. 总评测维度点: {len(_) }")
    print(f"2. 二值准确率(0/1, 精确一致): {acc:.1f}%")
    print(f"3. 需求口径准确率(5维): {requirement_acc['accuracy']:.1f}%")
    print("-" * 60)
    
    target = 90.0
    if acc >= target:
        print(f"✅ 结果: 通过 (>{target}%)")
        print("🎉 你的评估模型（裁判）非常可靠！")
    else:
        print(f"⚠️ 结果: 未通过 (<{target}%)")
        print("💡 建议：微调 data_evaluator.py 中的 Prompt 标准，或检查金标准分数是否合理。")

    if requirement_acc["accuracy"] >= target:
        print("✅ 需求口径准确率达标 (>90%)")
    else:
        print("⚠️ 需求口径准确率未达标 (<=90%)")

if __name__ == "__main__":
    main()