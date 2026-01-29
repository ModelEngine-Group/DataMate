"""
QA生成模块 - 根据数据生成问答对
"""

import json
import random
from typing import Dict, List, Any


def generate_qa_pairs(data):
    """
    核心逻辑：根据输入数据随机生成问答对列表。

    Args:
        data: 纳税记录数据字典

    Returns:
        问答对列表
    """
    qa_list = []

    # --- 第一轮对话：文档类型识别 ---
    qa_list.append({"role": "usr", "content": "<image>\n这是什么类型的文档？"})
    qa_list.append({"role": "assistant", "content": f"这是一份{data['文件名称']}。"})

    # --- 定义可随机抽取的问题库 ---
    questions = [
        {
            "prompt": "这份证明是给哪位纳税人开具的？",
            "answer": f"纳税人姓名是：{data['纳税人姓名']}。"
        },
        {
            "prompt": "纳税人的身份证件类型和号码是什么？",
            "answer": f"证件类型是{data['纳税人身份证照类型']}，号码是{data['纳税人身份号码']}。"
        },
        {
            "prompt": "凭证编码和填发日期分别是多少？",
            "answer": f"凭证编码：{data['凭证编码']}，填发日期：{data['填发日期'].replace('填发日期：', '')}。"
        },
        {
            "prompt": "这份证明是关于哪一年的纳税情况？",
            "answer": "这是年终为纳税人开具的全年纳税情况证明。"
        },
        {
            "prompt": "请列出所有的纳税项目。",
            "answer": "纳税项目包括：" + ", ".join([item['item'] for item in data['纳税项目']]) + "。"
        },
        {
            "prompt": "税款金额合计是多少？",
            "answer": f"税款金额合计（小写）：{data['税款金额合计（小写）']}元，大写：{data['税款金额合计（大写）']}。"
        },
        {
            "prompt": "工资、薪金所得小计是多少？",
            "answer": f"工资、薪金所得小计为：{data['工资、薪金所得小计']}元。"
        },
        {
            "prompt": "劳务报酬所得是多少？",
            "answer": f"劳务报酬所得为：{data['劳务报酬所得']}元。"
        },
        {
            "prompt": "稿酬所得是多少？",
            "answer": f"稿酬所得为：{data['稿酬所得']}元。"
        }
    ]

    # --- 随机抽取问题 ---
    selected_questions = random.sample(questions, min(8, len(questions)))
    for qa in selected_questions:
        qa_list.append({"role": "usr", "content": qa["prompt"]})
        qa_list.append({"role": "assistant", "content": qa["answer"]})

    # --- 最后一轮强制对话：JSON格式提取 ---
    qa_list.append({"role": "usr", "content": "请提取所有关键信息，以严格的JSON格式输出，不要包含额外的文本。"})

    # 构建要输出的JSON内容
    json_output = {
        "文件名称": data["文件名称"],
        "纳税人姓名": data["纳税人姓名"],
        "纳税人身份证照类型": data["纳税人身份证照类型"],
        "纳税人身份号码": data["纳税人身份号码"],
        "凭证编码": data["凭证编码"],
        "填发日期": data["填发日期"].replace('填发日期：', ''),
        "纳税项目": [
            {
                "项目": item["item"],
                "期间": item["period"],
                "金额": item["amount"]
            } for item in data["纳税项目"]
        ],
        "税款金额合计（小写）": data["税款金额合计（小写）"],
        "税款金额合计（大写）": data["税款金额合计（大写）"]
    }
    qa_list.append({"role": "assistant", "content": json.dumps(json_output, ensure_ascii=False)})

    return qa_list


def create_jsonl_record(image_name, messages):
    """
    创建JSONL格式的单条记录

    Args:
        image_name: 图片文件名
        messages: 消息列表

    Returns:
        JSONL记录
    """
    return {
        "image": image_name,
        "messages": messages
    }


def match_data_with_images(data_files, image_dir):
    """
    匹配数据文件与图片文件

    Args:
        data_files: 数据文件列表
        image_dir: 图片目录路径

    Returns:
        匹配后的列表，每个元素包含 (data_file, image_files)
    """
    matched_pairs = []

    for data_file in data_files:
        base_name = data_file.stem  # 去除.json后缀

        # 查找所有以该base_name开头的图片
        related_images = []
        for img_file in data_file.parent.parent.joinpath(image_dir).glob(f"{base_name}*"):
            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                related_images.append(img_file)

        matched_pairs.append((data_file, related_images))

    return matched_pairs


class QAGenerator:
    """QA生成器 - 生成多模态VL模型训练用的问答对"""

    def __init__(self, random_questions: int = 8):
        """
        初始化QA生成器

        Args:
            random_questions: 每个数据随机生成的问题数量
        """
        self.random_questions = random_questions

    def generate_batch(self, data_files, image_dir, output_file):
        """
        批量生成QA对并输出为JSONL格式

        Args:
            data_files: 数据文件列表
            image_dir: 图片目录路径
            output_file: 输出JSONL文件路径
        """
        # 匹配数据与图片
        matched_pairs = match_data_with_images(data_files, image_dir)

        # 生成JSONL记录
        jsonl_records = []
        total_records = 0

        for data_file, image_files in matched_pairs:
            try:
                # 加载数据
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 为每个相关图片生成QA对
                for img_file in image_files:
                    # 生成QA对
                    messages = generate_qa_pairs(data)

                    # 创建JSONL记录
                    record = create_jsonl_record(img_file.name, messages)
                    jsonl_records.append(record)
                    total_records += 1

                    print(f"✅ 生成记录: {data_file.stem} -> {img_file.name}")

            except Exception as e:
                print(f"❌ 处理 {data_file} 时出错: {e}")
                continue

        # 写入JSONL文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in jsonl_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        print(f"\n🎉 成功生成 {total_records} 条JSONL记录")
        print(f"📁 输出文件: {output_file}")

        return total_records


if __name__ == "__main__":
    # 测试代码
    from pathlib import Path

    # 创建测试数据
    test_data = {
        "文件名称": "个人所得税完税证明",
        "纳税人姓名": "张三",
        "纳税人身份证照类型": "居民身份证",
        "纳税人身份号码": "11010119******1234",
        "凭证编码": "(2025)市区个证100号",
        "填发日期": "填发日期：2025年01月25日",
        "纳税项目": [
            {"item": "工资、薪金所得小计", "period": "2024年01月", "amount": "15700.00"},
            {"item": "劳务报酬所得", "period": "2024年06月", "amount": "2400.00"},
            {"item": "稿酬所得", "period": "2024年09月", "amount": "800.00"}
        ],
        "工资、薪金所得小计": "15700.00",
        "劳务报酬所得": "2400.00",
        "稿酬所得": "800.00",
        "税款金额合计（小写）": "18900.00",
        "税款金额合计（大写）": "壹万捌仟玖佰元整"
    }

    # 测试生成QA对
    qa_pairs = generate_qa_pairs(test_data)

    print("=" * 60)
    print("测试：生成QA对")
    print("=" * 60)

    for i, qa in enumerate(qa_pairs):
        role = qa["role"]
        if role == "usr":
            print(f"\n问题 {i//2 + 1}:")
            print(f"  {qa['content']}")
        else:
            print(f"回答:")
            print(f"  {qa['content']}")

    print("\n" + "=" * 60)
    print("测试：创建JSONL记录")
    print("=" * 60)

    record = create_jsonl_record("test.jpg", qa_pairs)
    print(json.dumps(record, ensure_ascii=False, indent=2))
