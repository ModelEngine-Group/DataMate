# AudioPreEmphasis 预加重算子

## 概述

AudioPreEmphasis 对音频做一阶预加重滤波（\(y[n]=x[n]-coef \cdot x[n-1]\)），常用于 ASR 前端增强高频信息。算子会将处理后的音频写入 `export_path` 并更新 `sample` 文件字段。

## 功能特性

- **一阶预加重**：系数可配置
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`
- **覆盖策略**：可选覆盖同名输出

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| coef | slider | 0.97 | 预加重系数（常用 0.9~0.99） |
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

- **v1.0.0**：首次发布，支持一阶预加重

