# AudioQuantizeEncode 量化编码与重采样算子

## 概述

AudioQuantizeEncode 用于将音频重采样到指定采样率，并编码为 WAV PCM（8/16/24/32 bit）。输出文件写入 `export_path`，并更新 `sample` 中的文件路径与类型字段，便于后续算子继续处理或直接导出。

## 功能特性

- **重采样**：支持转换到指定采样率（Hz）
- **量化编码**：支持 WAV PCM 8/16/24/32 bit
- **声道转换**：支持 mono/stereo（或保持原声道）
- **覆盖策略**：可选覆盖同名输出

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| sampleRate | inputNumber | 16000 | 目标采样率（Hz），0=保持原采样率 |
| bitDepth | select | 16 | WAV PCM 位深：8/16/24/32 |
| channels | inputNumber | 1 | 目标声道数：1/2，0=保持 |
| overwrite | switch | false | 输出同名文件是否覆盖 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - 输出文件：写入 `sample["export_path"]`（输出扩展名固定为 `.wav`）
  - 更新字段：`sample["filePath"]` / `sample["fileType"]="wav"` / `sample["fileName"]` / `sample["fileSize"]`

## 依赖说明

- **Python 依赖**：`soundfile`、`numpy`、`torch`（用于重采样实现）

## 版本历史

- **v1.0.0**：首次发布，支持重采样与 WAV PCM 量化编码

