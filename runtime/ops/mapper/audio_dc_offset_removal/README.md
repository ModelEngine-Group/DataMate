# AudioDcOffsetRemoval 去直流分量算子

## 概述

AudioDcOffsetRemoval 对音频波形做直流分量去除（减去全段均值），常用于采集链路的偏置修正。算子会把处理后的音频写入 `export_path` 并更新 `sample` 文件字段。

## 功能特性

- **直流偏置消除**：对全段做减均值处理
- **文件输出更新**：输出写入 `export_path`，并更新 `filePath/fileType/fileName/fileSize`
- **覆盖策略**：可选择是否覆盖同名输出

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
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

- **v1.0.0**：首次发布，支持去直流分量

