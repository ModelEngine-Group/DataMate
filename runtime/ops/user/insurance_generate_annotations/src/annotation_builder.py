import os
import json
import pandas as pd
import random
import logging
from pathlib import Path

# ======================== 配置 ========================
INPUT_DIR = "../output/data"
OUTPUT_DIR = "../output/images/augmented"
CSV_FILE = "data.csv"
QA_CLASSIFICATION_FILE = "qa_classification.json"
QA_EXTRACTION_FILE = "qa_extraction.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# 固定分类问答配置
FIXED_CLASSIFICATION_QUESTION = "<image>\n图片是什么类别"
FIXED_CLASSIFICATION_ANSWER = "社会保险参保证明"


def load_csv_data(csv_path):
    """加载CSV数据"""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logger.info(f"✅ 成功加载CSV文件: {csv_path}, 共 {len(df)} 行数据")
        return df
    except Exception as e:
        logger.error(f"❌ 加载CSV文件失败: {e}")
        return None


def get_image_files(directory):
    """获取目录中所有的图片文件"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    image_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)

    logger.info(f"📁 找到 {len(image_files)} 个图片文件")
    return image_files


def generate_classification_qa(image_files):
    """生成分类QA对"""
    qa_list = []

    for img_name in image_files:
        img_path = f"./images/{img_name}"

        qa_item = {
            "images": [img_path],
            "messages": [
                {
                    "role": "user",
                    "content": FIXED_CLASSIFICATION_QUESTION
                },
                {
                    "role": "assistant",
                    "content": FIXED_CLASSIFICATION_ANSWER
                }
            ]
        }
        qa_list.append(qa_item)

    return qa_list


def generate_questions_and_answers(row_data):
    """根据一行数据生成3个问题和答案"""
    name = str(row_data.get('姓名', ''))
    gender = str(row_data.get('性别', ''))
    id_number = str(row_data.get('证件号码', ''))
    id_type = str(row_data.get('证件类型', ''))
    insurance_period = str(row_data.get('参保起止时间', ''))
    company = str(row_data.get('单位', ''))
    yanglao = str(row_data.get('养老', ''))
    gongshang = str(row_data.get('工伤', ''))
    shiyue = str(row_data.get('失业', ''))
    province = str(row_data.get('省份名', ''))
    proof_date = str(row_data.get('证明日期', ''))

    question_templates = [
        ("缴纳公司是什么", f"**{company}**"),
        ("证件类型和号码分别是什么", f"{id_type} {id_number}"),
        ("参保起止时间是什么时候", f"**{insurance_period}**"),
        ("性别是什么", f"**{gender}**"),
        ("养老、工伤、失业保险状态", f"养老：{yanglao}，工伤：{gongshang}，失业：{shiyue}"),
        ("省份是哪里", f"**{province}**"),
        ("证明日期是什么", f"**{proof_date}**"),
        ("姓名是什么", f"**{name}**"),
        ("证件号码是多少", f"**{id_number}**"),
        ("单位名称是什么", f"**{company}**")
    ]

    selected_qa = random.sample(question_templates, min(3, len(question_templates)))

    return selected_qa


def create_extraction_qa_json(image_files, csv_df):
    """创建信息提取QA JSON文件"""
    qa_list = []

    for image_file in image_files:
        image_filename = image_file
        logger.info(f"🔍 处理图片: {image_file}，开始匹配CSV中的姓名...")

        matched = False

        for idx, row in csv_df.iterrows():
            name = str(row['姓名']).strip()
            if not name:
                continue

            if name in image_filename:
                row_data = row.to_dict()
                logger.info(f"✅ 匹配成功：图片 {image_file} 包含姓名 {name}")

                qa_pairs = generate_questions_and_answers(row_data)

                messages = []
                for question, answer in qa_pairs:
                    user_message = {
                        "role": "user",
                        "content": f"<image>\n{question}"
                    }
                    messages.append(user_message)

                    assistant_message = {
                        "role": "assistant",
                        "content": answer
                    }
                    messages.append(assistant_message)

                qa_item = {
                    "images": [f"./images/{image_file}"],
                    "messages": messages
                }

                qa_list.append(qa_item)
                logger.info(f"✅ 已为图片 {image_file} 生成 {len(qa_pairs)} 个问题-答案对")
                matched = True
                break

        if not matched:
            logger.warning(f"⚠️  未找到包含图片名称的姓名数据: {image_file}")

    return qa_list


def generate_annotations(qa_type="all", input_dir=INPUT_DIR, output_dir=OUTPUT_DIR):
    """生成所有类型的QA对"""
    # 检查CSV文件
    csv_path = os.path.join(input_dir, CSV_FILE)
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV文件不存在: {csv_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"📁 创建输出目录: {output_dir}")

    # 获取图片文件列表
    image_files = get_image_files(input_dir + "/images")
    if not image_files:
        logger.warning(f"⚠️  在 {input_dir} 中未找到图片文件")
        return

    results = {}

    # 生成分类QA对
    if qa_type in ["classification", "all"]:
        logger.info("🔄 正在生成分类QA对...")
        classification_qa = generate_classification_qa(image_files)

        output_json_path = os.path.join(output_dir, QA_CLASSIFICATION_FILE)
        try:
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(classification_qa, f, ensure_ascii=False, indent=4)
            logger.info(f"✅ 分类QA对JSON文件已保存: {output_json_path}")
            logger.info(f"📊 共生成 {len(classification_qa)} 个分类QA对")
            results["classification"] = output_json_path
        except Exception as e:
            logger.error(f"❌ 保存分类QA JSON文件失败: {e}")

    # 生成信息提取QA对
    if qa_type in ["extraction", "all"]:
        csv_df = load_csv_data(csv_path)
        if csv_df is None:
            return

        logger.info("🔄 正在生成信息提取QA对...")
        extraction_qa = create_extraction_qa_json(image_files, csv_df)

        if extraction_qa:
            output_json_path = os.path.join(output_dir, QA_EXTRACTION_FILE)
            try:
                with open(output_json_path, 'w', encoding='utf-8') as f:
                    json.dump(extraction_qa, f, ensure_ascii=False, indent=4)
                logger.info(f"✅ 信息提取QA对JSON文件已保存: {output_json_path}")
                logger.info(f"📊 共生成 {len(extraction_qa)} 个信息提取QA对")
                results["extraction"] = output_json_path
            except Exception as e:
                logger.error(f"❌ 保存信息提取QA JSON文件失败: {e}")
        else:
            logger.warning("⚠️  未生成任何信息提取QA对，请检查图片名称与CSV数据的匹配情况")

    return
