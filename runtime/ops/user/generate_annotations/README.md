# 步骤五：图文对生成 - 使用说明

## 简介

本脚本用于生成模型训练所需的图文对数据，将图片和数据记录配对，输出标准化的训练数据集格式。

**注意**：本步骤需要第一步的数据记录和第四步的增强图片作为输入。

## 文件说明

```
step5_generate_annotations_package/
├── step5_generate_annotations.py  # 主脚本
├── requirements.txt               # 依赖包列表（无需额外依赖）
├── src/
│   ├── annotation_builder.py      # 标注生成模块
│   └── __init__.py                # 包初始化
└── README.md                      # 本说明文件
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
1. 第一步生成的 `records.json` 数据文件
2. 第四步生成的增强图片目录

### 基本用法

```bash
# 默认处理（需要前面的步骤已运行）
python step5_generate_annotations.py
```

### 指定输入输出路径

```bash
# 指定数据文件和图片目录
python step5_generate_annotations.py \
  --data ../step1_generate_data_package/data/step1_raw_data/records.json \
  --images ../step4_augment_images_package/data/step4_augmented_images \
  --output data/step5_annotations
```

### 完整参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --data | -d | data/step1_raw_data/records.json | 第一步的数据文件 |
| --images | -i | data/step4_augmented_images | 第四步的图片目录 |
| --output | -o | data/step5_annotations | 输出目录 |
| --format | -f | multimodal | 标注格式（multimodal/simple_json） |
| --split | -s | 0.8 | 训练集比例（验证集和测试集各占剩余的一半） |
| --seed | - | 42 | 随机种子（用于数据集划分） |

## 输出说明

运行成功后会在指定目录生成：

```
data/step5_annotations/
├── loan_clearance_001_2-桌面实景图.json
├── loan_clearance_001_3-桌面实景图_斜拍.json
├── loan_clearance_001_4-桌面实景图_阴影.json
├── ...
├── dataset.json                  # 汇总数据集
└── _metadata.json                # 元信息
```

### 文件命名规则

每个增强图片对应一个标注文件，文件名相同：
- 图片：`loan_clearance_003_2-桌面实景图.jpg`
- 标注：`loan_clearance_003_2-桌面实景图.json`

## 输出格式

### Multimodal 格式（默认）

适用于 LLaVA、Qwen-VL 等多模态大模型：

```json
{
  "id": "loan_clearance_003_2-桌面实景图",
  "image": "data/step4_augmented_images/loan_clearance_003_2-桌面实景图.jpg",
  "conversations": [
    {
      "from": "human",
      "value": "<image>\\n请提取这张贷款结清证明的关键信息，以JSON格式输出"
    },
    {
      "from": "gpt",
      "value": "{\"客户姓名\": \"徐萍\", \"身份证号码\": \"440303199707178290\", ...}"
    }
  ]
}
```

### Simple JSON 格式

适用于自定义训练流程：

```json
{
  "id": "loan_clearance_003_2-桌面实景图",
  "image": "data/step4_augmented_images/loan_clearance_003_2-桌面实景图.jpg",
  "data": {
    "客户姓名": "徐萍",
    "身份证号码": "440303199707178290",
    ...
  },
  "metadata": {
    "document_type": "贷款结清证明",
    "created_at": "2026-01-25T23:30:25"
  }
}
```

### Dataset 汇总文件

包含 train/val/test 划分的完整数据集：

```json
{
  "info": {
    "description": "贷款结清证明数据集",
    "total_samples": 25,
    "format": "multimodal"
  },
  "train": [...],      // 80% 数据
  "validation": [...], // 10% 数据
  "test": [...],       // 10% 数据
  "split": {
    "train": 20,
    "validation": 2,
    "test": 3
  }
}
```

## 使用示例

### 示例1：生成默认格式的图文对

```bash
python step5_generate_annotations.py
```

### 示例2：生成 Simple JSON 格式

```bash
python step5_generate_annotations.py --format simple_json
```

### 示例3：自定义训练集划分比例

```bash
# 训练集 70%，验证集 15%，测试集 15%
python step5_generate_annotations.py --split 0.7
```

### 示例4：指定随机种子确保可复现

```bash
python step5_generate_annotations.py --seed 123
```

## 数据匹配逻辑

脚本通过图片文件名自动匹配到对应的数据记录：

| 图片文件名 | 匹配到 | 数据索引 |
|------------|--------|----------|
| `loan_clearance_001_xxx.jpg` | records[0] | 第一条数据 |
| `loan_clearance_002_xxx.jpg` | records[1] | 第二条数据 |
| `loan_clearance_003_xxx.jpg` | records[2] | 第三条数据 |
| ... | ... | ... |

**匹配规则**：从文件名中提取 `loan_clearance_XXX` 部分，转换为数据索引。

## 常见问题

### Q: 提示 "找不到数据文件"

**A**: 确保先运行第一步生成数据，或使用 `-d` 参数指定正确的数据文件路径。

### Q: 提示 "找不到图片目录"

**A**: 确保先运行第四步生成增强图片，或使用 `-i` 参数指定正确的图片目录。

### Q: 部分图片无法匹配

**A**: 检查图片文件名是否符合 `loan_clearance_XXX_` 格式。不符合格式的图片会被跳过。

### Q: 如何使用生成的数据集训练模型？

**A**:
1. **多模态大模型（LLaVA、Qwen-VL）**：使用 `dataset.json`，按照官方教程格式化数据
2. **自定义训练**：参考 `simple_json` 格式，编写自己的数据加载器

### Q: 可以修改提示词吗？

**A**: 可以，修改 `src/annotation_builder.py` 中的 `human_prompt` 参数，默认为：
   ```
   <image>\n请提取这张贷款结清证明的关键信息，以JSON格式输出
   ```

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
