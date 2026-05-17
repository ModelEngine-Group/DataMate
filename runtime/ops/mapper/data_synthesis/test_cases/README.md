# data_synthesis 测试用例

本目录提供公开数据集来源说明和轻量可运行样例，用于验收平台复测数据合成算子。

## 公开数据集来源

- `cMedQA2`
  中文医学问答数据集，适合验证中文医学 QA、CoT 和 Preference 数据生成。
  <https://github.com/zhangsheng93/cMedQA2>
  <https://huggingface.co/datasets/fzkuji/cMedQA2>
- `PubMedQA`
  生物医学问答数据集，适合验证专业医学英文文本生成。
  <https://github.com/pubmedqa/pubmedqa>
  <https://huggingface.co/datasets/qiaojin/PubMedQA>
  <https://arxiv.org/abs/1909.06146>

## 本目录样例

- `example_input/cmedqa2_style_case_cn.txt`
  基于 `cMedQA2` 场景整理的中文医学问答输入。
- `example_input/pubmedqa_style_case_en.txt`
  基于 `PubMedQA` 场景整理的英文医学问答输入。
- `cases.json`
  记录测试样例来源、推荐任务类型和验收检查点。

## 平台测试步骤

1. 部署 `data_synthesis` 独立服务，确认 DataMate 运行环境能访问服务地址。
2. 在 DataMate 算子市场上传 `../data_synthesis.zip`。
3. 创建任务并上传 `example_input/` 下任一文本文件。
4. 算子参数设置 `taskTypes=QA,CoT,Preference`。
5. 运行任务并下载输出 JSON。

## 检查项

- 输出 JSON 包含 `source_file`、`task_types`、`results`、`status`。
- `results.QA`、`results.CoT`、`results.Preference` 均非空。
- `QA` 至少包含 `question`、`answer`。
- `CoT` 至少包含 `question`、`rationale`、`final_answer`。
- `Preference` 至少包含 `question`、`chosen`、`rejected`、`preference_reason`。
- 失败样本应标记为 `failed`，不应伪装成成功结果。
