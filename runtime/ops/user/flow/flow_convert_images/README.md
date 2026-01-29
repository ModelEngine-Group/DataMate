# 步骤三：图片转换 - 使用说明

## 简介

本脚本用于将 Word 文档转换为 PNG 图片。

**注意**：本步骤需要步骤二生成的 `.docx` 文件作为输入。

## 文件说明

```
step3_package/
├── step3_convert_images.py     # 主脚本
├── requirements.txt            # 依赖包列表
├── src/
│   ├── image_converter.py      # 图片转换模块
│   └── __init__.py             # 包初始化
└── README.md                   # 本说明文件
```

## 安装步骤

### 1. 确保已安装 Python 3.8+

```bash
python --version
```

### 2. 安装依赖包

```bash
pip install -r requirements.txt
```

如果下载慢，使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Windows 用户额外要求

本脚本在 Windows 上使用 Microsoft Word COM 接口进行转换，需要：
- 已安装 Microsoft Word
- 安装 `pywin32` 包（已在 requirements.txt 中）

## 使用方法

### 准备输入文件

确保有以下文件：
- 步骤二生成的 `.docx` 文件目录

### 基本用法

```bash
# 使用默认路径（需要 data/step2_docs/ 目录存在）
python step3_convert_images.py
```

### 指定输入输出路径

```bash
# 指定输入目录和输出目录
python step3_convert_images.py \
  --input ../step2_package/data/step2_docs \
  --output data/step3_images
```

### 调整图片清晰度

```bash
# 使用更高的 DPI（更清晰的图片）
python step3_convert_images.py --dpi 300
```

### 完整参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --input | -i | data/step2_docs | Word 文档目录 |
| --output | -o | data/step3_images | 输出目录 |
| --dpi | -d | 200 | 图片DPI（影响清晰度） |
| --pattern | -p | *.docx | 文件匹配模式 |

## 输出说明

运行成功后会在指定目录生成：

```
data/step3_images/
├── loan_clearance_001.png
├── loan_clearance_002.png
├── ...
└── _metadata.json
```

## 使用示例

### 示例1：处理步骤二的输出

```bash
# 假设步骤二的文档在 data/step2_docs/
python step3_convert_images.py
```

### 示例2：跨目录使用

```bash
# 步骤二和步骤三在不同目录
python step3_convert_images.py \
  -i ../step2_package/data/step2_docs \
  -o data/step3_images
```

### 示例3：生成高清图片

```bash
# 使用 300 DPI 生成更清晰的图片
python step3_convert_images.py --dpi 300
```

## 常见问题

### Q: 提示 "找不到输入目录"

**A**: 确保先运行步骤二，或使用 `-i` 参数指定正确的文档目录。

### Q: 提示 "没有可用的转换方法"

**A**:
1. Windows 用户：确保安装了 Microsoft Word 和 pywin32
2. Linux/Mac 用户：需要安装 LibreOffice

### Q: 转换速度很慢

**A**: Word COM 接口转换需要启动 Word 应用，属于正常现象。大量文件建议分批处理。

### Q: 如何提高图片质量？

**A**: 使用更高的 DPI 值，如 `--dpi 300` 或 `--dpi 400`。

### Q: Linux/Mac 用户如何使用？

**A**: 需要安装 LibreOffice：

```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# macOS
brew install libreoffice
```

## 转换方法说明

本脚本会自动检测可用的转换方法：

| 方法 | 说明 | 适用平台 |
|------|------|----------|
| win32com | 使用 Word COM 接口 | Windows |
| libreoffice | 使用 LibreOffice 命令行 | Linux/Mac/Windows |
| docx2pdf | 使用 docx2pdf 库 | 跨平台 |

## DPI 建议

| DPI | 适用场景 |
|-----|----------|
| 150 | 快速预览，文件较小 |
| 200 | 标准质量（推荐） |
| 300 | 高质量，适合打印 |
| 400+ | 超高质量，文件较大 |

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
