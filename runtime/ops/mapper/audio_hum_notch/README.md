# AudioHumNotch 工频陷波算子

## 概述

AudioHumNotch 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| freqHz | select | 50 | 中心频率（Hz）：50/60 |
| q | slider | 30 | 品质因数，越大陷波越窄 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy、scipy（scipy.signal）

## 版本历史

- **v1.0.0**：首次发布
