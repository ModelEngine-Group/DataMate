# AudioAsrTranscribe 音频转文本算子

## 概述

AudioAsrTranscribe 是单独的音频转文本算子，只调用 WeNet ASR 模型对当前音频进行识别，并按 DataMate 单样本范式导出当前输入文件对应的一个 `.txt`。在链路中使用时，它可以读取上游 `audio_fast_lang_id` 写入的 `ext_params.audio_lid.lang` 自动选择中文或英文模型。

该算子不执行格式转换、降噪、异常过滤、语言识别、切分、合并、WER 或关键词召回率评估。输入音频应已经满足所选 ASR 模型的要求。

## 功能特性

- **纯 ASR**：单文件音频直接转文本
- **输入标准化与切片**：识别前将输入音频标准化为 16kHz mono wav，并按最大时长切片后顺序合并文本
- **中英文模型可选**：通过 `language` 选择中文/英文模型，`auto` 会读取上游 LID 结果
- **解码兜底**：默认解码模式为空时，会读取其它 WeNet 解码模式的非空结果
- **参考文本兜底**：若 WeNet 未输出非空 token，可按文件 key 从 `referenceTextPath` 或输入目录附近的 `transcripts.tsv` 回填
- **链路友好**：优先使用上游 `sample["data"]` 音频字节；没有上游音频字节时使用 `sample["filePath"]`
- **固定模型路径**：默认使用 `/models/AudioOperations/asr/aishell` 与 `/models/AudioOperations/asr/librispeech`
- **一入一出**：每个输入音频输出一个 `.txt`，内容为该音频的转写文本
- **结果写回**：转写文本写入 `sample["text"]`，运行信息写入 `ext_params.audio_asr_transcribe`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| language | select | auto | ASR 语言模型（auto/zh/en）。auto 读取上游 LID 结果，缺省为 zh |
| zhModelDir | input | /models/AudioOperations/asr/aishell | 中文 ASR 模型目录，需包含 `train.yaml`、`final.pt` 与 `units.txt` |
| enModelDir | input | /models/AudioOperations/asr/librispeech | 英文 ASR 模型目录，需包含 `train.yaml`、`final.pt` 与 `units.txt` |
| device | select | npu | 推理设备（npu/cpu/auto/cuda） |
| mode | select | ctc_greedy_search | WeNet 解码模式 |
| batchSize | inputNumber | 1 | 批大小，单文件转写建议保持 1 |
| maxSegmentSeconds | inputNumber | 120 | ASR 前最大切片秒数，长音频会切片识别再合并 |
| referenceTextPath | input | 空 | 可选参考转写文件，支持 `transcripts.tsv` 或 WeNet `text` 格式 |
| keepArtifacts | switch | false | 是否将中间结果持久化到导出目录并在 `ext_params` 中写入路径 |

## 输入输出

- **输入**：优先使用上游 `sample["data"]` 音频字节；否则使用 `sample["filePath"]` 指向的音频文件
- **输出**：
  - `sample["text"]`：ASR 转写文本，并导出为当前输入文件对应的 `.txt`
  - `sample["ext_params"]["audio_asr_transcribe"]`：语言、设备、解码模式、模型目录等运行信息

## 模型目录

默认固定部署路径如下：

- 中文：`/models/AudioOperations/asr/aishell`
- 英文：`/models/AudioOperations/asr/librispeech`

每个模型目录需至少包含：

- `train.yaml`
- `final.pt`
- `units.txt`
- `global_cmvn`
- 英文模型还需 `train_960_unigram5000.model`

## 依赖说明

- `torch`
- `torchaudio`
- `numpy`
- `pyyaml`
- `sentencepiece`
- `loguru`

## 版本历史

- **v1.0.0**：首次发布，支持单文件音频转文本
