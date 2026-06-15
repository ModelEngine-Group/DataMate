# data_synthesis 项目说明

## 1. 项目简介

`data_synthesis` 是医疗数据生成工程，主要用于：

- 生成三类训练数据：`QA`、`CoT`、`Preference`
- 进行数据工程处理：增强（augmentation）、蒸馏（distillation）、配比（mix ratio）

---

## 2. 目录与文件作用

### 2.1 核心代码

- `data_synthesizer.py`  
  数据合成主引擎。包含三类模板、批量生成、JSON 清洗、字段校验、失败修复、确定性兜底、数据增强/蒸馏/配比逻辑。

### 2.2 运行与交付脚本

- `final_delivery_part1.py`  
  第一阶段交付主流程：按任务比例批量生成数据，输出 JSON/CSV/PNG/summary 等交付物。

- `benchmark_and_visualize.py`  
  批量压测与可视化报告脚本，统计不同任务的平均时延与成功率。

- `run_50_each_test.py`  
  稳定性测试脚本。默认每类任务运行 50 条，输出成功/失败明细与汇总结果到 `output/`。

### 2.3 数据与验证工具

### 2.4 依赖与环境脚本

- `download.py`  
  从 ModelScope 下载模型到本地缓存，支持控制是否下载训练中间产物。

- `docker.sh`  
  Ascend 容器启动参考脚本（设备挂载、代理、环境变量等）。

### 2.5 文档与数据文件

- `output/`  
  运行输出目录（示例：`generated_*.json`、`summary.json`、`result.txt` 等）。

- `__pycache__/`  
  Python 缓存目录，可忽略。

---

## 3. 运行前准备

1. 建议在 Ascend + Python 3.11 环境执行。
2. 安装基础依赖（至少包含）：`vllm`、`jinja2`、`pandas`、`matplotlib`。
3. 准备可用模型路径：
   - 可通过环境变量 `MODEL_PATH` 指定；
   - 若未指定，脚本会按内置候选路径自动查找。

---

## 4. 常用运行方法

在当前目录执行（`hw_project/data_synthesis`）：

1) 生成金标准数据集：

`python prepare_golden_data.py`

2) 快速压测与可视化：

`python benchmark_and_visualize.py`

3) 执行交付主流程（批量生成 + 报告落盘）：

`python final_delivery_part1.py`

4) 三任务各 50 条稳定性测试：

`python run_50_each_test.py`

5) 下载模型（可选）：

`python download.py --model_id testUser/Qwen3-1.7b-Medical-R1-sft --cache_dir ~/.cache/modelscope`

---

## 5. 主要输出说明

- `generated_qa.json` / `generated_cot.json` / `generated_preference.json`：生成成功样本
- `failed_*.json`：失败样本及失败原因
- `benchmark_metrics.csv`：明细指标（任务类型、时延、状态等）
- `visual_report.png` / `benchmark_report_batch.png`：可视化报告
- `summary.json` / `result.txt`：汇总统计与达标判定

---

## 6. 注意事项

- `CoT` 任务通常比 `QA` 延时更高，属于正常现象。
- `Preference` 对质量要求更高，脚本中对弱兜底有抑制策略，失败率可能略高于 QA。
- 若模型输出不规范 JSON，系统会自动触发“修复阶段”和必要兜底。
- 生成结果的模型化质量评估由独立的 `data_quality_evaluator` 算子和 `data_quality_evaluator_service` 提供。
