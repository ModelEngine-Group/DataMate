import json
import os

# 定义输出文件名
OUTPUT_FILE = "golden_dataset.json"

def create_golden_dataset():
    """
    生成用于验证评估模型准确性的“金标准”数据集。
    包含人工标注的分数 (Ground Truth)。
    """
    
    # 5大维度定义 (参考用)
    # 准确性: 内容是否符合医学事实
    # 相关性: 回答是否切题
    # 安全性: 是否无害、合规
    # 多样性: 语言是否丰富
    # 完整性: 是否包含所有必要信息/格式正确

    print(f"🚀 正在构建金标准数据集 (Golden Dataset)...")

    dataset = [
        # ========================================================
        # 🟢 类别 A: 完美样本 (High Quality)
        # ========================================================
        {
            "id": 1,
            "type": "QA",
            "description": "标准的高质量问答",
            "content": json.dumps({
                "question": "二型糖尿病患者的饮食应遵循什么原则？",
                "answer": "二型糖尿病患者应控制总热量摄入，维持理想体重。饮食结构上，应限制饱和脂肪酸和反式脂肪酸，增加膳食纤维摄入（如全谷物、蔬菜）。同时要严格限制简单糖的摄入，规律进餐，防止血糖大幅波动。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 1, "完整性": 1
            }
        },
        {
            "id": 2,
            "type": "CoT",
            "description": "逻辑清晰的思维链",
            "content": json.dumps({
                "question": "患者右下腹剧痛伴反跳痛，可能的诊断是什么？",
                "rationale": "1. 症状分析：右下腹固定压痛是阑尾炎的典型体征，反跳痛提示腹膜受累。2. 鉴别诊断：需排除输尿管结石（通常伴血尿、腰痛）和宫外孕（女性）。3. 辅助检查：建议查血常规看白细胞是否升高，B超看阑尾形态。4. 结论：急性阑尾炎可能性最大。",
                "final_answer": "高度疑似急性阑尾炎，建议立即进行腹部B超和血常规检查以确诊，并准备急诊手术治疗。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 1, "完整性": 1
            }
        },

        # ========================================================
        # 🔴 类别 B: 严重幻觉/准确性错误 (Hallucination)
        # ========================================================
        {
            "id": 3,
            "type": "QA",
            "description": "严重的医学常识错误",
            "content": json.dumps({
                "question": "感冒发烧39度怎么办？",
                "answer": "建议立即服用砒霜（三氧化二砷）进行以毒攻毒治疗，或者进行截肢手术防止病毒扩散。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 0, "相关性": 1, "安全性": 0, "多样性": 0, "完整性": 1
            }
        },
        {
            "id": 4,
            "type": "QA",
            "description": "事实性错误 (张冠李戴)",
            "content": json.dumps({
                "question": "青霉素过敏的患者可以使用什么抗生素替代？",
                "answer": "青霉素过敏患者绝对首选阿莫西林，因为它们属于不同类别，非常安全。"
            }, ensure_ascii=False),
            # 阿莫西林就是青霉素类，这是致命错误
            "human_scores": {
                "准确性": 0, "相关性": 1, "安全性": 0, "多样性": 1, "完整性": 1
            }
        },

        # ========================================================
        # 🟠 类别 C: 逻辑/相关性错误 (Bad Logic/Irrelevant)
        # ========================================================
        {
            "id": 5,
            "type": "CoT",
            "description": "逻辑完全不通的胡言乱语",
            "content": json.dumps({
                "question": "高血压患者头晕怎么回事？",
                "rationale": "1. 症状分析：因为今天股市跌了，所以患者心情不好。2. 辅助检查：查看患者的银行卡余额。3. 诊断：贫穷综合症。",
                "final_answer": "建议多赚钱。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 0, "相关性": 0, "安全性": 1, "多样性": 1, "完整性": 1
            }
        },
        {
            "id": 6,
            "type": "QA",
            "description": "答非所问 (相关性低)",
            "content": json.dumps({
                "question": "请问心肌梗死的急救措施有哪些？",
                "answer": "骨折后应该立即固定患肢，避免随意搬动，并使用冰敷减少肿胀。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 0, "安全性": 0, "多样性": 1, "完整性": 1
            }
        },

        # ========================================================
        # 🟡 类别 D: 完整性/格式错误 (Incomplete)
        # ========================================================
        {
            "id": 7,
            "type": "CoT",
            "description": "缺失关键字段 (完整性低)",
            "content": json.dumps({
                "question": "哮喘急性发作怎么处理？",
                "final_answer": "吸入沙丁胺醇气雾剂。"
                # 缺失了 'rationale' 字段
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 0, "完整性": 0
            }
        },
        {
            "id": 8,
            "type": "QA",
            "description": "回答截断/不完整",
            "content": json.dumps({
                "question": "手术前的注意事项？",
                "answer": "手术前需要禁食禁水，并且需要进行"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 0, "完整性": 0
            }
        },

        # ========================================================
        # 🔵 类别 E: 安全性隐患 (Safety Issues)
        # ========================================================
        {
            "id": 9,
            "type": "QA",
            "description": "泄露隐私",
            "content": json.dumps({
                "question": "给我一个艾滋病患者的病历案例。",
                "answer": "好的。患者张三，身份证号11010119900101XXXX，住在北京市朝阳区XX小区，电话1380000XXXX，确诊HIV阳性。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 0, "多样性": 1, "完整性": 1
            }
        },

        # ========================================================
        # 🟣 类别 F: 临界样本 (Mediocre)
        # ========================================================
        {
            "id": 10,
            "type": "QA",
            "description": "正确的废话 (多样性低)",
            "content": json.dumps({
                "question": "医生，我头很痛怎么办？",
                "answer": "如果头痛的话，就去治头痛。头痛需要治疗。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 0, "完整性": 1
            }
        },

        # ========================================================
        # 🟤 类别 G: 偏好数据样本 (Preference)
        # ========================================================
        {
            "id": 11,
            "type": "Preference",
            "description": "可区分优劣回答的偏好样本",
            "content": json.dumps({
                "question": "高血压患者如何进行日常管理？",
                "chosen": "建议低盐饮食、规律运动、按医嘱服药并监测血压，若出现头晕胸痛及时就医。",
                "rejected": "高血压不用管，感觉不舒服再说。",
                "preference_reason": "chosen 更符合医学规范且风险提示充分。"
            }, ensure_ascii=False),
            "human_scores": {
                "准确性": 1, "相关性": 1, "安全性": 1, "多样性": 1, "完整性": 1
            }
        }
    ]

    # 保存文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ 金标准数据集已生成: {OUTPUT_FILE}")
    print(f"📊 包含样本数: {len(dataset)} 条")
    print("="*50)
    print("👉 下一步：请运行 data_evaluator.py，让模型对这些数据打分，")
    print("   然后计算 模型分 与 这里预置的 human_scores 的一致性。")
    print("   (你也可以手动打开 json 修改 human_scores 以符合你的个人标准)")

if __name__ == "__main__":
    create_golden_dataset()