# AudioQuantizeEncode 量化编码与重采样算子

## 概述

AudioQuantizeEncode 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| sampleRate | inputNumber | 16000 | 目标采样率（Hz），0=保持原采样率 |
| bitDepth | select | 16 | WAV PCM 位深：8/16/24/32 |
| channels | inputNumber | 1 | 目标声道数：1/2，0=保持 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
