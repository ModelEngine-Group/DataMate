import os
from pathlib import Path
from .src import ImageConverter


def main():
    """
    主函数：将Word文档转换为JPG图片
    """
    # 配置路径
    input_dir = "../output/01_words"
    output_dir = "output/02_images"

    # 检查输入目录是否存在
    input_abs_dir = Path(__file__).parent.parent / input_dir
    if not os.path.exists(input_abs_dir):
        print(f"❌ 输入目录不存在: {input_abs_dir}")
        print(f"请先运行 generate_docs/process.py 生成Word文档")
        exit(1)

    # 创建输出目录
    output_abs_dir = Path(__file__).parent.parent / output_dir
    os.makedirs(output_abs_dir, exist_ok=True)

    # 创建转换器
    converter = ImageConverter(str(output_abs_dir))

    # 检测转换方法
    if converter.method == "none":
        print(f"\n❌ 没有可用的转换方法！")
        print("请安装以下依赖之一:")
        print("  1. pip install pywin32 (Windows)")
        print("  2. 安装LibreOffice")
        print("  3. pip install docx2pdf pdf2image")
        exit(1)

    # 转换目录中的所有docx文件
    results = converter.convert_directory(str(input_abs_dir), "*.docx")

    print(f"\n🎉 共转换 {len(results)} 个文件，保存在 '{output_abs_dir}' 目录中。")


if __name__ == "__main__":
    main()
