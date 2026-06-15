# AudioDcOffsetRemoval 去直流分量算子

## 概述

AudioDcOffsetRemoval 处理输入音频，输出处理后的音频文件。

算子会跳过 `references`/`reference` 目录下的参考文件和普通非音频文件；若遇到扩展名是 `.wav` 但内容不可解码的伪音频，也会软跳过并在 `ext_params.audio_skip` 中记录原因。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| channelMode | select | preserve | `preserve` 按原声道分别减均值；`mono` 先转单声道再处理 |
| offsetThreshold | slider | 0.0 | 最大绝对直流偏移低于该阈值时不处理；0 表示总是处理 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。
- **运行信息**：`sample["ext_params"]["audio_dc_offset_removal"]` 会记录最大直流偏移、是否实际处理等信息。

## 依赖说明

- **Python 依赖**：soundfile、numpy

## 版本历史

- **v1.0.0**：首次发布
