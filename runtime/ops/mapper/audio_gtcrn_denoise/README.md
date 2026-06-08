# AudioGtcrnDenoise GTCRN 智能降噪算子

## 概述

AudioGtcrnDenoise 处理输入音频，输出处理后的音频文件。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| modelPath | input | /models/AudioOperations/gtcrn/gtcrn.onnx | GTCRN ONNX 模型绝对路径 |

## 输入输出

- **输入**：`sample["filePath"]` 指向的音频文件。
- **输出**：处理后的音频文件。

## 依赖说明

- **Python 依赖**：onnxruntime、soundfile、numpy；模型固定部署路径默认为 /models/AudioOperations/gtcrn/gtcrn.onnx

## 版本历史

- **v1.0.0**：首次发布
