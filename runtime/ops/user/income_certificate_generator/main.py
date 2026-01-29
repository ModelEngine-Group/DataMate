#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入证明批量生成主脚本
功能：整合4_process4和5_process5，从模板生成训练数据

工作流程：
  1. 使用模板生成回填数据并填充文档
  2. 转换为图片
  3. 添加印章
  4. 合成真实背景
  5. 保存初始JSON
  6. 转换为LLaVA或MLLM训练格式
"""

import os
import sys
import importlib.util

from loguru import logger

# Windows控制台GBK编码兼容性处理
if sys.platform == 'win32':
    import builtins
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
                '💰': '[MONEY]',
                '📄': '[DOC]',
                '⚠': '[WARN]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '\u2713': '[OK]',  # ✓
                '\u2717': '[X]',   # ✗
                '\u274c': '[ERROR]', # ❌
                '\u2705': '[OK]',    # ✅
                '\U0001f4cb': '[INFO]', # 📋
            }
            for old, new in replacements.items():
                s = s.replace(old, new)
            # 进一步移除任何不在GBK范围内的字符
            try:
                s.encode('gbk')
            except UnicodeEncodeError:
                # 如果还有无法编码的字符，逐个替换
                safe_chars = []
                for char in s:
                    try:
                        char.encode('gbk')
                        safe_chars.append(char)
                    except UnicodeEncodeError:
                        safe_chars.append('?')
                s = ''.join(safe_chars)
            return s

        new_args = [safe_str(arg) for arg in args]
        _original_print(*new_args, **kwargs)
    builtins.print = _safe_print


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


# 导入处理模块
process4_module = import_module_from_file(
    "process4_module",
    os.path.join(script_dir, "4_process4.py")
)

process5_module = import_module_from_file(
    "process5_module",
    os.path.join(script_dir, "5_process5.py")
)


def batch_generate_training_data(
    template_path=None,
    count=5,
    coordinates_json_path=None,
    background_folder_path=None,
    output_folder_path=None,
    init_json_path=None,
    output_format='llava'
):
    """
    批量生成训练数据（图片 + QA对JSON）

    Args:
        template_path: 模板文档路径（可选，默认使用 template/income-template.docx）
        count: 生成数量（默认5）
        coordinates_json_path: 背景坐标JSON文件路径（可选）
        background_folder_path: 背景图片文件夹路径（可选）
        output_folder_path: 输出合成图片文件夹路径（可选）
        init_json_path: 初始JSON格式文件路径（可选）
        output_format: 输出格式（'llava' 或 'mllm'，默认'llava'）

    Returns:
        tuple: (success_count, fail_count, init_json_path, final_json_path)
    """
    logger.info("="*80)
    logger.info("收入证明批量生成主脚本")
    logger.info("="*80)
    logger.info(f"模板文档: {template_path}")
    logger.info(f"生成数量: {count}")
    logger.info(f"输出格式: {output_format.upper()}")
    logger.info("-"*80)

    # ========== 第一步：批量生成合成图片和初始JSON ==========
    logger.info("\n>>> 第一步：批量生成合成图片和初始JSON")
    logger.info("="*80)

    try:
        # 调用 4_process4.py 的批量生成功能
        process4_module.batch_generate_with_backgrounds(
            template_path=template_path,
            loop_count=count,
            coordinates_json_path=coordinates_json_path,
            background_folder_path=background_folder_path,
            output_folder_path=output_folder_path,
            init_json_path=init_json_path
        )

        # 获取初始JSON路径（用于下一步）
        if init_json_path is None:
            init_json_path = os.path.join(script_dir, "output", "04_jsonl", "income-template_format.json")

    except Exception as e:
        logger.info(f"\n❌ 错误: 批量生成失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ========== 第二步：转换为训练格式 ==========
    logger.info(f"\n>>> 第二步：转换为{output_format.upper()}训练格式")
    logger.info("="*80)

    try:
        # 确定输出文件夹
        if output_folder_path is None:
            output_folder = os.path.join(script_dir, "output", "04_jsonl")
        else:
            output_folder = output_folder_path

        # 调用 5_process5.py 的格式转换功能
        process5_module.convert_data_format(
            input_json_path=init_json_path,
            output_folder_path=output_folder,
            format_type=output_format
        )

        # 确定最终JSON文件路径
        if output_format == 'llava':
            final_json_path = os.path.join(output_folder, "income-template_llava_format.json")
        else:  # mllm
            final_json_path = os.path.join(output_folder, "income-template_mllm_format.json")

        # 返回结果
        success_count = count  # 假设全部成功，实际已在4_process4中统计
        fail_count = 0

        return success_count, fail_count, init_json_path, final_json_path

    except Exception as e:
        logger.info(f"\n❌ 错误: 格式转换失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="收入证明批量生成主脚本 - 从模板生成训练数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用所有默认路径（模板文档、生成5条、LLaVA格式）
  python main.py

  # 指定模板文档和生成数量
  python main.py --template template.docx --count 10

  # 指定所有参数
  python main.py --template template.docx --count 10 --format mllm

  # 指定背景文件夹和输出文件夹
  python main.py --template template.docx --count 20 --background-folder bg/ --output output/

完整示例：
  python main.py \\
    --template template/income-template.docx \\
    --count 100 \\
    --background-folder backgrounds/ \\
    --output-folder output/simulates/ \\
    --format llava

工作流程:
  1. 使用模板生成回填数据并填充文档
  2. 将Word文档转换为图片
  3. 添加公司印章
  4. 合成真实背景（随机选择背景图片）
  5. 保存初始JSON（包含_id和image字段）
  6. 转换为LLaVA或MLLM训练格式

默认路径说明:
  - 默认模板: template/income-template.docx
  - 默认坐标JSON: data/coordinates.json
  - 默认背景文件夹: backgrounds
  - 默认输出文件夹: output/03_simulates
  - 默认初始JSON: output/04_jsonl/income-template_format.json
  - 默认输出格式: llava
        """
    )

    parser.add_argument(
        '--template',
        help='模板文档路径（可选，默认：template/income-template.docx）'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='生成数量（默认5）'
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
        help='初始JSON格式文件路径（可选，默认：output/04_jsonl/income-template_format.json）'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['llava', 'mllm'],
        default='llava',
        help='输出格式类型（默认: llava）'
    )

    args = parser.parse_args()

    # 设置默认模板路径
    if args.template is None:
        template_path = os.path.join(script_dir, "template", "income-template.docx")
    else:
        template_path = args.template

    # 检查模板文件是否存在
    if not os.path.exists(template_path):
        logger.info(f"❌ 错误: 模板文件不存在 - {template_path}")
        sys.exit(1)

    try:
        success_count, fail_count, init_json, final_json = batch_generate_training_data(
            template_path=template_path,
            count=args.count,
            coordinates_json_path=args.coordinates_json,
            background_folder_path=args.background_folder,
            output_folder_path=args.output_folder,
            init_json_path=args.init_json,
            output_format=args.format
        )

        # 打印最终统计
        logger.info("\n" + "="*80)
        logger.info("✓ 全部处理完成！")
        logger.info("="*80)
        logger.info(f"模板文档: {template_path}")
        logger.info(f"生成数量: {args.count}")
        logger.info(f"成功: {success_count} 条")
        logger.info(f"失败: {fail_count} 条")
        logger.info(f"\n输出文件:")
        logger.info(f"  初始JSON: {init_json}")
        logger.info(f"  训练JSON: {final_json}")
        logger.info("="*80)

    except KeyboardInterrupt:
        logger.info("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
