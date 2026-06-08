# AudioFormatConvert 音频格式转换与重采样算子

## 概述

AudioFormatConvert 处理输入音频，将结果转换为指定音频格式，并由 DataMate 标准导出流程保存。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetFormat | select | wav | 目标输出格式（扩展名） |
| sampleRate | inputNumber | 16000 | 目标采样率（Hz），0 表示保持原采样率 |
| channels | inputNumber | 1 | 目标声道数：1=单声道，2=双声道，0=保持原声道 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：`pydub==0.25.1`、`soundfile==0.12.1`、`numpy==2.2.6`，由 DataMate 运行环境提供。
- **系统依赖**：`ffmpeg`，由 DataMate 运行环境提供，用于 mp3/aac/m4a 等格式解码与编码。

## 版本历史

- **v1.0.0**：首次发布
