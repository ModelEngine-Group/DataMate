# AudioAnomalyFilter 异常语音检测与过滤算子

## 概述

AudioAnomalyFilter 用于对音频做快速质量检测，计算时长、静音帧比例与音频可读性，并给出 `quality_flag`。异常音频会写入输出数据集的 `references/anomaly_report.jsonl`，默认不再输出异常音频；如开启保留开关，则异常音频按原文件名继续输出。

## 功能特性

- **时长检测**：支持最小时长/最大时长阈值
- **静音比例检测**：基于短时 RMS 统计静音帧占比
- **可读性检测**：文本文件强行改成 `.wav` 等不可读取音频会被标记为 `invalid`
- **异常清单**：异常音频以 JSONL 形式写入 `references/anomaly_report.jsonl`
- **过滤开关**：默认过滤异常音频；开启后保留异常音频，文件名不变
- **结果结构化输出**：报告写入 `ext_params.audio_quality`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| minDur | inputNumber | 1.0 | 最小时长（秒），小于该值视为异常 |
| maxDur | inputNumber | 20000.0 | 最大时长（秒），大于该值视为异常 |
| silenceRatioTh | slider | 0.8 | 静音帧比例阈值（0~1），>= 阈值视为异常 |
| silenceRmsRatioTh | slider | 0.05 | 静音判定阈值 = global_rms * 该比例 |
| keepInvalidAudio | switch | false | 是否保留异常音频输出；关闭时只写清单，不输出异常音频 |
| anomalyReportPath | input | /dataset/{dataset_id}/references/anomaly_report.jsonl | 异常清单 JSONL 路径；默认优先写入当前输出数据集的 references |

## 输入输出

- **输入**：`sample["filePath"]`（音频文件路径）
- **输出**：
  - `sample["ext_params"]["audio_quality"]`：
    - `quality_flag`: `ok/invalid`
    - `duration/silence_ratio/global_rms/reason/read_error/keep_invalid_audio/anomaly_report_file`
  - 正常音频：按原文件名输出
  - 异常音频：写入异常清单；默认不输出音频，开启 `keepInvalidAudio` 后按原文件名输出

## 异常清单格式

默认路径：

```text
/dataset/{dataset_id}/references/anomaly_report.jsonl
```

在 DataMate 任务有 `export_path` 时，会优先写入本次输出数据集：

```text
<export_path>/references/anomaly_report.jsonl
```

每行一个 JSON 对象，例如：

```json
{"file":"bad.wav","fileName":"bad.wav","key":"bad","reason":"unreadable_audio,duration_le_zero,too_much_silence","read_error":"RuntimeError: failed to read audio: ...","duration":0.0,"silence_ratio":1.0,"global_rms":0.0,"keep_invalid_audio":false}
```

## 依赖说明

- **Python 依赖**：优先 `torchaudio`，兜底 `soundfile`

## 版本历史

- **v1.0.0**：支持时长/静音比例/可读性检测；异常音频写入 references 清单，可选择过滤或按原名保留
