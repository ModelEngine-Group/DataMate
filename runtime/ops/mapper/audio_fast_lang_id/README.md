# AudioFastLangId 快速语言识别（中英）算子

## 概述

AudioFastLangId 用于对音频做快速语言识别（仅输出 `zh/en`），复用 `audio_preprocessor/src/utils/fast_lang_id.py` 的 SpeechBrain 推理逻辑。算子不会改写音频文件，仅将识别结果写入 `ext_params`，方便后续分流到不同 ASR 模型或处理链路。

## 功能特性

- **快速推理**：支持只截取前 N 秒进行判断
- **仅输出 zh/en**：中文相关语言码统一映射为 `zh`，其他映射为 `en`
- **结构化输出**：结果写入 `ext_params.audio_lid.lang`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| modelSource | input | (空) | SpeechBrain 模型 source（本地目录或 HuggingFace repo）；为空使用默认 |
| modelSavedir | input | (空) | 模型缓存目录；为空使用默认 |
| device | select | cpu | 推理设备（cpu/cuda/npu） |
| batchSize | inputNumber | 1 | 批大小（单文件时通常为 1） |
| maxSeconds | inputNumber | 3.0 | 只取前 N 秒做判断，0=全长 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - `sample["ext_params"]["audio_lid"]["lang"] = "zh" | "en"`
  - 不修改 `filePath`（不重写音频）

## 依赖说明

- **Python 依赖**：`torch`、`torchaudio`、`speechbrain`
- **模型依赖**：SpeechBrain LID 权重需在环境中可访问（本地目录或可联网拉取）

## 版本历史

- **v1.0.0**：首次发布，支持中英二分类 LID 输出

