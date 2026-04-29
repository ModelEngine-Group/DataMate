# AudioFormatConvert 音频格式转换与重采样算子

## 概述

AudioFormatConvert 用于将常见音频格式互相转换，并支持可选的重采样与声道数转换。算子会把输出文件写入 `export_path`，并更新 `sample` 中的文件路径与类型字段，便于后续算子继续处理。

## 功能特性

- **格式互转**：支持 `wav/flac/mp3/aac/m4a/ogg` 等常见格式互转
- **重采样**：可将采样率转换为指定值（Hz）
- **声道转换**：可转换为单声道/双声道
- **覆盖策略**：可选择是否覆盖 `export_path` 下的同名输出

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetFormat | select | wav | 目标输出格式（扩展名） |
| sampleRate | inputNumber | 16000 | 目标采样率（Hz），0 表示保持原采样率 |
| channels | inputNumber | 1 | 目标声道数：1=单声道，2=双声道，0=保持原声道 |
| overwrite | switch | false | 输出同名文件是否覆盖 |

## 输入输出

- **输入**：`sample["filePath"]`（音频文件路径）
- **输出**：
  - 输出文件：写入 `sample["export_path"]`
  - 更新字段：`sample["filePath"]` / `sample["fileType"]` / `sample["fileName"]` / `sample["fileSize"]`

## 依赖说明

- **Python 依赖**：`pydub`（优先）、`soundfile`、`numpy`、`torch`（用于重采样兜底实现）
- **系统依赖**：`pydub` 通常需要 `ffmpeg` 才能处理 mp3/aac/m4a 等格式

## 版本历史

- **v1.0.0**：首次发布，支持格式互转/重采样/声道转换

