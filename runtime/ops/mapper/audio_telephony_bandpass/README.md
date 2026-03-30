# AudioTelephonyBandpass 电话带通算子

## 概述

AudioTelephonyBandpass 用于模拟窄带话机频带（默认 300–3400Hz），突出语音可懂度并抑制低频/高频无关成分。算子依赖 `scipy.signal`，输出写入 `export_path` 并更新 `sample` 文件字段。

## 功能特性

- **带通滤波**：默认 300–3400Hz，可配置上下截止
- **阶数可调**：Butterworth `order` 可配置
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| lowHz | inputNumber | 300 | 下截止频率（Hz） |
| highHz | inputNumber | 3400 | 上截止频率（Hz） |
| order | inputNumber | 4 | Butterworth 阶数 |
| outFormat | select | wav | 输出格式（扩展名） |
| overwrite | switch | false | 输出同名文件是否覆盖 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - 输出文件：写入 `sample["export_path"]`
  - 更新字段：`sample["filePath"]` / `sample["fileType"]` / `sample["fileName"]` / `sample["fileSize"]`

## 依赖说明

- **Python 依赖**：`soundfile`、`numpy`、`scipy`（`scipy.signal`）

## 版本历史

- **v1.0.0**：首次发布，支持电话带通滤波

