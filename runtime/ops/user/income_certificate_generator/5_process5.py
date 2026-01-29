#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入证明数据格式转换工具
功能：将 income-template_format.json 转换为 LLaVA 或 MLLM 格式
"""

import os
import sys
import json

from loguru import logger


def convert_to_llava_format(data_list):
    """
    转换为LLaVA格式

    Args:
        data_list: 原始数据列表

    Returns:
        list: LLaVA格式的数据列表
    """
    llava_data = []

    for record in data_list:
        # 检查是否有_id和image字段
        if '_id' not in record:
            logger.info(f"  ⚠ 跳过没有_id字段的记录")
            continue

        if 'image' not in record:
            logger.info(f"  ⚠ 跳过没有image字段的记录（ID: {record['_id']['value']}）")
            continue

        record_id = record['_id']['value']
        image_path = record['image']['value']

        logger.info(f"\n处理记录ID: {record_id}")
        logger.info(f"  图片: {image_path}")

        # 提取所有字段并构建JSON响应
        field_data = {}

        # 处理入职日期：合并年份、月份、日期
        year = record.get('年份', {}).get('value', '')
        month = record.get('月份', {}).get('value', '')
        day = record.get('日期', {}).get('value', '')

        # 如果三个字段都存在，合并为入职日期
        if year and month and day:
            field_data['入职日期'] = f"{year}-{month}-{day}"

        # 添加其他字段（除了_id、image、年份、月份、日期）
        for field_name, field_info in record.items():
            if field_name in ['_id', 'image', '年份', '月份', '日期']:
                continue
            field_data[field_name] = field_info.get('value', '')

        # 构建示例JSON（使用第一条数据作为示例）
        example_json = {}
        for key in list(field_data.keys())[:3]:  # 取前3个字段作为示例
            example_json[key] = field_data[key]

        # 创建LLaVA格式的对话
        conversation_item = {
            "id": record_id,
            "image": image_path,
            "conversations": [
                {
                    "from": "human",
                    "value": f"<image>\n请分析图片中这张收入证明中的所有关键信息，并按照Json格式返回分析结果，返回示例：{json.dumps(example_json, ensure_ascii=False)}"
                },
                {
                    "from": "gpt",
                    "value": json.dumps(field_data, ensure_ascii=False)
                }
            ]
        }

        llava_data.append(conversation_item)
        logger.info(f"  ✓ 添加记录，字段数: {len(field_data)}")

    return llava_data


def convert_to_mllm_format(data_list):
    """
    转换为MLLM格式

    Args:
        data_list: 原始数据列表

    Returns:
        list: MLLM格式的数据列表
    """
    mllm_data = []

    for record in data_list:
        # 检查是否有_id和image字段
        if '_id' not in record:
            logger.info(f"  ⚠ 跳过没有_id字段的记录")
            continue

        if 'image' not in record:
            logger.info(f"  ⚠ 跳过没有image字段的记录（ID: {record['_id']['value']}）")
            continue

        record_id = record['_id']['value']
        image_path = record['image']['value']

        logger.info(f"\n处理记录ID: {record_id}")
        logger.info(f"  图片: {image_path}")

        # 提取所有字段并构建JSON响应
        field_data = {}

        # 处理入职日期：合并年份、月份、日期
        year = record.get('年份', {}).get('value', '')
        month = record.get('月份', {}).get('value', '')
        day = record.get('日期', {}).get('value', '')

        # 如果三个字段都存在，合并为入职日期
        if year and month and day:
            field_data['入职日期'] = f"{year}-{month}-{day}"

        # 添加其他字段（除了_id、image、年份、月份、日期）
        for field_name, field_info in record.items():
            if field_name in ['_id', 'image', '年份', '月份', '日期']:
                continue
            field_data[field_name] = field_info.get('value', '')

        # 构建示例JSON（使用第一条数据作为示例）
        example_json = {}
        for key in list(field_data.keys())[:3]:  # 取前3个字段作为示例
            example_json[key] = field_data[key]

        # 创建MLLM格式的对话
        conversation_item = {
            "id": record_id,
            "image": image_path,
            "messages": [
                {
                    "role": "user",
                    "value": f"<image>\n请分析图片中这张收入证明中的所有关键信息，并按照Json格式返回分析结果，返回示例：{json.dumps(example_json, ensure_ascii=False)}"
                },
                {
                    "role": "assistant",
                    "value": json.dumps(field_data, ensure_ascii=False)
                }
            ]
        }

        mllm_data.append(conversation_item)
        logger.info(f"  ✓ 添加记录，字段数: {len(field_data)}")

    return mllm_data


def convert_data_format(input_json_path, output_folder_path, format_type='llava'):
    """
    转换数据格式

    Args:
        input_json_path: 输入JSON文件路径
        output_folder_path: 输出文件夹路径
        format_type: 格式类型 ('llava' 或 'mllm')
    """
    # 输出文件名
    if format_type == 'llava':
        output_json = os.path.join(output_folder_path, "income-template_llava_format.json")
    else:  # mllm
        output_json = os.path.join(output_folder_path, "income-template_mllm_format.json")

    logger.info("="*80)
    logger.info("收入证明数据格式转换工具")
    logger.info("="*80)
    logger.info(f"输入文件: {input_json_path}")
    logger.info(f"输出格式: {format_type.upper()}")
    logger.info(f"输出文件夹: {output_folder_path}")
    logger.info(f"输出文件: {os.path.basename(output_json)}")
    logger.info("-"*80)

    # 检查输入文件是否存在
    if not os.path.exists(input_json_path):
        logger.info(f"\n❌ 错误: 输入文件不存在 - {input_json_path}")
        sys.exit(1)

    # 读取原始数据
    logger.info(f"\n正在读取输入文件...")
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # 检查数据格式
        if isinstance(raw_data, list):
            data_list = raw_data
            logger.info(f"✓ 读取到 {len(data_list)} 条记录")
        else:
            logger.info(f"❌ 错误: JSON文件格式不正确，应该是数组格式")
            sys.exit(1)

    except json.JSONDecodeError as e:
        logger.info(f"❌ 错误: JSON文件解析失败 - {e}")
        sys.exit(1)
    except Exception as e:
        logger.info(f"❌ 错误: 读取文件失败 - {e}")
        sys.exit(1)

    # 根据格式类型进行转换
    logger.info(f"\n开始转换为 {format_type.upper()} 格式...")
    logger.info("="*80)

    if format_type == 'llava':
        converted_data = convert_to_llava_format(data_list)
    elif format_type == 'mllm':
        converted_data = convert_to_mllm_format(data_list)
    else:
        logger.info(f"❌ 错误: 不支持的格式类型 '{format_type}'")
        sys.exit(1)

    # 保存转换后的数据
    print(f"\n{'='*80}")
    print(f"转换完成！共生成 {len(converted_data)} 条对话")
    print(f"正在保存到: {output_json}")

    try:
        # 确保输出目录存在
        os.makedirs(output_folder_path, exist_ok=True)

        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 保存成功!")

        # 显示文件大小
        file_size = os.path.getsize(output_json) / 1024
        print(f"文件大小: {file_size:.1f} KB")

    except Exception as e:
        print(f"❌ 错误: 保存文件失败 - {e}")
        sys.exit(1)

    print("="*80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="收入证明数据格式转换工具 - 将数据转换为LLaVA或MLLM格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用默认输入输出路径
  python 5_process5.py

  # 指定输入JSON文件
  python 5_process5.py --input data/my_data.json

  # 指定输入JSON和输出文件夹
  python 5_process5.py --input data/my_data.json --output output/

  # 指定所有参数
  python 5_process5.py --input data/my_data.json --output output/ --format llava

默认路径说明:
  - 默认输入: output/04_jsonl/income-template_format.json
  - 默认输出文件夹: output/04_jsonl/

格式说明:
  LLaVA格式: 使用 "conversations" 字段
  MLLM格式: 使用 "messages" 字段

  输入文件要求:
  - 必须是JSON数组格式
  - 每个对象必须包含 "_id" 和 "image" 字段
  - 示例: [{"_id": {"value": "0001"}, "image": {"value": "image.jpg"}, ...}]
        """
    )

    parser.add_argument(
        '--input',
        help='输入JSON文件路径（可选，默认：output/04_jsonl/income-template_format.json）'
    )

    parser.add_argument(
        '--output',
        help='输出文件夹路径（可选，默认：output/04_jsonl/）'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['llava', 'mllm'],
        default='llava',
        help='输出格式类型（默认: llava）'
    )

    args = parser.parse_args()

    # 设置默认路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if args.input is None:
        input_json_path = os.path.join(script_dir, "output", "04_jsonl", "income-template_format.json")
    else:
        input_json_path = args.input

    if args.output is None:
        output_folder_path = os.path.join(script_dir, "output", "04_jsonl")
    else:
        output_folder_path = args.output

    try:
        convert_data_format(input_json_path, output_folder_path, format_type=args.format)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
