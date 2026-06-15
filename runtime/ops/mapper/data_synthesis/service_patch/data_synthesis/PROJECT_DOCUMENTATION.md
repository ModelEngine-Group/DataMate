# 医疗数据合成与评估项目说明文档

## 1. 项目背景与目标

本项目目标是通过**结构调整**与**内容丰富**优化医疗训练数据集，以提升数据对模型训练的贡献度。当前需求聚焦于：

1. 数据合成模板能力：支持 QA、CoT、Preference（偏好数据）三类生成。
2. 数据工程能力：支持数据增强、数据蒸馏、数据配比。
3. 数据质量评估能力：支持多维度质量评估及验收口径统计。
4. 验收要求：
   - 单条平均生成延迟 ≤ 3 秒（目标阈值）
   - 生成准确率 ≥ 90%
   - 问题多样性 ≥ 5 种
   - 问题相关性 ≥ 95%
   - 答案完整性 ≥ 85%
   - 逻辑连贯性 > 85%
   - 评估准确率 > 90%（需求口径下可忽略“逻辑性、区分度”）

---

## 2. 当前实现程度（结论）

### 2.1 已完成项（核心功能）

- ✅ 支持三类数据模板生成：QA / CoT / Preference。
- ✅ 支持数据增强（augmentation）、数据蒸馏（distillation）、数据配比（mix ratio）。
- ✅ 支持合成结果字段完整性校验（按任务类型校验必填字段）。
- ✅ 支持 7 维质量评估框架（准确性、相关性、逻辑性、区分度、安全性、多样性、完整性）。
- ✅ 支持“需求口径准确率”统计（忽略逻辑性与区分度）。
- ✅ 已新增需求测试文件并在容器内通过（4/4）。

### 2.2 部分完成 / 说明项

- ⚠️ 部分验收指标（如真实场景延迟、真实模型准确率）需在目标容器与真实模型上跑批后确认最终数值；
  当前已具备完整统计与判定代码、测试样例与执行入口。
- ⚠️ 编辑器静态导入告警（vllm/pandas/matplotlib）与容器运行环境可能不一致，不影响容器内实测。

---

## 3. 项目结构与职责

目录：`hw_project/data_synthesis/`

- `data_synthesizer.py`：核心数据合成引擎（模板、生成、清洗、校验、数据工程能力）。
- `data_evaluator.py`：质量评估引擎（多维评估、批量评分、准确率汇总）。
- `benchmark_and_visualize.py`：三任务压测与可视化（QA/CoT/Preference）。
- `final_delivery_part1.py`：交付主流程（配比构建、批量生成、产物落盘）。
- `prepare_golden_data.py`：金标准数据集构建（已包含 Preference 样本）。
- `verify_evaluator.py`：评估模型验证（含需求口径准确率）。
- `requirement_metrics.py`：统一指标计算与阈值判定模块。
- `test_project_requirements.py`：需求测试集合（单元测试）。

---

## 4. 功能实现说明（按模块）

## 4.1 数据合成模块：`data_synthesizer.py`

### 已实现功能

1. **三模板生成能力**
   - QA 模板：输出 `question/answer`。
   - CoT 模板：输出 `question/rationale/final_answer`。
   - Preference 模板：输出 `question/chosen/rejected/preference_reason`。

2. **生成后清洗与解析**
   - 去除 markdown 包裹。
   - 提取 JSON 主体（括号配平）。
   - 容错解析（`strict=False` + 换行修复兜底）。

3. **完整性校验**
   - 按 task_type 校验字段是否齐全、是否为空。
   - 不完整时返回 `failed` 并附原因。

4. **数据工程能力（增强/蒸馏/配比）**
   - `_augment_text`：结构改写、重排等轻量增强。
   - `_distill_text`：去冗余、保核心信息。
   - `build_training_corpus`：支持 original/augmented/distilled 三来源按比例混合构建训练语料。

### 关键实现思路

- 通过统一模板映射 `task_templates` + `_render_prompt`，将多任务生成路径统一。
- 通过 `required_fields` + `_validate_generated_data` 提升“数据完整性”质量控制。
- 在数据进入生成前使用 `build_training_corpus` 做“源头可控”的数据工程处理，满足增强、蒸馏、配比需求。

---

## 4.2 质量评估模块：`data_evaluator.py`

### 已实现功能

1. **7维评估能力**
   - 准确性、相关性、逻辑性、区分度、安全性、多样性、完整性。

2. **批量打分能力**
   - 自动笛卡尔展开：样本数 × 评估维度。
   - 批量推理并聚合回样本维度结果结构。

3. **需求口径准确率汇总**
   - `summarize_accuracy(...)`：支持忽略指定维度（默认忽略逻辑性、区分度），并按允许误差计算准确率。

### 关键实现思路

- 评估维度与标准显式配置化（`dimension_criteria`），便于后续调参与规范统一。
- 通过“结构化 JSON 输出约束”降低评估结果后处理复杂度。

---

## 4.3 主交付流程：`final_delivery_part1.py`

### 已实现功能

1. 支持三任务合成（QA/CoT/Preference）。
2. 支持来源配比（`SOURCE_MIX_RATIO`）与任务配比（`TASK_RATIO`）。
3. 统一落盘产物：
   - `generated_qa.json`
   - `generated_cot.json`
   - `generated_preference.json`
   - `benchmark_metrics.csv`
   - `visual_report.png`
   - `summary.json`

### 关键实现思路

- 先构建混合语料池，再按任务比切分输入。
- 每个任务独立计时并记录 per-item latency。
- 用结构化 summary 统一收敛验收关键指标。

---

## 4.4 指标模块：`requirement_metrics.py`

### 已实现功能

1. 指标计算：
   - `avg_latency_sec`
   - `format_integrity_pct`
   - `accuracy_pct`
   - `relevance_pct`
   - `answer_completeness_pct`
   - `logic_consistency_pct`
   - `diversity_count`

2. 阈值判定：`check_project_targets(metrics)`
   - 按项目需求输出每项是否达标（布尔值）。

### 关键实现思路

- 使用评估得分阈值（≥4 分）映射成通过率口径。
- 多样性采用问题去重计数。
- 格式完整性同时考虑状态成功与字段完整。

---

## 4.5 验证与测试

### 1) 评估验证脚本：`verify_evaluator.py`

- 在原有严格/宽松准确率基础上，新增“需求口径准确率（忽略逻辑性、区分度）”。

### 2) 需求测试脚本：`test_project_requirements.py`

覆盖 4 类关键能力：

- 三模板生成功能可用（QA/CoT/Preference）。
- 增强/蒸馏/配比逻辑正确。
- 指标计算与阈值判定逻辑正确。
- 评估准确率“忽略逻辑性、区分度”口径正确。

### 3) 已执行测试结果（容器内）

- 执行命令：
  - `python3.11 -m unittest -v test_project_requirements.py`
- 结果：
  - `Ran 4 tests`
  - `OK`

---

## 5. 需求映射矩阵（需求 -> 实现）

| 需求项 | 实现位置 | 状态 |
|---|---|---|
| QA 生成 | `data_synthesizer.py` | ✅ |
| CoT 生成 | `data_synthesizer.py` | ✅ |
| 偏好数据生成 | `data_synthesizer.py`（Preference 模板） | ✅ |
| 数据增强 | `_augment_text` | ✅ |
| 数据蒸馏 | `_distill_text` | ✅ |
| 数据配比 | `build_training_corpus` | ✅ |
| 质量评估（7维） | `data_evaluator.py` | ✅ |
| 需求口径准确率（忽略逻辑性、区分度） | `summarize_accuracy` + `verify_evaluator.py` | ✅ |
| 指标计算与阈值判定 | `requirement_metrics.py` | ✅ |
| 自动化测试 | `test_project_requirements.py` | ✅ |

---

## 6. 运行说明

## 6.1 进入工作目录

`/work/hw_project/data_synthesis`

## 6.2 推荐解释器

在当前容器中建议使用：

`/usr/local/python3.11.14/bin/python3.11`

## 6.3 典型执行入口

1. 快速三任务压测：`benchmark_and_visualize.py`
2. 主交付流程：`final_delivery_part1.py`
3. 构建金标准：`prepare_golden_data.py`
4. 评估验证：`verify_evaluator.py`
5. 需求测试：`test_project_requirements.py`

---

## 7. 已知限制与后续优化建议

1. **真实验收指标需线上实测**
   - 测试脚本已给出计算口径，但真实指标仍需以目标模型、目标硬件、目标数据规模跑批得到。

2. **评估稳定性可进一步增强**
   - 可加入评估输出重试机制与多次投票机制，降低单次推理波动。

3. **偏好样本可扩展难度层级**
   - 建议加入轻微错误、中等错误、严重错误三档 rejected 生成策略。

4. **数据工程策略可参数化**
   - 增强/蒸馏策略当前为轻量启发式，可扩展为可插拔策略插件。

---

## 8. 本阶段交付结论

项目当前已经从“基础 QA/CoT 生成”升级为“覆盖数据工程 + 偏好学习 + 多维评估 + 指标验收 + 自动化测试”的完整闭环实现，具备进入下一步真实数据与真实模型规模化验收的工程基础。
