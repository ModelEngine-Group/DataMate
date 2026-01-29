#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入证明添加印章工具
功能：在收入证明图片上添加公司印章
"""

import os
import sys

from loguru import logger

# 添加common目录到路径（使用相对路径）
# common目录现在在算子目录下
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'common'))

from add_seal import add_seal_to_image


def add_seal_to_income_proof(input_path=None, output_path=None, seal_type="finance", company_name=None):
    """
    给收入证明图片添加印章

    Args:
        input_path: 输入图片路径（可选，默认使用 output/02_images/income-template_filled.png）
        output_path: 输出图片路径（可选，默认使用 output/02_images/income-template_sealed.png）
        seal_type: 印章类型（可选，默认为"finance"，可选值：finance/name/bank/multiple）
        company_name: 公司名称（可选，不传则使用默认值，用于财务章、银行章、多章组合）

    Returns:
        str: 输出图片的完整路径，失败返回None
    """
    # 定义默认的路径（相对于脚本所在目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 如果未指定输入路径，使用默认路径
    if input_path is None:
        input_path = os.path.join(script_dir, "output", "02_images", "income-template_filled.png")

    # 如果未指定输出路径，使用默认路径
    if output_path is None:
        output_path = os.path.join(script_dir, "output", "02_images", "income-template_sealed.png")

    logger.info("="*60)
    logger.info("收入证明添加印章工具")
    logger.info("="*60)

    # 检查输入图片是否存在
    if not os.path.exists(input_path):
        logger.info(f"\n错误: 输入图片文件不存在 - {input_path}")
        logger.info(f"请确保文件路径正确，或先运行前面的处理步骤生成该文件。")
        sys.exit(1)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"\n输入图片: {input_path}")
    logger.info(f"输出图片: {output_path}")
    logger.info(f"印章类型: {seal_type}")
    logger.info(f"公司名称: {company_name}")

    # 添加印章
    logger.info(f"\n正在添加印章...")
    try:
        result = add_seal_to_image(
            image_path=input_path,
            company_name=company_name,
            seal_type=seal_type,
            output_path=output_path,
            position_ratio=None,  # 自动智能定位
            seal_size_ratio=0.22
        )

        if result:
            logger.info("\n" + "="*60)
            logger.info("[OK] 印章添加成功!")
            logger.info("="*60)
            logger.info(f"输出文件: {result}")

            # 获取文件大小
            file_size = os.path.getsize(result) / 1024
            logger.info(f"文件大小: {file_size:.1f} KB")

            return result
        else:
            logger.info("\n[FAIL] 印章添加失败")
            return None

    except FileNotFoundError as e:
        logger.info(f"\n错误: 找不到文件 - {e}")
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
        description="收入证明添加印章工具 - 在收入证明图片上添加公司印章",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认路径和默认公司名称
  python 3_process3.py

  # 指定公司名称
  python 3_process3.py "上海腾讯科技有限公司"

  # 指定输入输出路径
  python 3_process3.py --input input.png --output output.png "公司名称"

  # 使用人名章（不指定人名则使用默认值"张三"）
  python 3_process3.py --seal-type name
  python 3_process3.py --seal-type name --person-name "李四"

  # 使用银行章（不指定银行则使用默认值）
  python 3_process3.py --seal-type bank
  python 3_process3.py --seal-type bank --bank-text "承兑银行"

默认路径说明:
  - 默认输入: output/02_images/income-template_filled.png
  - 默认输出: output/02_images/income-template_sealed.png
  - 默认印章类型: finance（财务专用章）

印章类型说明:
  - finance: 财务专用章（圆形，可选company_name，默认："上海腾讯科技有限公司"）
  - name: 人名章（方形，可选person-name参数，默认："张三"）
  - bank: 银行章（椭圆，可选bank-text参数，默认："招商银行股份有限公司"）
  - multiple: 多章组合（可选company_name、可选person-name、可选bank-text）
        """
    )

    parser.add_argument('--input', help='输入图片路径（可选）')
    parser.add_argument('--output', help='输出图片路径（可选）')
    parser.add_argument('--seal-type', choices=['finance', 'name', 'bank', 'multiple'],
                       default='finance', help='印章类型（可选，默认: finance）')
    parser.add_argument('company_name', nargs='?',
                       help='公司名称（可选，用于finance/bank/multiple印章，默认："上海腾讯科技有限公司"）')
    parser.add_argument('--person-name',
                       help='人名（可选，用于name印章，默认："张三"）')
    parser.add_argument('--bank-text',
                       help='银行文字（可选，用于bank印章，默认："招商银行股份有限公司"）')

    args = parser.parse_args()

    # 定义默认值
    DEFAULT_COMPANY_NAME = "上海腾讯科技有限公司"
    DEFAULT_PERSON_NAME = "张三"
    DEFAULT_BANK_TEXT = "招商银行股份有限公司"

    # 根据印章类型确定参数，如果未提供则使用默认值
    if args.seal_type == 'name':
        company_name = args.person_name if args.person_name else DEFAULT_PERSON_NAME
        logger.info(f"使用默认人名: {company_name}")
    elif args.seal_type == 'bank':
        company_name = args.bank_text if args.bank_text else DEFAULT_BANK_TEXT
        logger.info(f"使用默认银行文字: {company_name}")
    else:  # finance 或 multiple
        company_name = args.company_name if args.company_name else DEFAULT_COMPANY_NAME
        print(f"使用默认公司名称: {company_name}")

    result = add_seal_to_income_proof(
        input_path=args.input,
        output_path=args.output,
        seal_type=args.seal_type,
        company_name=company_name
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
