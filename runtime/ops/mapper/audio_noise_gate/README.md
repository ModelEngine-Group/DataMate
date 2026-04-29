# AudioNoiseGate 噪声门算子

## 概述

AudioNoiseGate 基于短时 RMS 做噪声门控：当帧能量低于阈值时，按 `floorRatio` 衰减该帧信号。阈值使用“相对全段峰值”的 dB 表达，适合远场/底噪场景的轻量抑噪。

## 功能特性

- **门控抑噪**：低能量帧按比例衰减
- **阈值表达直观**：阈值为相对峰值的 dB
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| thresholdDb | slider | -45 | 门限（dB，相对全段峰值） |
| frameMs | inputNumber | 20 | 帧长（ms） |
| hopMs | inputNumber | 10 | 帧移（ms） |
| floorRatio | slider | 0.05 | 门控时保留能量比例（0~1） |
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

- **v1.0.0**：首次发布，支持噪声门控

