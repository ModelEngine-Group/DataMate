# AudioNoiseGate 噪声门算子

## 概述

AudioNoiseGate 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| thresholdDb | slider | -45 | 门限（dB，相对全段峰值） |
| frameMs | inputNumber | 20 | 帧长（ms） |
| hopMs | inputNumber | 10 | 帧移（ms） |
| floorRatio | slider | 0.05 | 门控时保留能量比例（0~1） |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
