# data_quality_evaluator 测试用例

本目录提供公开数据集来源说明和轻量评估样例，用于验收平台复测数据质量评估算子。

## 公开数据集来源

- `cMedQA2`
  中文医学问答数据集，适合验证中文医学 QA 质量评估。
  <https://github.com/zhangsheng93/cMedQA2>
  <https://huggingface.co/datasets/fzkuji/cMedQA2>
- `PubMedQA`
  生物医学问答数据集，适合验证专业医学问答质量评估。
  <https://github.com/pubmedqa/pubmedqa>
  <https://huggingface.co/datasets/qiaojin/PubMedQA>
  <https://arxiv.org/abs/1909.06146>

## 本目录样例

- `example_input/public_eval_cases.json`
  包含 `QA`、`CoT`、`Preference` 三类记录，并包含明显合格与明显不合格样本。
- `cases.json`
  记录测试样例来源、目标维度和验收检查点。

## 平台测试步骤

1. 部署带评估接口的独立服务，确认 DataMate 运行环境能访问服务地址。
2. 在 DataMate 算子市场上传 `../data_quality_evaluator.zip`。
3. 创建任务并上传 `example_input/public_eval_cases.json`。
4. 算子参数使用：
   - `targetDimensions=accuracy,relevance,safety,diversity,completeness`
   - `evaluatorBackend=vllm`
5. 运行任务并下载输出 JSON。

## 检查项

- 输出 JSON 包含 `source_file`、`record_count`、`dimensions`、`results`、`summary`、`status`。
- 每条记录包含 5 个维度评分和理由。
- 明显错误或高风险医学内容应在 `准确性` 或 `安全性` 上给出 0 分。
- 合格样本多数维度应给出 1 分。
- `summary.task_type_counts` 与输入样本类型统计一致。
