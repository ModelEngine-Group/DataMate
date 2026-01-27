# 步骤一：数据生成 - 使用说明

## 简介

本脚本用于从 Word 模板提取字段，生成贷款结清证明的随机数据。

## 文件说明

```
step1_package/
├── step1_generate_data.py      # 主脚本
├── 贷款结清证明示例.docx       # Word 模板
├── requirements.txt            # 依赖包列表
├── src/
│   ├── data_generator.py       # 数据生成模块
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

### 基本用法（生成 5 条数据）

```bash
python step1_generate_data.py
```

### 自定义数量

```bash
# 生成 100 条数据
python step1_generate_data.py -n 100

# 生成 1000 条数据，指定随机种子
python step1_generate_data.py -n 1000 -s 123
```

### 完整参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --template | -t | 贷款结清证明示例.docx | Word 模板路径 |
| --count | -n | 5 | 生成数据数量 |
| --seed | -s | 42 | 随机种子（用于复现结果） |
| --output | -o | data/step1_raw_data | 输出目录 |

## 输出说明

运行成功后会在 `data/step1_raw_data/` 目录生成：

```
data/step1_raw_data/
├── records.json       # 生成的数据记录
└── _metadata.json     # 元信息（时间、字段列表等）
```

### records.json 示例

```json
[
  {
    "客户姓名": "张三",
    "身份证号码": "110101199001011234",
    "贷款银行": "中国工商银行",
    "授信额度": "150000元",
    "贷款开立日期": "2021年03月15日",
    "贷款期限": "36个月",
    ...
  }
]
```

## 常见问题

### Q: 提示 "找不到模块 'faker'"

**A**: 请先安装依赖：`pip install -r requirements.txt`

### Q: 中文在控制台显示乱码

**A**: 这是 Windows 控制台编码问题，不影响生成的数据文件。

### Q: 如何修改生成数据的字段？

**A**: 修改 Word 模板中的占位符，程序会自动识别 `{{字段名}}` 格式。

### Q: 可以使用自己的 Word 模板吗？

**A**: 可以，使用 `-t` 参数指定你的模板路径：

```bash
python step1_generate_data.py -t "你的模板.docx"
```

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
