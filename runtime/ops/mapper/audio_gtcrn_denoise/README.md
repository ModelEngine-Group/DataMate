# AudioGtcrnDenoise GTCRN 智能降噪算子

## 概述

AudioGtcrnDenoise 封装 `audio_preprocessor` 的 GTCRN ONNX 降噪逻辑，对输入音频进行智能降噪处理。算子会将降噪后的音频写入 `export_path`，并更新 `sample` 文件字段，便于后续链路继续处理。

## 功能特性

- **GTCRN ONNX 推理**：复用 `audio_preprocessor/src/utils/gtcrn_denoise.py`
- **输出文件更新**：写入 `export_path`，更新 `filePath/fileType/fileName/fileSize`
- **覆盖策略**：可选覆盖同名输出

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| modelPath | input | (空) | GTCRN `.onnx` 模型绝对路径；为空则使用默认路径（若存在） |
| outFormat | select | wav | 输出格式（建议 wav） |
| overwrite | switch | false | 输出同名文件是否覆盖 |

## 输入输出

- **输入**：`sample["filePath"]`
- **输出**：
  - 输出文件：写入 `sample["export_path"]`
  - 更新字段：`sample["filePath"]` / `sample["fileType"]` / `sample["fileName"]` / `sample["fileSize"]`

## 依赖说明

- **Python 依赖**：`onnxruntime`、`soundfile`、`numpy`、`torch`
- **模型依赖**：需提供 GTCRN ONNX 模型文件（通常放在模型仓并在运行环境挂载）

## 版本历史

- **v1.0.0**：首次发布，支持 GTCRN ONNX 降噪

