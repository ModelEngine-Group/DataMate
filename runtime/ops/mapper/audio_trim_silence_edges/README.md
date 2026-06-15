# AudioTrimSilenceEdges 首尾静音裁剪算子

## 概述

AudioTrimSilenceEdges 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| frameMs | inputNumber | 30 | 帧长（ms） |
| hopMs | inputNumber | 10 | 帧移（ms） |
| threshDb | slider | -50 | 能量阈值（dB，相对全段峰值） |
| padMs | inputNumber | 50 | 裁剪后两端各保留的静音（ms） |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
