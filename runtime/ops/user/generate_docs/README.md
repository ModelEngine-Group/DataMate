# 步骤二：文档生成 - 使用说明

## 简介

本脚本用于将数据填充到 Word 模板，生成贷款结清证明文档。

**注意**：本步骤需要步骤一生成的 `records.json` 文件作为输入。

## 文件说明

```
step2_package/
├── step2_generate_docs.py      # 主脚本
├── 贷款结清证明示例.docx       # Word 模板
├── requirements.txt            # 依赖包列表
├── src/
│   ├── doc_generator.py        # 文档生成模块
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

## 使用方法

### 准备输入数据

确保有以下文件：
1. 步骤一生成的 `records.json` 数据文件
2. `贷款结清证明示例.docx` 模板文件

### 基本用法

```bash
# 使用默认路径（需要 data/step1_raw_data/records.json 存在）
python step2_generate_docs.py
```

### 指定输入输出路径

```bash
# 指定数据文件和输出目录
python step2_generate_docs.py \
  --input ../step1_package/data/step1_raw_data/records.json \
  --output data/step2_docs
```

### 完整参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --input | -i | data/step1_raw_data/records.json | 数据文件路径 |
| --template | -t | 贷款结清证明示例.docx | Word 模板路径 |
| --output | -o | data/step2_docs | 输出目录 |
| --prefix | -p | loan_clearance | 输出文件名前缀 |

## 输出说明

运行成功后会在指定目录生成：

```
data/step2_docs/
├── loan_clearance_001.docx
├── loan_clearance_002.docx
├── ...
└── _metadata.json
```

## 使用示例

### 示例1：处理步骤一的输出

```bash
# 假设步骤一的数据在 data/step1_raw_data/records.json
python step2_generate_docs.py
```

### 示例2：跨目录使用

```bash
# 步骤一和步骤二在不同目录
python step2_generate_docs.py \
  -i ../step1_package/data/step1_raw_data/records.json \
  -o data/step2_docs
```

### 示例3：自定义文件名前缀

```bash
python step2_generate_docs.py -p my_loan_doc
```

## 常见问题

### Q: 提示 "找不到数据文件"

**A**: 确保先运行步骤一，或使用 `-i` 参数指定正确的数据文件路径。

### Q: 可以使用自己的数据文件吗？

**A**: 可以，数据文件格式为 JSON 数组，每条记录包含字段名和值的字典。

### Q: 生成的 docx 文件打不开

**A**: 检查模板文件是否损坏，确保使用的是有效的 .docx 模板。

### Q: 如何修改模板？

**A**: 模板中使用 `{{字段名}}` 格式的占位符，修改模板后确保占位符名称与数据字段一致。

## 数据文件格式

输入的 `records.json` 格式：

```json
[
  {
    "客户姓名": "张三",
    "身份证号码": "110101199001011234",
    "贷款银行": "中国工商银行",
    ...
  },
  {
    "客户姓名": "李四",
    ...
  }
]
```

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
