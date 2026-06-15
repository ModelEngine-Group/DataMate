# AudioFastLangId 快速语言识别（中英）算子

## 概述

AudioFastLangId 用于对音频做快速语言识别（输出 `zh/en`）。算子支持两种输出模式：

- **集成模式**：保留输入音频不改名、不改格式，并把每条音频的语言写入 `references/language.jsonl`，用于后续 `audioOps-音频转文本` 自动选择中文/英文 ASR 模型。
- **独立模式**：每个输入音频输出一个 txt 标签文件，文件内容为 `zh` 或 `en`。

## 功能特性

- **快速推理**：支持只截取前 N 秒进行判断
- **仅输出 zh/en**：中文相关语言码统一映射为 `zh`，其他映射为 `en`
- **链路集成**：集成模式下保留原音频并写入语言文件
- **独立输出**：独立模式下直接输出语言标签 txt
- **幂等写入**：重复运行时按文件名覆盖 `language.jsonl` 中已有记录，不追加重复行

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| outputMode | select | integrated | `integrated` 写语言文件并保留音频；`standalone` 输出 txt 标签 |
| languageFilePath | input | /dataset/{dataset_id}/references/language.jsonl | 集成模式下写入的语言 JSONL 路径；默认优先写入当前任务输出数据集的 `references/language.jsonl` |
| modelSource | input | /models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa | SpeechBrain LID 本地模型目录 |
| maxSeconds | inputNumber | 3.0 | 只取前 N 秒做判断，0=全长 |

## 输入输出

### 集成模式

- **输入**：音频文件
- **输出样本**：仍为原音频，文件名不追加语言标记
- **额外文件**：写入 `languageFilePath`。默认路径会优先落到当前任务输出数据集的 `references/language.jsonl`，每行一个 JSON 对象：

```jsonl
{"file": "aishell_0000.wav", "fileName": "aishell_0000.wav", "key": "aishell_0000", "lang": "zh"}
{"file": "librispeech_0000.wav", "fileName": "librispeech_0000.wav", "key": "librispeech_0000", "lang": "en"}
```

### 独立模式

- **输入**：音频文件
- **输出**：txt 文件，内容为 `zh` 或 `en`

## 推荐编排

`audioOps-快速语言识别（中英）` 使用集成模式后，可直接接 `audioOps-音频转文本`。后者默认会读取 `references/language.jsonl`，按每条音频对应语言选择 ASR 模型。

## 依赖说明

- **Python 依赖**：`torch`、`torchaudio`、`speechbrain`
- **模型依赖**：SpeechBrain LID 权重需在固定本地目录中可访问

## 版本历史

- **v1.0.0**：首次发布，支持中英二分类 LID 输出
- **v1.0.0 更新**：新增集成/独立输出模式；集成模式写入 `language.jsonl` 并保留原音频
