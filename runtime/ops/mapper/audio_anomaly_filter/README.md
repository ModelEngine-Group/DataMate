# AudioAnomalyFilter 异常语音检测与过滤算子

## 概述

AudioAnomalyFilter 用于对音频做快速质量检测，计算时长、静音帧比例与音频可读性，并给出 `quality_flag`。算子不再通过清空 `text/data` 模拟删除文件，而是写入结构化质量标签；下游音频算子可根据标签软跳过异常样本。

## 功能特性

- **时长检测**：支持最小时长/最大时长阈值
- **静音比例检测**：基于短时 RMS 统计静音帧占比
- **可读性检测**：文本文件强行改成 `.wav` 等不可读取音频会被标记为 `invalid`
- **下游门控**：支持让后续音频算子跳过异常样本，符合 DataMate 一文件一输出链路
- **结果结构化输出**：报告写入 `ext_params.audio_quality`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| minDur | inputNumber | 1.0 | 最小时长（秒），小于该值视为异常 |
| maxDur | inputNumber | 20000.0 | 最大时长（秒），大于该值视为异常 |
| silenceRatioTh | slider | 0.8 | 静音帧比例阈值（0~1），>= 阈值视为异常 |
| silenceRmsRatioTh | slider | 0.05 | 静音判定阈值 = global_rms * 该比例 |
| skipInvalidDownstream | switch | true | true=后续音频算子遇到 invalid 软跳过；false=仅打标并继续处理 |

## 输入输出

- **输入**：`sample["filePath"]`（音频文件路径）
- **输出**：
  - `sample["ext_params"]["audio_quality"]`：
    - `quality_flag`: `ok/invalid`
    - `duration/silence_ratio/global_rms/reason/read_error/skip_downstream`
  - 如果该算子为链路最后一个算子：导出当前音频，质量报告写入 `ext_params.audio_quality`
  - 如果该算子位于链路中间：保持当前音频，后续音频算子按 `skip_downstream` 决定是否软跳过

## 依赖说明

- **Python 依赖**：优先 `torchaudio`，兜底 `soundfile`

## 版本历史

- **v1.0.0**：支持时长/静音比例/可读性检测，按 DataMate 链路语义写质量标签并门控下游
