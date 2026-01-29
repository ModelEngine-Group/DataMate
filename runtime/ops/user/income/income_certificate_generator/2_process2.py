#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入证明文档转图片工具
功能：将Word文档转换为PNG图片
"""

import os
import sys

from loguru import logger

# 添加common目录到路径（使用相对路径）
# common目录现在在算子目录下
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'common'))

from convert_to_image import WordToImageConverter


def convert_docx_to_image(input_path=None, output_path=None):
    """
    将Word文档转换为图片

    Args:
        input_path: 输入Word文档路径（可选，默认使用 output/01_words/income-template_filled.docx）
        output_path: 输出图片路径（可选，默认使用 output/02_images/income-template_filled.png）

    Returns:
        str: 输出图片的完整路径，失败返回None
    """
    # 定义默认的输入输出路径（相对于脚本所在目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 如果未指定输入路径，使用默认路径
    if input_path is None:
        input_path = os.path.join(script_dir, "output", "01_words", "income-template_filled.docx")

    # 如果未指定输出路径，使用默认路径
    if output_path is None:
        output_dir = os.path.join(script_dir, "output", "02_images")
        output_filename = "income-template_filled.png"
    else:
        # 从完整路径中提取目录和文件名
        output_dir = os.path.dirname(output_path)
        output_filename = os.path.basename(output_path)

    logger.info("="*60)
    logger.info("收入证明文档转图片工具")
    logger.info("="*60)

    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        logger.info(f"\n错误: 输入文件不存在 - {input_path}")
        logger.info(f"请确保文件路径正确，或先运行前面的处理步骤生成该文件。")
        sys.exit(1)

    logger.info(f"\n输入文件: {input_path}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"输出文件名: {output_filename}")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 创建转换器
        logger.info(f"\n正在初始化转换器...")
        converter = WordToImageConverter(output_dir=output_dir, dpi=200)

        # # 打印转换器信息
        # converter.print_info()

        # 执行转换
        logger.info(f"\n开始转换: {os.path.basename(input_path)}")
        result = converter.convert(input_path)

        if result:
            logger.info("\n" + "="*60)
            logger.info("[OK] 转换成功!")
            logger.info("="*60)
            logger.info(f"输出文件: {result}")

            # 获取文件大小
            file_size = os.path.getsize(result) / 1024
            logger.info(f"文件大小: {file_size:.1f} KB")

            # 检查输出文件是否与期望的文件名一致
            expected_output = os.path.join(output_dir, output_filename)
            if result == expected_output:
                logger.info(f"\n[SUCCESS] 文件已生成: {output_filename}")
            else:
                logger.info(f"\n[INFO] 实际输出文件: {os.path.basename(result)}")

            return result
        else:
            logger.info("\n[FAIL] 转换失败")
            return None

    except FileNotFoundError as e:
        logger.info(f"\n错误: 找不到文件或目录 - {e}")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='收入证明文档转图片工具 - 将Word文档转换为PNG图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认路径
  python 2_process2.py

  # 指定输入文件
  python 2_process2.py --input /path/to/document.docx

  # 指定输出文件
  python 2_process2.py --output /path/to/output.png

  # 指定输入和输出文件
  python 2_process2.py --input document.docx --output output.png

默认路径说明:
  - 默认输入: output/01_words/income-template_filled.docx
  - 默认输出: output/02_images/income-template_filled.png
        """
    )

    parser.add_argument('--input', help='输入Word文档路径（可选）')
    parser.add_argument('--output', help='输出图片路径（可选）')

    args = parser.parse_args()

    result = convert_docx_to_image(
        input_path=args.input,
        output_path=args.output
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
