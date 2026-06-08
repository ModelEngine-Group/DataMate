# AudioTelephonyBandpass 电话带通算子

## 概述

AudioTelephonyBandpass 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| lowHz | inputNumber | 300 | 下截止频率（Hz） |
| highHz | inputNumber | 3400 | 上截止频率（Hz） |
| order | inputNumber | 4 | Butterworth 阶数 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy、scipy（scipy.signal）

## 版本历史

- **v1.0.0**：首次发布
