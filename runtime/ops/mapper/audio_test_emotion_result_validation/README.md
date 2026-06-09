# AudioTestEmotionResultValidation 情感识别结果验证算子

该算子用于验证 `audioOps-语音情感识别` 默认模式输出的数据集。

默认情感识别算子会把每个音频转成一个 `.txt`，文本内容是预测英文情感标签。本验证算子读取该标签，并从 RAVDESS 文件名解析真实情感，计算逐文件是否正确和整体准确率。

## RAVDESS 文件名规则

示例：

```text
03-01-06-01-02-02-08.wav
```

第 3 段是情感编号：

| 编号 | 情感 |
|---|---|
| 01 | neutral |
| 02 | calm |
| 03 | happy |
| 04 | sad |
| 05 | angry |
| 06 | fearful |
| 07 | disgust |
| 08 | surprised |

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| validationReportPath | input | /dataset/{dataset_id}/references/emotion_validation.jsonl | 逐文件验证结果 |
| summaryPath | input | /dataset/{dataset_id}/references/emotion_validation_summary.json | 准确率汇总 |

## 输出

- 每个输入 `.txt` 输出一个 JSON 文本，包含 `expected/predicted/correct/accuracy_so_far`
- 同时写入：
  - `references/emotion_validation.jsonl`
  - `references/emotion_validation_summary.json`
