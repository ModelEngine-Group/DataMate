#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入证明批量生成工具
功能：批量生成带有背景的合成图片
工作流程：
  1. 标记背景坐标
  2. 循环生成：
     - 生成唯一ID
     - 调用 1_process1.py 生成回填数据并填充文档
     - 调用 2_process2.py 转换为图片
     - 调用 3_process3.py 添加印章
     - 调用 2_composite_with_background.py 合成背景
     - 重命名合成图片
"""

import os
import sys
import shutil
import importlib.util
import json
from pathlib import Path

from loguru import logger

# Windows控制台GBK编码兼容性处理
if sys.platform == 'win32':
    import builtins
    if not hasattr(builtins, '_print_patched'):
        _original_print = builtins.print
        def _safe_print(*args, **kwargs):
            """安全打印函数，替换GBK不支持的字符"""
            def safe_str(obj):
                s = str(obj)
                # 替换所有可能导致GBK编码错误的字符
                replacements = {
                    '✓': '[OK]',
                    '❌': '[ERROR]',
                    '✗': '[X]',
                    '📋': '[INFO]',
                    '\u2713': '[OK]',
                    '\u2717': '[X]',
                    '\u274c': '[ERROR]',
                    '\u2705': '[OK]',
                    '\U0001f4cb': '[INFO]',
                }
                for old, new in replacements.items():
                    s = s.replace(old, new)
                return s
            new_args = [safe_str(arg) for arg in args]
            _original_print(*new_args, **kwargs)
        builtins.print = _safe_print
        builtins._print_patched = True

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 添加common目录到路径（使用相对路径）
# common目录现在在算子目录下
common_dir = os.path.join(script_dir, 'common')
sys.path.insert(0, common_dir)

# 动态导入模块（文件名以数字开头，需要使用importlib）
def import_module_from_file(module_name, file_path):
    """从文件路径动态导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入common目录下的处理模块
mark_bg_module = import_module_from_file(
    "mark_bg_module",
    os.path.join(common_dir, "1_mark_background_coordinates.py")
)
composite_module = import_module_from_file(
    "composite_module",
    os.path.join(common_dir, "2_composite_with_background.py")
)

# 导入同目录下的处理模块
process1_module = import_module_from_file(
    "process1_module",
    os.path.join(script_dir, "1_process1.py")
)
process2_module = import_module_from_file(
    "process2_module",
    os.path.join(script_dir, "2_process2.py")
)
process3_module = import_module_from_file(
    "process3_module",
    os.path.join(script_dir, "3_process3.py")
)


def generate_unique_id(index):
    """
    生成长度为10的唯一ID

    Args:
        index: 当前索引（从1开始）

    Returns:
        str: 格式化后的ID，如 "0000000001"
    """
    return f"{index:010d}"


def batch_generate_with_backgrounds(template_path=None, loop_count=5, coordinates_json_path=None, background_folder_path=None, output_folder_path=None, init_json_path=None):
    """
    批量生成带有背景的合成图片

    Args:
        template_path: 模板文件路径（可选，默认使用 template/income-template.docx）
        loop_count: 循环次数（默认5）
        coordinates_json_path: 背景坐标JSON文件路径（可选，默认使用 data/coordinates.json）
        background_folder_path: 背景图片文件夹路径（可选，默认使用 backgrounds）
        output_folder_path: 输出合成图片文件夹路径（可选，默认使用 output/03_simulates）
        init_json_path: 生成的初始JSON格式文件路径（可选，默认使用 output/04_jsonl/income-template_format.json）
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 如果未传入 template_path，则使用默认模板
    if template_path is None:
        template_path = os.path.join(script_dir, 'template', 'income-template.docx')

    # 定义路径（如果未指定则使用默认值）
    if background_folder_path is None:
        background_folder = os.path.join(script_dir, "backgrounds")
    else:
        background_folder = background_folder_path

    if coordinates_json_path is None:
        coordinates_json = os.path.join(script_dir, "data", "coordinates.json")
    else:
        coordinates_json = coordinates_json_path

    if output_folder_path is None:
        output_folder = os.path.join(script_dir, "output", "03_simulates")
    else:
        output_folder = output_folder_path

    if init_json_path is None:
        output_json_path = os.path.join(script_dir, "output", "04_jsonl", "income-template_format.json")
    else:
        output_json_path = init_json_path

    source_image = os.path.join(script_dir, "output", "02_images", "income-template_sealed.png")

    logger.info("="*80)
    logger.info("收入证明批量生成工具")
    logger.info("="*80)
    logger.info(f"循环次数: {loop_count}")
    logger.info(f"背景文件夹: {background_folder}")
    logger.info(f"坐标文件: {coordinates_json}")
    logger.info(f"源图片: {source_image}")
    logger.info(f"输出文件夹: {output_folder}")
    logger.info(f"输出JSON: {output_json_path}")
    logger.info("-"*80)

    # 确保输出目录存在
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(os.path.dirname(coordinates_json), exist_ok=True)

    # ========== 第一步：标记背景坐标 ==========
    logger.info("\n>>> 第一步：标记背景坐标")
    logger.info("-"*80)

    if not os.path.exists(coordinates_json):
        logger.info("坐标文件不存在，开始标记背景图片...")
        mark_bg_module.batch_mark_coordinates(
            background_folder=background_folder,
            json_path=coordinates_json,
            debug=False,
            skip_existing=True
        )
        logger.info("✓ 背景坐标标记完成\n")
    else:
        logger.info(f"✓ 坐标文件已存在: {coordinates_json}\n")

    # ========== 第二步：循环生成合成图片 ==========
    logger.info("\n>>> 第二步：批量生成合成图片")
    logger.info("="*80)

    success_count = 0
    fail_count = 0

    # 用于存储所有记录的fill_data
    all_fill_data = []

    for i in range(1, loop_count + 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"[{i}/{loop_count}] 开始处理第 {i} 条记录")
        logger.info("="*80)

        # 生成唯一ID
        unique_id = generate_unique_id(i)
        logger.info(f"\n生成唯一ID: {unique_id}")

        try:
            # --- 步骤1：生成回填数据并填充文档 ---
            logger.info("\n[步骤1/4] 生成回填数据并填充文档...")
            # 确定各步骤的输入/输出路径（使用传入的 output_folder 或默认值）
            base_output = output_folder if output_folder else os.path.join(script_dir, "output")

            # 子目录：01_words, 02_images（保持原有结构但放到 base_output 下）
            words_dir = os.path.join(base_output, "01_words")
            images_dir = os.path.join(base_output, "02_images")
            os.makedirs(words_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)

            output_doc_path = os.path.join(words_dir, f"income-template_filled_{i}.docx")

            # 调用 process1，显式传入 template_path 和输出文档路径
            success_count_1, failed_count_1, company_name, fill_data = process1_module.process_template(
                template_path=template_path,
                output_doc_path=output_doc_path
            )

            if failed_count_1 > 0:
                logger.info(f"  ⚠ 文档填充有 {failed_count_1} 个字段失败，但继续处理")

            logger.info(f"  ✓ 公司名称: {company_name}")

            # --- 步骤2：将Word文档转换为图片 ---
            logger.info("\n[步骤2/4] 将Word文档转换为图片...")
            image_output_path = os.path.join(images_dir, f"income-template_filled_{i}.png")

            # 将 process1 的输出作为 process2 的输入
            process2_module.convert_docx_to_image(input_path=output_doc_path, output_path=image_output_path)
            print("  ✓ 图片转换完成")

            # --- 步骤3：添加印章 ---
            print("\n[步骤3/4] 添加印章...")
            sealed_image_path = os.path.join(images_dir, f"income-template_sealed_{i}.png")

            process3_module.add_seal_to_income_proof(input_path=image_output_path, output_path=sealed_image_path, company_name=company_name)
            print("  ✓ 印章添加完成")

            # --- 步骤4：合成背景 ---
            print("\n[步骤4/4] 合成背景...")
            # 使用刚刚生成并盖章的图片作为合成源
            source_image = os.path.abspath(sealed_image_path)
            success = composite_module.composite_with_random_background(
                source_path=source_image,
                json_path=coordinates_json,
                background_folder=background_folder,
                output_folder=output_folder
            )

            if not success:
                print(f"  ✗ 背景合成失败")
                fail_count += 1
                continue

            # --- 步骤5：重命名合成图片 ---
            print("\n[步骤5/5] 重命名合成图片...")

            # 查找最新生成的合成图片
            output_files = list(Path(output_folder).glob("income-template_sealed_*_composite_*.jpg"))

            if output_files:
                # 按修改时间排序，获取最新的文件
                latest_file = max(output_files, key=lambda f: f.stat().st_mtime)

                # 构建新文件名（直接使用ID）
                new_filename = f"income-template_sealed_composite_{unique_id}.jpg"
                new_file_path = os.path.join(output_folder, new_filename)

                # 重命名文件
                shutil.move(str(latest_file), new_file_path)

                print(f"  ✓ 文件已重命名: {new_filename}")
                success_count += 1
                # 添加ID到fill_data中
                fill_data["_id"] = {
                    "value": unique_id,
                    "type": "_id"
                }
                # 添加image到fill_data中
                fill_data["image"] = {
                    "value": new_filename,
                    "type": "image_path"
                }
                print(f"  ✓ 已添加ID: {unique_id}")

                # 将fill_data添加到数组中
                all_fill_data.append(fill_data)
            else:
                print(f"  ✗ 未找到生成的合成图片")
                fail_count += 1

        except Exception as e:
            print(f"\n✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
            continue

        print(f"\n✓ [{i}/{loop_count}] 处理完成")

    # ========== 统计结果 ==========
    print("\n" + "="*80)
    print("批量生成完成！")
    print("="*80)
    print(f"总数: {loop_count}")
    print(f"成功: {success_count} 条")
    print(f"失败: {fail_count} 条")
    print("="*80)
    print(f"\n所有合成图片已保存至: {output_folder}")

    # ========== 保存JSON数据 ==========
    print(f"\n>>> 第三步：保存填充数据到JSON文件")
    print("-"*80)

    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

        # 保存所有fill_data到JSON文件
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_fill_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 数据已保存至: {output_json_path}")
        print(f"✓ 共保存 {len(all_fill_data)} 条记录")

        # 显示文件大小
        file_size = os.path.getsize(output_json_path) / 1024
        print(f"✓ 文件大小: {file_size:.1f} KB")

    except Exception as e:
        print(f"✗ 保存JSON文件失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="收入证明批量生成工具 - 批量生成带有背景的合成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用所有默认路径
  python 4_process4.py

  # 指定循环次数
  python 4_process4.py --count 10

  # 指定背景文件夹
  python 4_process4.py --background-folder /path/to/backgrounds

  # 指定输出文件夹
  python 4_process4.py --output-folder /path/to/output

  # 完整示例：指定所有路径
  python 4_process4.py --count 10 --coordinates-json data/coords.json --background-folder bg/ --output-folder output/ --init-json result.json

工作流程:
  1. 标记背景图片坐标（如果不存在）
  2. 循环执行以下步骤:
     - 生成10位唯一ID（如 0000000001）
     - 调用 1_process1.py 生成回填数据并填充文档
     - 添加ID到填充数据中
     - 调用 2_process2.py 转换为图片
     - 调用 3_process3.py 添加印章
     - 调用 2_composite_with_background.py 合成背景
     - 重命名合成图片（使用ID）
  3. 保存所有填充数据到JSON文件

默认路径说明:
  - 默认坐标JSON: data/coordinates.json
  - 默认背景文件夹: backgrounds
  - 默认输出文件夹: output/03_simulates
  - 默认初始JSON: output/04_jsonl/income-template_format.json
        """
    )

    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='循环次数（默认5）'
    )

    parser.add_argument(
        '--coordinates-json',
        help='背景坐标JSON文件路径（可选，默认：data/coordinates.json）'
    )

    parser.add_argument(
        '--background-folder',
        help='背景图片文件夹路径（可选，默认：backgrounds）'
    )

    parser.add_argument(
        '--output-folder',
        help='输出合成图片文件夹路径（可选，默认：output/03_simulates）'
    )

    parser.add_argument(
        '--init-json',
        help='生成的初始JSON格式文件路径（可选，默认：output/04_jsonl/income-template_format.json）'
    )

    args = parser.parse_args()

    try:
        batch_generate_with_backgrounds(
            loop_count=args.count,
            coordinates_json_path=args.coordinates_json,
            background_folder_path=args.background_folder,
            output_folder_path=args.output_folder,
            init_json_path=args.init_json
        )
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
