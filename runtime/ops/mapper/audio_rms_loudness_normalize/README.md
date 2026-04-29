# AudioRmsLoudnessNormalize 整段 RMS 归一与峰值顶限算子

## 概述

AudioRmsLoudnessNormalize 先将整段音频 RMS 归一到目标值，再按峰值顶限缩放，避免归一化后出现过大峰值导致削波。适合播客/内容生产等需要统一响度的场景。

## 功能特性

- **整段 RMS 归一**：对齐到 `targetRms`
- **峰值顶限**：按 `peakCeiling` 限制峰值
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetRms | slider | 0.08 | 目标 RMS（线性） |
| peakCeiling | slider | 0.99 | 峰值顶限（0~1） |
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

- **v1.0.0**：首次发布，支持 RMS 归一与峰值顶限

