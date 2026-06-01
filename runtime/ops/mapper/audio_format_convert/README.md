# AudioFormatConvert 音频格式转换与重采样算子

## 概述

AudioFormatConvert 处理输入音频，并将结果写入 `sample["data"]`，同时设置 `sample["target_type"]`。作为链路中间节点时，它保持当前样本仍为音频格式，方便后续 LID/ASR 继续读取；作为最后一个算子时，最终落盘交由 DataMate 标准导出流程负责。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetFormat | select | wav | 目标输出格式（扩展名） |
| sampleRate | inputNumber | 16000 | 目标采样率（Hz），0 表示保持原采样率 |
| channels | inputNumber | 1 | 目标声道数：1=单声道，2=双声道，0=保持原声道 |

## 输入输出

- **输入**：`sample["filePath"]`，若上游算子已产生 `sample["data"]`，则优先处理该音频字节。
- **输出**：`sample["data"]` 为处理后的音频字节；`sample["target_type"]` 为目标音频后缀。

## 依赖说明

- **Python 依赖**：`pydub==0.25.1`、`soundfile==0.12.1`、`numpy==2.2.6`，由 DataMate 运行环境提供。
- **系统依赖**：`ffmpeg`，由 DataMate 运行环境提供，用于 mp3/aac/m4a 等格式解码与编码。

## 版本历史

- **v1.0.0**：首次发布
