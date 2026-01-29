import os
from pathlib import Path
from .src import ImageAugmenter


def main():
    """
    主函数：执行真实世界模拟
    """
    # 配置路径
    src_dir = "../output/02_images"
    backgrounds_dir = "../backgrounds"
    output_dir = "output/03_simulated"
    coord_file = "coordinates_cache.json"

    # 检查源文件夹是否存在
    src_abs_dir = Path(__file__).parent.parent / src_dir
    if not os.path.exists(src_abs_dir):
        print(f"❌ 源目录不存在: {src_abs_dir}")
        print(f"请先运行 convert_images/process.py 生成JPG图片")
        exit(1)

    # 检查背景文件夹是否存在
    bg_abs_dir = Path(__file__).parent.parent / backgrounds_dir
    if not os.path.exists(bg_abs_dir):
        print(f"❌ 背景目录不存在: {bg_abs_dir}")
        exit(1)

    # 创建输出目录
    output_abs_dir = Path(__file__).parent.parent / output_dir
    os.makedirs(output_abs_dir, exist_ok=True)

    # 创建增强器
    augmenter = ImageAugmenter(
        backgrounds_dir=str(bg_abs_dir),
        output_dir=str(output_abs_dir),
        coord_file=str(Path(__file__).parent.parent / coord_file)
    )

    # 批量处理
    augmenter.process_images(str(src_abs_dir))

    print(f"\n🎉 图片已保存在 '{output_abs_dir}' 目录中。")


if __name__ == "__main__":
    main()
