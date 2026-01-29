import os
import glob
from pathlib import Path
from .src import QAGenerator


def main():
    """
    主函数：生成QA对并输出JSONL数据集
    """
    # 配置路径
    data_dir = "../data"
    image_dir = "../output/03_simulated"
    output_dir = "output/04_jsonl"
    output_file = "个人所得税完税证明_dataset.jsonl"

    # 检查数据目录是否存在
    data_abs_dir = Path(__file__).parent.parent / data_dir
    if not os.path.exists(data_abs_dir):
        print(f"❌ 数据目录不存在: {data_abs_dir}")
        print(f"请先运行 generate_data/process.py 生成数据文件")
        exit(1)

    # 检查图片目录是否存在
    image_abs_dir = Path(__file__).parent.parent / image_dir
    if not os.path.exists(image_abs_dir):
        print(f"❌ 图片目录不存在: {image_abs_dir}")
        print(f"请先运行 augment_images/process.py 生成模拟图片")
        exit(1)

    # 创建输出目录
    output_abs_dir = Path(__file__).parent.parent / output_dir
    os.makedirs(output_abs_dir, exist_ok=True)

    # 获取所有数据文件
    data_files = list(data_abs_dir.glob("*.json"))
    data_files.sort()

    if not data_files:
        print(f"❌ 在 {data_abs_dir} 目录中未找到JSON文件")
        exit(1)

    print(f"📂 找到 {len(data_files)} 个数据文件")

    # 创建输出文件完整路径
    output_abs_file = os.path.join(output_abs_dir, output_file)

    # 创建QA生成器
    generator = QAGenerator(random_questions=8)

    # 生成QA对并输出JSONL
    total_records = generator.generate_batch(
        data_files=[f for f in data_files],
        image_dir=str(image_abs_dir),
        output_file=output_abs_file
    )

    print(f"\n🎊 数据集生成完成！")
    print(f"📁 输出文件: {output_abs_file}")
    print(f"\n目录结构：")
    print(f"  - data/                    : 原始JSON数据文件")
    print(f"  - output/01_words/          : 生成的Word文档")
    print(f"  - output/02_images/         : 转换后的JPG图片")
    print(f"  - output/03_simulated/      : 真实世界模拟图片")
    print(f"  - output/04_jsonl/          : 最终JSONL数据集")


if __name__ == "__main__":
    main()
