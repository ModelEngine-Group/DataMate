# AudioHumNotch 工频陷波算子

## 概述

AudioHumNotch 用于抑制 50/60Hz 工频哼声，通过陷波滤波器降低电源噪声对语音可懂度的影响。算子会将处理后的音频写入 `export_path` 并更新 `sample` 文件字段。

## 功能特性

- **工频陷波**：支持 50/60Hz 选择
- **可调 Q 值**：控制陷波带宽
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| freqHz | select | 50 | 中心频率（Hz）：50/60 |
| q | slider | 30 | 品质因数，越大陷波越窄 |
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

- **v1.0.0**：首次发布，支持 50/60Hz 工频陷波

