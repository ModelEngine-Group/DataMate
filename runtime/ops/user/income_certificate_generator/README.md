# 收入证明生成器算子

## 算子简介

本算子用于批量生成收入证明的多模态训练数据集，支持从Word模板到最终训练JSON的全流程自动化处理。

## 功能特性

- ✅ **模板填充**：使用Faker自动生成随机数据并填充Word模板
- ✅ **格式转换**：将Word文档转换为高清图片（跨平台支持）
- ✅ **印章添加**：自动添加公司印章（可选）
- ✅ **真实场景合成**：将文档合成到真实背景中，模拟拍摄效果（可选）
- ✅ **多格式输出**：支持LLaVA和MLLM训练格式
- ✅ **跨平台兼容**：支持Linux、Windows、macOS

## 工作流程

```
┌─────────────────┐
│ 1. 模板填充      │ → 使用Faker生成随机数据，填充Word模板
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. 格式转换      │ → 将Word文档转换为高清图片（Playwright渲染）
└────────┬────────┘
         ↓
┌─────────────────┐
│ 3. 印章添加      │ → 在图片上自动添加公司印章（可选）
└────────┬────────┘
         ↓
┌─────────────────┐
│ 4. 背景合成      │ → 将文档合成到真实背景，模拟拍摄效果（可选）
└────────┬────────┘
         ↓
┌─────────────────┐
│ 5. JSON生成      │ → 生成初始JSON格式数据
└────────┬────────┘
         ↓
┌─────────────────┐
│ 6. 格式转换      │ → 转换为LLaVA或MLLM训练格式
└─────────────────┘
```

## 使用方法

### 在DataMate工作流中使用

1. 在DataMate工作流编排界面中添加此算子
2. 配置算子参数：
   - **生成数量**：1-1000张
   - **输出格式**：LLaVA或MLLM
   - **添加印章**：是否添加公司印章
   - **真实场景模拟**：是否启用背景合成
3. 运行工作流

### 本地调试

```bash
# 进入算子目录
cd runtime/ops/mapper/income_certificate_generator

# 安装依赖
pip install -r requirements.txt

# Linux环境额外安装
sudo apt-get install poppler-utils
playwright install chromium

# Windows/macOS环境
playwright install chromium

# 运行测试
python main.py --count 10 --format llava
```

## 算子参数

| 参数名 | 类型 | 说明 | 默认值 | 范围 |
|--------|------|------|--------|------|
| count | inputNumber | 生成数量 | 5 | 1-1000 |
| outputFormat | select | 输出格式 | llava | llava/mllm |
| addSeal | switch | 是否添加印章 | true | - |
| simulateRealWorld | switch | 真实场景模拟 | true | - |

## 输出说明

生成的数据保存在两个位置：

### 1. 算子目录输出（`output/`）

```
output/
├── 01_words/              # 填充后的Word文档
│   └── income-template_filled.docx
├── 02_images/             # 转换后的原始图片
│   ├── income-template_filled.png
│   └── income-template_sealed.png
├── 03_simulates/          # 背景合成后的图片
│   └── simulate_*.jpg
└── 04_jsonl/              # 最终训练数据JSON
    ├── income-template_format.json      # 初始格式
    ├── income-template_llava_format.json # LLaVA格式
    └── income-template_mllm_format.json  # MLLM格式
```

### 2. DataMate统一管理目录

通过 `datamate_output_dir` 参数指定，算子会自动将生成的数据复制到该目录：
- `income_certificate/income-template_format.json`
- `income_certificate/income-template_llava_format.json` (或 mllm)
- `income_certificate/output/` (完整输出目录)

## 输出数据格式

### LLaVA格式示例

```json
[
  {
    "id": "income_001",
    "image": "path/to/simulate_001.jpg",
    "conversations": [
      {
        "from": "human",
        "value": "<image>\n请识别这张收入证明中的员工姓名和月收入。"
      },
      {
        "from": "gpt",
        "value": "经过识别，该收入证明中：\n员工姓名：张三\n月收入：人民币15,000元（壹万伍仟元整）"
      }
    ]
  }
]
```

### MLLM格式示例

```json
[
  {
    "id": "income_001",
    "image": "path/to/simulate_001.jpg",
    "question": "请识别这张收入证明中的员工姓名和月收入。",
    "answer": "员工姓名：张三\n月收入：人民币15,000元（壹万伍仟元整）"
  }
]
```

## 依赖环境

### Python版本
- Python 3.8+

### 系统依赖

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
playwright install chromium
```

**Windows**:
```powershell
# 安装poppler（下载并添加到PATH）
# https://github.com/oschwartz10612/poppler-windows/releases/
playwright install chromium
```

**macOS**:
```bash
brew install poppler
playwright install chromium
```

### Python依赖

详见 `requirements.txt`：
- python-docx: Word文档处理
- faker: 随机数据生成
- Pillow: 图像处理
- opencv-python: 图像处理
- playwright: 跨平台Word转图片

## 算子结构

```
income_certificate_generator/
├── __init__.py              # 算子注册文件
├── metadata.yml             # 算子元数据和UI配置
├── process.py               # DataMate算子入口
├── requirements.txt         # Python依赖
├── README.md                # 算子说明文档
├── main.py                  # 主逻辑脚本
├── 1_process1.py           # Word生成
├── 2_process2.py           # Word→JPG转换
├── 3_process3.py           # 添加印章
├── 4_process4.py           # 背景合成
├── 5_process5.py           # 格式转换
├── template/               # 模板文件
│   └── income-template.docx
├── backgrounds/            # 背景图片库
│   ├── 正常_1.jpg
│   ├── 斜拍_1.jpg
│   └── ...
├── data/                   # 配置数据
│   └── coordinates.json
├── common/                 # 公共工具函数
│   ├── __init__.py
│   ├── 1_mark_background_coordinates.py
│   ├── 2_composite_with_background.py
│   ├── convert_to_image.py
│   └── add_seal.py
└── output/                 # 输出目录（运行时生成）
    ├── 01_words/
    ├── 02_images/
    ├── 03_simulates/
    └── 04_jsonl/
```

## 性能指标

- **生成速度**：2-3秒/张
- **内存占用**：约500MB
- **CPU占用**：约1核
- **推荐并发**：1-2个实例

## 常见问题

### Q1: Linux环境提示缺少poppler？
**A**: 安装poppler-utils：
```bash
sudo apt-get install poppler-utils
```

### Q2: Word转图片失败？
**A**: 确保已安装Playwright浏览器：
```bash
playwright install chromium
```

### Q3: 生成的图片中文乱码？
**A**: 确保系统已安装中文字体：
```bash
# Linux
sudo apt-get install fonts-wqy-zenhei

# 或在template中指定字体
```

### Q4: 如何自定义模板？
**A**: 替换 `template/income-template.docx`，并更新 `data/coordinates.json` 中的坐标信息。

### Q5: 如何添加更多背景图？
**A**: 将背景图片放到 `backgrounds/` 目录，支持jpg/png/jpeg/webp格式。

## 更新日志

### v1.0.0 (2024-01-28)
- ✅ 首次发布
- ✅ 支持收入证明批量生成
- ✅ 支持LLaVA和MLLM格式输出
- ✅ 跨平台兼容（Linux/Windows/macOS）
- ✅ 双路输出（算子目录 + DataMate统一管理）

## 许可证

MIT License

## 作者

DataMate Team

---

如有问题或建议，请联系 DataMate 开发团队。
