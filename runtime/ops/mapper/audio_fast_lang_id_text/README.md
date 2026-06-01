# AudioFastLangIdText 快速语言识别文本输出（中英）算子

## 概述

AudioFastLangIdText 用于对单个音频文件做快速语言识别（仅输出 `zh/en`），复用 `audio_preprocessor/src/utils/fast_lang_id.py` 的 SpeechBrain 推理逻辑。该算子用于单独运行，最终导出当前文件对应的语言标签 `.txt`，并会用标签文本替换音频输出。

## 功能特性

- **快速推理**：支持只截取前 N 秒进行判断
- **仅输出 zh/en**：中文相关语言码统一映射为 `zh`，其他映射为 `en`
- **一入一出**：每个输入音频输出一个 `.txt`，内容为 `zh` 或 `en`
- **结构化输出**：结果同步写入 `ext_params.audio_lid.lang`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| modelSource | input | /models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa | SpeechBrain LID 本地模型目录 |
| modelSavedir | input | /models/AudioOperations/lid/_speechbrain_cache | 模型缓存目录 |
| device | select | cpu | 推理设备（cpu/cuda/npu） |
| batchSize | inputNumber | 1 | 批大小（单文件时通常为 1） |
| maxSeconds | inputNumber | 3.0 | 只取前 N 秒做判断，0=全长 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - `sample["text"] = "zh" | "en"`，并导出为当前输入文件对应的 `.txt`
  - `sample["ext_params"]["audio_lid"]["lang"] = "zh" | "en"`

## 依赖说明

- **Python 依赖**：`torch`、`torchaudio`、`speechbrain`
- **模型依赖**：SpeechBrain LID 权重需在固定本地目录中可访问

## 版本历史

- **v1.0.0**：首次发布，支持中英二分类 LID 输出
