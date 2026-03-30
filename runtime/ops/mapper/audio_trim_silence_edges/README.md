# AudioTrimSilenceEdges 首尾静音裁剪算子

## 概述

AudioTrimSilenceEdges 用于裁剪音频首尾静音区域：通过短时能量阈值判定静音帧，找到首个与末个“有效语音”区间后进行裁剪，并可保留两端 `padMs` 的 padding，避免过度切断。

## 功能特性

- **首尾静音裁剪**：按帧能量阈值从两端向内收缩
- **可保留 padding**：裁剪后两端可保留固定毫秒数
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| frameMs | inputNumber | 30 | 帧长（ms） |
| hopMs | inputNumber | 10 | 帧移（ms） |
| threshDb | slider | -50 | 能量阈值（dB，相对全段峰值） |
| padMs | inputNumber | 50 | 裁剪后两端各保留的静音（ms） |
| outFormat | select | wav | 输出格式（扩展名） |
| overwrite | switch | false | 输出同名文件是否覆盖 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - 输出文件：写入 `sample["export_path"]`
  - 更新字段：`sample["filePath"]` / `sample["fileType"]` / `sample["fileName"]` / `sample["fileSize"]`

## 依赖说明

- **Python 依赖**：`soundfile`、`numpy`

## 版本历史

- **v1.0.0**：首次发布，支持首尾静音裁剪

