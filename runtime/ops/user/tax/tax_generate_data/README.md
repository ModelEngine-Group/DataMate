# 数据生成算子 - 使用说明

## 简介

本算子用于生成个人所得税完税证明的随机数据，包含纳税人姓名、身份证号、纳税项目、金额等信息。

## 文件说明

```
generate_data/
├── __init__.py                  # 包初始化
├── README.md                    # 本说明文件
├── metadata.yml                 # 算子元数据
├── process.py                   # 主脚本
├── requirements.txt              # 依赖包列表
└── src/
    ├── __init__.py              # 源模块初始化
    └── data_generator.py        # 数据生成模块
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

### 基本用法（生成 10 条数据）

```bash
python process.py
```

### 修改生成数量

编辑 `process.py` 文件，修改 `count` 变量：

```python
count = 100  # 生成100条数据
```

### 自定义配置

可以在 `process.py` 中修改以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| output_dir | "data" | 输出目录 |
| count | 10 | 生成数量 |
| seed | 42 | 随机种子 |

## 输出说明

运行成功后会在 `data/` 目录生成 JSON 文件，文件名格式为：`{纳税人姓名}_个人所得税完税证明.json`

### JSON 数据示例

```json
{
  "文件属性": "附件2：年终为纳税人开具全年纳税情况的完税证明",
  "文件名称": "个人所得税完税证明",
  "纳税人姓名": "张三",
  "纳税人身份证照类型": "居民身份证",
  "纳税人身份号码": "11010119******1234",
  "凭证编码": "(2025)市区个证100号",
  "填发日期": "填发日期：2025年01月25日",
  "纳税项目": [
    {"item": "工资、薪金所得小计", "period": "2024年01月", "amount": "15700.00"},
    {"item": "劳务报酬所得", "period": "2024年06月", "amount": "2400.00"},
    {"item": "稿酬所得", "period": "2024年09月", "amount": "800.00"}
  ],
  "工资、薪金所得小计": "15700.00",
  "劳务报酬所得": "2400.00",
  "稿酬所得": "800.00",
  "税款金额合计（小写）": "18900.00",
  "税款金额合计（大写）": "壹万捌仟玖佰元整"
}
```

## 常见问题

### Q: 提示 "找不到模块 'faker'"

**A**: 请先安装依赖：`pip install -r requirements.txt`

### Q: 如何修改生成的金额范围？

**A**: 在 `src/data_generator.py` 中修改 `random_amount()` 方法的随机范围。

### Q: 生成的身份证号需要修改格式吗？

**A**: 可以在 `src/data_generator.py` 中修改 `generate_id_number_masked()` 方法。

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-28
