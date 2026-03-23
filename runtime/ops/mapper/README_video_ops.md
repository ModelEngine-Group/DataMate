# DataMate 视频算子说明

## 1. 模块概述

本模块为 DataMate 提供视频数据清洗与视频 AI 辅助标注相关算子，覆盖视频预处理、敏感内容检测与裁剪、多目标跟踪、主体跟踪裁剪、关键帧提取、OCR、ASR、视频分类、视频摘要、事件标注等能力。

所有视频算子均按照 DataMate 算子规范组织在 `runtime/ops/mapper/` 目录下，每个算子目录包含以下标准文件：

- `__init__.py`
- `metadata.yml`
- `process.py`

视频算子共用的基础能力统一放置于：

- `runtime/ops/mapper/_video_common/`

---

## 2. 已实现算子

### 2.1 视频清洗与预处理
- `video_format_convert`：视频格式转换
- `video_deborder_crop`：黑边去除与有效区域裁剪
- `video_sensitive_detect`：敏感内容检测
- `video_sensitive_crop`：敏感片段裁剪

### 2.2 跟踪与结构化提取
- `video_mot_track`：多目标跟踪
- `video_subject_crop`：主体跟踪裁剪
- `video_keyframe_extract`：关键帧提取
- `video_audio_extract`：音频提取

### 2.3 OCR / ASR
- `video_subtitle_ocr`：字幕提取
- `video_text_ocr`：显著文字 OCR 提取
- `video_speech_asr`：语音提取 / 语音识别

### 2.4 基于 QwenVL 的视频语义理解
- `video_classify_qwenvl`：视频分类
- `video_summary_qwenvl`：视频摘要提取
- `video_event_tag_qwenvl`：事件标注

---

## 3. 目录结构

```text
runtime/ops/mapper/
├── __init__.py
├── _video_common/
│   ├── __init__.py
│   ├── ffmpeg.py
│   ├── io_video.py
│   ├── log.py
│   ├── model_paths.py
│   ├── paths.py
│   ├── qwen_http_client.py
│   └── schema.py
├── video_audio_extract/
├── video_classify_qwenvl/
├── video_deborder_crop/
├── video_event_tag_qwenvl/
├── video_format_convert/
├── video_keyframe_extract/
├── video_mot_track/
├── video_sensitive_crop/
├── video_sensitive_detect/
├── video_speech_asr/
├── video_subject_crop/
├── video_subtitle_ocr/
├── video_summary_qwenvl/
└── video_text_ocr/
```

---

## 4. 模型管理方式

代码与模型权重分离管理：

- GitHub 仓库中仅保存算子代码、配置与文档；
- 模型权重统一存放于模型库，不直接提交到代码仓库。

对于本地模型类算子，运行时按以下优先级解析模型根目录：

1. `params["model_root"]`
2. 环境变量 `DATAMATE_MODEL_ROOT`
3. 默认兜底目录（如 `/mnt/models`）

对于 QwenVL 相关算子，不在每个算子进程中重复加载模型，而是通过独立 HTTP 服务调用模型能力，以减少重复初始化开销、提升整体执行效率。

---

## 5. 推理方式划分

### 5.1 本地模型类算子
以下算子直接从统一模型根目录读取模型：

- `video_mot_track`
- `video_subject_crop`
- `video_subtitle_ocr`
- `video_text_ocr`
- `video_speech_asr`

### 5.2 QwenVL 服务类算子
以下算子通过独立 HTTP 服务进行推理：

- `video_sensitive_detect`
- `video_classify_qwenvl`
- `video_summary_qwenvl`
- `video_event_tag_qwenvl`

---

## 6. 运行环境说明

当前视频模块涉及两类运行环境：

### 6.1 DataMate 视频算子运行环境
主要用于视频算子本体执行，涉及能力包括：

- OpenCV
- FFmpeg 相关依赖
- YOLO / Ultralytics
- PaddleOCR
- ONNX Runtime
- Faster-Whisper / ASR 相关依赖

### 6.2 QwenVL 服务运行环境
主要用于独立的 QwenVL HTTP 服务，包括：

- Flask
- Transformers
- Qwen-VL 相关依赖
- Torch 及设备运行时相关依赖

---

## 7. 典型输出结果

不同算子的输出可能包括：

- 裁剪后视频
- 转码后视频
- `tracks.json`
- `summary.json`
- `events.json`
- `subtitles.srt`
- OCR 结果文件
- 提取音频文件
- 调试视频 / 可视化结果

---

## 8. QwenVL 服务依赖说明

以下算子依赖独立的 QwenVL HTTP 服务：

- `video_sensitive_detect`
- `video_classify_qwenvl`
- `video_summary_qwenvl`
- `video_event_tag_qwenvl`

该服务会在启动时预加载模型，并在内存中常驻，从而避免多个算子重复加载同一大模型。

---


