# 图片转换算子 - 使用说明

## 简介

本算子用于将生成的Word文档转换为JPG图片，支持多种转换方法自动检测。

## 文件说明

```
convert_images/
├── __init__.py                  # 包初始化
├── README.md                    # 本说明文件
├── metadata.yml                 # 算子元数据
├── process.py                   # 主脚本
├── requirements.txt              # 依赖包列表
└── src/
    ├── __init__.py              # 源模块初始化
    └── image_converter.py        # 图片转换模块
```

## 安装步骤

### 1. 确保已安装 Python 3.8+

```bash
python --version
```

### 2. 安装依赖包（三选一）

#### 选项1：Windows（推荐）

```bash
pip install pywin32
```

#### 选项2：跨平台

```bash
pip install docx2pdf pdf2image
```

**Windows用户还需要下载Poppler**：
- 下载地址: https://github.com/oschwartz10612/poppler-windows/releases/
- 解压后将 `bin` 目录添加到系统PATH

#### 选项3：Linux/Mac

```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# macOS
brew install --cask libreoffice
```

如果下载慢，使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 使用方法

### 基本用法

```bash
python process.py
```

### 前置条件

运行前需要满足以下条件：

1. **Word文档存在**：`../output/01_words/` 目录下需要有 Word 文档
2. **依赖已安装**：根据系统安装对应的转换依赖

如果Word文档不存在，请先运行：

```bash
cd ../tax_generate_docs
python process.py
```

## 支持的转换方法

本算子会自动检测并使用以下转换方法（按优先级）：

### 1. win32com（Windows专用）

- **优点**：使用Word API，转换质量最好
- **依赖**：`pip install pywin32`
- **路径**：`C:\Program Files\Microsoft Office\...`

### 2. LibreOffice（跨平台）

- **优点**：免费开源，跨平台支持
- **依赖**：安装LibreOffice
- **路径**：需要soffice在系统PATH中

### 3. docx2pdf + pdf2image（跨平台）

- **优点**：纯Python实现，无需额外软件
- **依赖**：`pip install docx2pdf pdf2image`
- **注意**：Windows需要安装Poppler

### 4. 备用渲染（降级方案）

- **场景**：当以上方法都失败时使用
- **说明**：简单文本渲染，格式不完美
- **用途**：仅用于测试或紧急情况

## 输出说明

运行成功后会在 `output/02_images/` 目录生成 JPG 文件。

## 输出目录结构

```
output/
└── 02_images/
    ├── 张三_个人所得税完税证明.jpg
    ├── 李四_个人所得税完税证明.jpg
    └── ...
```

## 常见问题

### Q1: 提示 "没有可用的转换方法"

**A**: 根据错误信息安装对应的依赖：
- Windows: 运行 `pip install pywin32`
- Linux/Mac: 安装LibreOffice
- 跨平台: 运行 `pip install docx2pdf pdf2image` (Windows还需下载Poppler)

### Q2: PDF转图片失败

**A**:
1. 确认已安装 `pdf2image`: `pip install pdf2image`
2. Windows用户需要下载并安装 Poppler
3. 确认Poppler路径在系统PATH中，或在代码中指定路径

### Q3: Poppler下载失败

**A**: 访问官方下载页面：
- https://github.com/oschwartz10612/poppler-windows/releases/
- 选择最新版本下载 `Release-xxx.zip`
- 解压后将 `Library\bin` 目录添加到系统PATH

### Q4: 生成的图片质量不高

**A**: 可以在 `process.py` 中修改 `dpi` 参数：
```python
converter = ImageConverter(str(output_abs_dir), dpi=300)  # 提高DPI到300
```

### Q5: LibreOffice无法启动

**A**:
1. 确认LibreOffice已正确安装
2. 尝试从命令行运行 `soffice --version` 测试
3. 确保soffice在系统PATH中

### Q6: Word文档路径错误

**A**:
1. 确认在 `convert_images` 目录下运行
2. 或修改 `process.py` 中的 `input_dir` 变量

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-28
