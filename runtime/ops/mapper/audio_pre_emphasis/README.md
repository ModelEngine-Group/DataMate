# AudioPreEmphasis 预加重算子

## 概述

AudioPreEmphasis 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| coef | slider | 0.97 | 预加重系数（常用 0.9~0.99） |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
