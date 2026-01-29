# 文档生成算子 - 使用说明

## 简介

本算子用于将JSON数据填充到Word模板，批量生成个人所得税完税证明文档。

## 文件说明

```
generate_docs/
├── __init__.py                  # 包初始化
├── README.md                    # 本说明文件
├── metadata.yml                 # 算子元数据
├── process.py                   # 主脚本
├── requirements.txt              # 依赖包列表
└── src/
    ├── __init__.py              # 源模块初始化
    └── doc_generator.py        # 文档生成模块
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

## 使用方法

### 基本用法（批量生成）

```bash
python process.py
```

### 前置条件

运行前需要满足以下条件：

1. **数据文件存在**：`../data/` 目录下需要有 JSON 数据文件
2. **模板文件存在**：`../template/个人所得税完税证明.docx` 需要存在

如果数据文件不存在，请先运行：

```bash
cd ../tax_generate_data
python process.py
```

## 输出说明

运行成功后会在 `output/01_words/` 目录生成 Word 文档，文件名格式为：`{纳税人姓名}_个人所得税完税证明.docx`

## 输出目录结构

```
output/
└── 01_words/
    ├── 张三_个人所得税完税证明.docx
    ├── 李四_个人所得税完税证明.docx
    └── ...
```

## 常见问题

### Q: 提示 "找不到模块 'docx'"

**A**: 请先安装依赖：`pip install python-docx`

### Q: 提示模板文件不存在

**A**:
1. 确认模板文件在 `../template/` 目录下
2. 或修改 `process.py` 中的 `template_path` 变量

### Q: 提示数据目录不存在

**A**: 请先运行 `generate_data/process.py` 生成数据文件

### Q: 生成的文档格式不对

**A**: 检查模板文件中的表格结构是否正确

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-28
