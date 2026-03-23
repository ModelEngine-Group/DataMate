# 视频算子模型说明

## 1. 基本原则

视频算子采用“代码与模型分离”的管理方式：

- 代码、元数据与说明文档保存在 GitHub 仓库中；
- 模型权重统一存放于模型库或模型存储目录；
- 模型文件不直接提交到代码仓库。

---

## 2. 本地模型的解析方式

对于本地模型类算子，模型根目录按以下优先级解析：

1. `params["model_root"]`
2. 环境变量 `DATAMATE_MODEL_ROOT`
3. 默认兜底目录（如 `/mnt/models`）

算子在确定模型根目录后，再基于相对路径查找具体模型文件或模型目录。

---

## 3. QwenVL 模型管理方式

QwenVL 相关算子不在每个算子进程中直接加载模型，而是通过独立的 HTTP 服务调用模型能力。

其设计目的包括：

- 避免多个算子重复加载同一大模型；
- 降低重复初始化的时间开销；
- 减少整体内存占用；
- 提高分类、摘要、事件标注、敏感检测等算子的复用效率。

---

## 4. 建议的模型组织方式

建议在模型库中按统一相对路径组织模型，例如：

- `yolo/yolov8n.pt`
- `ocr/det`
- `ocr/rec`
- `ocr/cls`
- `asr/...`
- `qwen/Qwen2.5-VL-7B-Instruct`

具体目录名称可根据模型库中的实际组织方式进行调整，但建议在代码与文档中保持一致。

---

## 5. 算子与模型对应关系

### 5.1 本地模型类算子
- `video_mot_track`：依赖目标跟踪模型（如 YOLO）
- `video_subject_crop`：依赖目标跟踪结果或目标跟踪模型
- `video_subtitle_ocr`：依赖 OCR 检测、识别、方向分类模型
- `video_text_ocr`：依赖 OCR 检测、识别、方向分类模型
- `video_speech_asr`：依赖 ASR 模型

### 5.2 QwenVL 服务类算子
- `video_sensitive_detect`：依赖 QwenVL HTTP 服务
- `video_classify_qwenvl`：依赖 QwenVL HTTP 服务
- `video_summary_qwenvl`：依赖 QwenVL HTTP 服务
- `video_event_tag_qwenvl`：依赖 QwenVL HTTP 服务

---

## 6. 部署说明

在部署与运行前，需确保：

- 所需模型已正确放置于模型库或模型目录；
- `model_root` 或 `DATAMATE_MODEL_ROOT` 配置正确；
- QwenVL 相关算子运行前，独立 HTTP 服务已正常启动；
- 模型相对路径与代码中的约定保持一致。

---

## 7. 说明

当前项目中的模型权重未进行参数修改，默认优先复用模型库中已有模型，不重复提交模型权重文件。
