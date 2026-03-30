# AudioAsrPipeline 音频预处理与中英ASR流水线算子

## 概述

AudioAsrPipeline 将 `audio_preprocessor` 的推荐流水线封装为一个 DataMate Mapper 算子：标准化、（可选）降噪、（可选）异常过滤、语言识别、切分、ASR 识别与合并。最终合并文本写入 `sample["text"]`，并在 `ext_params` 中记录中间产物路径，便于排查与验收。

## 功能特性

- **端到端流水线**：normalization →（可选）GTCRN →（可选）异常过滤 → LID → split → ASR → merge
- **可配置**：每个关键步骤参数化（降噪开关、过滤阈值、LID 截断秒数、切分长度、ASR 设备等）
- **结果可追溯**：中间产物路径记录在 `ext_params.audio_asr.artifacts`
- **面向验收**：输出合并转写文本到 `sample["text"]`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| doDenoise | switch | false | 是否启用 GTCRN 降噪 |
| denoiseModelPath | input | (空) | GTCRN ONNX 模型绝对路径（启用降噪时必填） |
| doAnomalyFilter | switch | true | 是否启用异常语音检测与过滤 |
| minDur | inputNumber | 1.0 | 最小时长（秒） |
| maxDur | inputNumber | 20000.0 | 最大时长（秒） |
| silenceRatioTh | slider | 0.8 | 静音帧比例阈值（0~1） |
| silenceRmsRatioTh | slider | 0.05 | 静音判定阈值比例 |
| lidModelSource | input | (空) | SpeechBrain LID 模型 source（本地目录或 HF repo） |
| lidDevice | select | cpu | LID 推理设备（cpu/cuda/npu） |
| lidMaxSeconds | inputNumber | 3.0 | LID 只取前 N 秒，0=全长 |
| maxSegmentSeconds | inputNumber | 120 | 切分最大秒数 |
| asrDevice | select | auto | ASR 设备参数（auto/cpu/npu） |

## 输入输出

- **输入**：`sample["filePath"]`（音频文件路径）
- **输出**：
  - `sample["text"]`：合并后的转写文本（来自 `merged_text.txt`）
  - `sample["ext_params"]["audio_asr"]`：
    - `lang`：LID 结果（zh/en）
    - `artifacts`：中间产物路径（normalized/denoise/lid/split/asr/merged_text）

## 依赖说明

- **Python 依赖**（按启用功能而定）：
  - normalization/切分：`pydub`、`soundfile`、`numpy`
  - LID：`torch`、`torchaudio`、`speechbrain`
  - 降噪：`onnxruntime`（以及 GTCRN 模型文件）
- **系统依赖**：
  - `pydub` 通常需要 `ffmpeg`

## 版本历史

- **v1.0.0**：首次发布，支持音频标准化/（可选）降噪/过滤/LID/切分/ASR/合并

