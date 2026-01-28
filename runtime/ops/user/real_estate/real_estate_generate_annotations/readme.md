# 步骤四：图文对生成 - 不动产权证

## 简介

本模块用于生成模型训练所需的图文对数据，将图片和数据记录配对，输出标准化的训练数据集格式。

## 文件说明

```
generate_annotations/
├── process.py                    # 主处理脚本
├── metadata.yml                 # 算子配置文件
├── requirements.txt            # 依赖包列表
├── src/
│   ├── annotation_builder.py   # 标注生成模块
│   └── __init__.py           # 包初始化
└── README.md                  # 本说明文件
```

## 安装步骤

### 1. 确保已安装 Python 3.8+

```bash
python --version
```

### 2. 无需安装额外依赖

本步骤仅使用 Python 标准库，无需安装额外依赖包。

## 使用方法

### 准备输入文件

确保有以下内容：
1. 第一步生成的 `generated_records.json` 数据文件
2. 第三步生成的增强图片目录

### 基本用法

```bash
# 默认处理（需要前面的步骤已运行）
python process.py
```

### 指定输入输出路径

```bash
# 指定数据文件和图片目录
python process.py \
  --data ../step1_generate_data_package/generated_records.json \
  --images ../step3_augment_images_package/images_output \
  --output data/step4_annotations
```

## 输出说明

运行成功后会在指定目录生成：

```
data/step4_annotations/
├── qa_pairs.jsonl
└── _metadata.json
```

### 文件命名规则

每个增强图片对应一个标注文件，文件名相同：
- 图片：`estate_001_2-桌面实景图.jpg`
- 标注：`qa_pairs.jsonl`（JSONL格式）

## 输出格式

### Multimodal 格式（默认）

适用于 LLaVA、Qwen-VL 等多模态大模型：

```json
{
  "file_info": "images/estate_001_2-桌面实景图.jpg",
  "individual_qa_pairs": [
    {
      "question": "这份不动产登记记录的年份是？",
      "answer": "2024"
    },
    ...
  ],
  "complete_qa_pairs": {
    "question": "请提供这份不动产登记记录的完整信息。",
    "answer": "年份：2024，县（市、区）：XXX县，文档编号：1234567，..."
  }
}
```

### Simple JSON 格式

适用于自定义训练流程：

```json
{
  "file_info": "images/estate_001_2-桌面实景图.jpg",
  "data": {
    "年份": "2024",
    "县（市、区）": "XXX县",
    ...
  },
  "metadata": {
    "document_type": "不动产权证",
    "created_at": "2026-01-25T23:30:25"
  }
}
```

## 问题列表

系统自动生成以下12个问题：

1. 这份不动产登记记录的年份是？
2. 该不动产所在县（市、区）是？
3. 该登记记录的文档编号是多少？
4. 不动产权利人姓名是？
5. 该不动产的所有权形式是？
6. 不动产登记地址是？
7. 不动产权证书号是多少？
8. 该不动产的权利类型是什么？
9. 该不动产的权利性质是什么？
10. 该不动产的用途是什么？
11. 该不动产的土地使用权面积和房屋建筑面积分别是多少？
12. 该不动产的土地使用期限是？

## 数据匹配逻辑

脚本通过图片文件名自动匹配到对应的数据记录：

| 图片文件名 | 匹配到 | 数据索引 |
|------------|--------|----------|
| `estate_001_xxx.jpg` | records[0] | 第一条数据 |
| `estate_002_xxx.jpg` | records[1] | 第二条数据 |
| `estate_003_xxx.jpg` | records[2] | 第三条数据 |
| ... | ... | ... |

**匹配规则**：从文件名中提取 `estate_XXX` 部分，转换为数据索引。

## 常见问题

### Q: 提示 "找不到数据文件"

**A**: 确保先运行第一步生成数据，或使用 `-d` 参数指定正确的数据文件路径。

### Q: 提示 "找不到图片目录"

**A**: 确保先运行第三步生成增强图片，或使用 `-i` 参数指定正确的图片目录。

### Q: 部分图片无法匹配

**A**: 检查图片文件名是否符合 `estate_XXX_` 格式。不符合格式的图片会被跳过。

### Q: 如何使用生成的数据集训练模型？

**A**:
1. **多模态大模型（LLaVA、Qwen-VL）**：使用 `qa_pairs.jsonl`，按照官方教程格式化数据
2. **自定义训练**：参考 `simple_json` 格式，编写自己的数据加载器

### Q: 可以修改提示词吗？

**A**: 可以，修改 `src/annotation_builder.py` 中的 `QUESTIONS` 列表和 `complete_qa_pairs` 的提示词。

## 数据集统计

运行后会生成 `_metadata.json`，包含：
- 总记录数
- 总图片数
- 成功匹配数
- 数据集划分信息

## 训练建议

### 数据量建议
- **小规模实验**：100-500 张图片
- **中等规模**：1000-5000 张图片
- **大规模生产**：10000+ 张图片

### 数据划分建议
- **训练集**：70%-80%
- **验证集**：10%-15%
- **测试集**：10%-15%

### 模型选择
- **文档理解**：LayoutLMv3、Donut
- **多模态对话**：LLaVA、Qwen-VL
- **OCR + 提取**：PaddleOCR + 自定义分类器

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
