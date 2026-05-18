# AudioNoiseGate 噪声门算子

## 概述

AudioNoiseGate 处理输入音频，并将结果写入 `sample["data"]`，同时设置 `sample["target_type"]`。输出路径、同名文件处理和最终落盘均交由 DataMate 的标准导出流程负责。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| thresholdDb | slider | -45 | 门限（dB，相对全段峰值） |
| frameMs | inputNumber | 20 | 帧长（ms） |
| hopMs | inputNumber | 10 | 帧移（ms） |
| floorRatio | slider | 0.05 | 门控时保留能量比例（0~1） |

## 输入输出

- **输入**：`sample["filePath"]`，若上游算子已产生 `sample["data"]`，则优先处理该音频字节。
- **输出**：`sample["data"]` 为处理后的音频字节；`sample["target_type"]` 为目标音频后缀。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
