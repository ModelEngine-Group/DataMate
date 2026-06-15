# data_synthesis 测试用例

本目录提供 30 个中文测试用例，用于在 DataMate 平台验证数据合成算子。测试输入均为中文医疗问答、中文病例摘要或中文健康咨询风格文本。

## 公开数据来源参考

- cMedQA2：https://github.com/zhangsheng93/cMedQA2
- medical-o1-reasoning-SFT：https://huggingface.co/datasets/FreedomIntelligence/medical-o1-reasoning-SFT

上述链接用于说明测试样例的数据风格来源；本目录中的输入文件已整理为可直接上传平台的小型中文样例。

## 测试方法

1. 在 DataMate 平台上传并启用 data_synthesis 算子。
2. 只上传 `example_input` 目录下的 `.txt` 输入文件，不要上传 `cases.json`、`README.md` 或整个 `test_cases` 外层目录。
3. 参数 `taskTypes` 填写 `QA,CoT,Preference`。
4. 运行完成后下载结果 JSON。
5. 对照 `cases.json` 中的 `checks` 检查 QA、CoT、Preference 三类结果是否存在、是否为中文、是否没有乱码。

## 目录说明

- `cases.json`：30 个中文测试 case 的清单和验收检查点。
- `example_input/*.txt`：30 个可直接上传 DataMate 的中文输入文件。
