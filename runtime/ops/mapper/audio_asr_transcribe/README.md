# AudioAsrTranscribe 音频转文本算子

## 概述

AudioAsrTranscribe 是单独的音频转文本算子，只调用 WeNet ASR 模型对输入音频进行识别，并按 DataMate 单样本范式导出当前输入文件对应的一个 `.txt`。`language=auto` 时会读取语言映射文件为每条音频选择中文或英文模型；没有命中语言文件时按中文识别。

该算子不执行格式转换、降噪、异常过滤、语言识别、切分、合并、WER 或关键词召回率评估。输入音频应已经满足所选 ASR 模型的要求。

## 功能特性

- **纯 ASR**：单文件音频直接转文本
- **输入标准化与切片**：识别前将输入音频标准化为 16kHz mono wav，并按最大时长切片后顺序合并文本
- **中英文模型可选**：通过 `language` 选择中文/英文模型；`auto` 读取语言文件，找不到对应音频时按中文识别
- **固定解码**：固定使用 `ctc_greedy_search`
- **固定模型路径**：默认使用 `/models/AudioOperations/asr/aishell` 与 `/models/AudioOperations/asr/librispeech`
- **一入一出**：每个输入音频输出一个 `.txt`，内容为该音频的转写文本
- **结果写回**：转写文本写入 `sample["text"]`，运行信息写入 `ext_params.audio_asr_transcribe`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| language | select | auto | ASR 语言模型（auto/zh/en）。auto 读取语言文件，缺省为 zh |
| languageFilePath | input | /dataset/{dataset_id}/references/language.jsonl | 语言映射 JSONL 文件路径，支持 `{dataset_id}` 占位 |
| zhModelDir | input | /models/AudioOperations/asr/aishell | 中文 ASR 模型目录，需包含 `train.yaml`、`final.pt` 与 `units.txt` |
| enModelDir | input | /models/AudioOperations/asr/librispeech | 英文 ASR 模型目录，需包含 `train.yaml`、`final.pt` 与 `units.txt` |
| maxSegmentSeconds | inputNumber | 120 | ASR 前最大切片秒数，长音频会切片识别再合并 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件
- **输出**：
  - `sample["text"]`：ASR 转写文本，并导出为当前输入文件对应的 `.txt`
  - `sample["ext_params"]["audio_asr_transcribe"]`：语言、语言来源、固定解码模式、模型目录等运行信息

## 语言文件

默认路径为：

```text
/dataset/{dataset_id}/references/language.jsonl
```

如果数据集里使用 `reference/language.jsonl`，算子也会自动查找并读取。
该文件作为数据集侧边配置读取。处理每条音频时，算子会从显式 `languageFilePath`、DataMate 任务清单 `/flow/<task_id>/dataset.jsonl`、源音频所在数据集目录等位置查找并缓存使用。处理任务中的 `{dataset_id}` 可能是目标数据集 ID，因此算子会优先从源文件路径和任务清单反查源数据集。

每行一条 JSON 对象；文件名可以写完整文件名或不带后缀的 stem。

模板示例：

```jsonl
{"file": "aishell_0000.wav", "lang": "zh"}
{"file": "BAC009S0006W0427", "lang": "zh"}
{"file": "1272-128104-0011.flac", "lang": "en"}
```

同时兼容旧的空格、Tab 或逗号分隔格式：

```text
aishell_0000.wav zh
BAC009S0006W0427 zh
1272-128104-0011.flac en
```

语言文件命中时优先级最高，会优先于手动选择的 `zh/en` 参数；未命中时才按手动语言参数、中文的顺序兜底。

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

## 并发与内存

ASR 会加载较大的 WeNet 模型。为避免多 worker 同时加载模型导致 OOM，算子内部固定将真正的 ASR 推理串行化；WeNet 批大小固定为 1。

## 依赖说明

- `torch`
- `torchaudio`
- `numpy`
- `pyyaml`
- `sentencepiece`
- `loguru`

## 版本历史

- **v1.0.0**：首次发布，支持单文件音频转文本
