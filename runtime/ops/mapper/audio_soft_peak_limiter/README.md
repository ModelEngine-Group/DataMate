# AudioSoftPeakLimiter 软限幅算子

## 概述

AudioSoftPeakLimiter 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| threshold | slider | 0.92 | 线性区阈值（0~1） |
| knee | slider | 0.08 | 过渡宽度（0~1），越大越柔和 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
