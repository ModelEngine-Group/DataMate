# AudioSoftPeakLimiter 软限幅算子

## 概述

AudioSoftPeakLimiter 对峰值做软限幅（tanh 近似压缩），用于减轻硬削波与爆音风险，常用于播客/通话等内容生产链路的轻量动态控制。

## 功能特性

- **软饱和压缩**：对超过阈值的部分平滑压缩
- **参数可调**：`threshold` 控制线性区阈值，`knee` 控制过渡宽度
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| threshold | slider | 0.92 | 线性区阈值（0~1） |
| knee | slider | 0.08 | 过渡宽度（0~1），越大越柔和 |
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

- **v1.0.0**：首次发布，支持软限幅处理

