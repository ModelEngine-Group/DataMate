# AudioSimpleAgc 分段 RMS 自动增益算子

## 概述

AudioSimpleAgc 按帧估计 RMS，并将电平拉向目标 RMS，同时限制最大增益，避免过度放大噪声。算子输出写入 `export_path` 并更新 `sample` 文件字段。

## 功能特性

- **帧级 AGC**：按 `frameMs/hopMs` 分析并调节增益
- **增益限制**：通过 `maxGain` 限制放大倍数
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| targetRms | slider | 0.05 | 目标 RMS（线性） |
| frameMs | inputNumber | 50 | 帧长（ms） |
| hopMs | inputNumber | 25 | 帧移（ms） |
| maxGain | slider | 10 | 最大线性增益 |
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

- **v1.0.0**：首次发布，支持分段 RMS AGC

