# 步骤3.5：公章加盖

## 功能说明

该步骤负责在原始PNG图片上加盖银行公章。

## 输入输出

**输入**：
- `data/step3_images/*.png` - 第三步生成的PNG图片
- `data/step1_raw_data/records.json` - 第一步生成的数据记录（包含"贷款银行"字段）

**输出**：
- `data/step3.5_sealed_images/*.png` - 加盖公章后的PNG图片

## 功能特性

- 自动读取数据记录，提取"贷款银行"字段
- 动态生成对应银行的公章
- 基于模板分析的精确盖章位置（纵向52%，横向67%）
- 公章大小为文档宽度的18%
- 公章透明度200/255，真实逼真

## 包结构

```
step3_5_seal_package/
├── step3_5_seal.py       # 主脚本
├── seal_generator.py     # 公章生成模块
├── src/
│   └── seal_stamper.py   # 核心盖章功能
├── requirements.txt
└── README.md
```

## 使用方法

### 单独执行

```bash
python steps/step3_5_seal_package/step3_5_seal.py

# 参数说明
# -i, --input       输入目录（默认: data/step3_images）
# -o, --output      输出目录（默认: data/step3.5_sealed_images）
# -d, --data        数据文件（默认: data/step1_raw_data/records.json）
```

### 在完整流程中执行

```bash
# 通过 run_all.py 自动执行
python run_all.py -n 100

# 流程顺序: 1 → 2 → 3 → 3.5 → 4 → 5
```

## 盖章参数

公章的样式和位置由 `seal_generator.py` 定义：

- **弧度**：210度（文字间距紧凑）
- **文字位置**：离外圈距离 0.78 * outer_radius
- **盖章位置**：
  - 纵向：52%（基于模板分析，覆盖落款文字）
  - 横向：67%（右侧落款区域）
- **大小**：文档宽度的18%（接近真实公章比例）
- **透明度**：200/255

## 输出示例

```
输入: loan_clearance_001.png
输出: loan_clearance_001.png (加盖公章)
      贷款银行: 平安银行
```

## 依赖

- Pillow (图像处理)
- seal_generator (公章生成器，本包内)
