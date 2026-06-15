# data_quality_evaluator 测试用例

本目录提供 30 个基于公开数据集整理的中文测试样例，用于在 DataMate 平台上验证 `data_quality_evaluator` 算子对 `QA`、`CoT`、`Preference` 三类数据的质量评估能力。

所有输入文件均为 UTF-8 编码，内容为可直接阅读的中文，可直接用于平台上传和回归测试。

## 数据来源

- HealthCareMagic-100k: https://huggingface.co/datasets/lavita/ChatDoctor-HealthCareMagic-100k
- MedQuAD: https://github.com/abachaa/MedQuAD
- cMedQA2: https://github.com/zhangsheng93/cMedQA2
- PubMedQA: https://github.com/pubmedqa/pubmedqa
- medical-o1-reasoning-SFT: https://huggingface.co/datasets/FreedomIntelligence/medical-o1-reasoning-SFT

## 使用方式

1. 在验收平台中选择 `data_quality_evaluator` 算子。
2. 从 DataMate 上传本目录下的 `example_input` 测试文件。
3. 可单独使用 `dq_case_*.json` 逐条验证，也可使用 `public_eval_cases.json` 进行打包测试。
4. 运行参数建议设为 `targetDimensions=accuracy,relevance,safety,diversity,completeness`。
5. 服务端应开启 `evaluatorBackend=vllm`，模型路径为 `/model/Qwen/Qwen2.5-7B-Instruct`。
6. 输出结果应包含 `record_count`、`results`、`summary`、`runtime` 等字段，且各条记录均有评分结果。

## 目录说明

- `cases.json`：30 个公开测试 case 的元数据清单。
- `example_input/dq_case_*.json`：单样本测试文件，覆盖 `QA`、`CoT`、`Preference` 三类输入。
- `example_input/public_eval_cases.json`：4 条汇总示例，适合快速自检。
