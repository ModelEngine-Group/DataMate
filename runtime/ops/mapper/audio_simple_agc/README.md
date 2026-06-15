# AudioSimpleAgc 分段 RMS 自动增益算子

## 概述

AudioSimpleAgc 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetRms | slider | 0.05 | 目标 RMS（线性） |
| frameMs | inputNumber | 50 | 帧长（ms） |
| hopMs | inputNumber | 25 | 帧移（ms） |
| maxGain | slider | 10 | 最大线性增益 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
