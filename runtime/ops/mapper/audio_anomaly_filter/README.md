# AudioAnomalyFilter 异常语音检测与过滤算子

## 概述

AudioAnomalyFilter 用于对音频做快速质量检测，计算时长与静音帧比例，并给出 `quality_flag`。当判定为异常时，可选择直接“过滤”（清空 `text/data`）或“保留但打标”（仅写入报告）。

## 功能特性

- **时长检测**：支持最小时长/最大时长阈值
- **静音比例检测**：基于短时 RMS 统计静音帧占比
- **过滤策略可控**：支持保留异常文件（仅打标）或直接过滤
- **结果结构化输出**：报告写入 `ext_params.audio_quality`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| minDur | inputNumber | 1.0 | 最小时长（秒），小于该值视为异常 |
| maxDur | inputNumber | 20000.0 | 最大时长（秒），大于该值视为异常 |
| silenceRatioTh | slider | 0.8 | 静音帧比例阈值（0~1），>= 阈值视为异常 |
| silenceRmsRatioTh | slider | 0.05 | 静音判定阈值 = global_rms * 该比例 |
| keepInvalid | switch | false | true=保留异常文件仅打标；false=异常则清空 text/data 便于过滤 |

## 输入输出

- **输入**：`sample["filePath"]`（音频文件路径）
- **输出**：
  - `sample["ext_params"]["audio_quality"]`：
    - `quality_flag`: `ok/invalid`
    - `duration/silence_ratio/global_rms/reason`
  - 若 `keepInvalid=false` 且 `quality_flag=invalid`：清空 `sample["text"]` 与 `sample["data"]`

## 依赖说明

- **Python 依赖**：优先 `torchaudio`，兜底 `soundfile`

## 版本历史

- **v1.0.0**：首次发布，支持时长/静音比例检测与过滤策略配置

