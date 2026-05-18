# AudioFastLangId 快速语言识别（中英）算子

## 概述

AudioFastLangId 用于对单个音频文件做快速语言识别（仅输出 `zh/en`），复用 `audio_preprocessor/src/utils/fast_lang_id.py` 的 SpeechBrain 推理逻辑。算子会把语言结果写入 `ext_params.audio_lid.lang`，并保持当前音频作为输出。

## 功能特性

- **快速推理**：支持只截取前 N 秒进行判断
- **仅输出 zh/en**：中文相关语言码统一映射为 `zh`，其他映射为 `en`
- **链路友好**：写入 `ext_params`，保留当前音频给后续 ASR 使用，并在文件名写入 `__lid_zh/en`
- **单独可用**：作为最后一个节点时导出当前音频，并在文件名中追加 `__lid_zh/en`
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

- **输入**：优先使用上游 `sample["data"]` 音频字节；否则使用 `sample["filePath"]`
- **输出**：
  - 保留当前音频内容，并写入 `ext_params.audio_lid.lang`
  - 导出或传递时文件名追加 `__lid_zh/en`
  - `sample["ext_params"]["audio_lid"]["lang"] = "zh" | "en"`

## 依赖说明

- **Python 依赖**：`torch`、`torchaudio`、`speechbrain`
- **模型依赖**：SpeechBrain LID 权重需在固定本地目录中可访问

## 版本历史

- **v1.0.0**：首次发布，支持中英二分类 LID 输出
