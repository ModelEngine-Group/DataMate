# unstructuredio 算子

## 目录内容

- `operator_src/`：DataMate 算子源码目录，压缩该目录内指定文件即可上传平台。
- `adapter_src/`：NPU/OCR 适配源码与实验归档。
- `test_cases/`：公开 PDF、DOCX 测试样本和测试说明。

## 已实现功能

- PDF 优先尝试 `hi_res + yolox + OCR force` 链路。
- 版面检测模型使用 YOLOX PT 权重，并通过 `torch_npu` 加载到 NPU。
- 表格结构识别模型使用本地 `microsoft/table-transformer-structure-recognition` 权重，优先通过 `TableTransformerConfig + state_dict` 手工加载到 NPU，避免运行时访问远程模型或额外拉取 ResNet 骨干权重。
- OCR 适配器优先在独立子进程中加载 PaddleOCR NPU，避免 Paddle NPU 与 Torch-NPU 在同一 Python 进程内冲突；主进程、OCR worker、自检脚本均会注入 Ascend/NNAL 动态库路径。
- 普通模式下，如果 NPU/OCR 初始化失败，算子会回退到 `fast/auto`，保证工程可用，并在输出 `mode` 中标明 fallback。
- 严格验收模式下，开启 `requireNpuModels=true` 或 `UNSTRUCTUREDIO_REQUIRE_NPU_MODELS=1` 后，PDF 必须使用完整 `pdf-npu-ocr-hi_res` 链路；OCR native/Tesseract fallback 被禁用，任何 NPU 组件不可用都会直接失败。
- DOCX/DOC 严格模式先使用 `LibreOffice/soffice` 转 PDF，再复用 PDF NPU 视觉解析链路；只接受完整 `pdf-npu-ocr-hi_res`，缺少 `soffice` 或 OCR-NPU 不可用时直接失败，不静默走 CPU fast path。
- 输出保持 unstructured 风格 JSON，核心字段包括 `index`、`category`、`text`、`page_number`、`coordinates`、`text_as_html`。

## 开源模型链接

- 版面检测模型 `unstructuredio/yolo_x_layout`：<https://huggingface.co/unstructuredio/yolo_x_layout>
- 表格结构识别模型 `microsoft/table-transformer-structure-recognition`：<https://huggingface.co/microsoft/table-transformer-structure-recognition>
- YOLOX 上游项目：<https://github.com/Megvii-BaseDetection/YOLOX>
- PaddleOCR：<https://github.com/PaddlePaddle/PaddleOCR>
- PP-OCRv4 模型说明：<https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/ppocr/model_list.md>

## 模型路径

默认使用容器内 `/models` 挂载点，可通过环境变量覆盖：

- `UNSTRUCTUREDIO_YOLOX_MODEL_PATH=/models/unstructuredio/yolox_l.pt`
- `UNSTRUCTUREDIO_YOLOX_SRC_PATH=/models/unstructuredio/YOLOX-main`
- `UNSTRUCTUREDIO_OCR_MODEL_ROOT=/models/unstructuredio/paddleocr`
- `UNSTRUCTUREDIO_OCR_DET_MODEL_DIR=/models/unstructuredio/paddleocr/ch_PP-OCRv4_det_infer`
- `UNSTRUCTUREDIO_OCR_REC_MODEL_DIR=/models/unstructuredio/paddleocr/ch_PP-OCRv4_rec_infer`
- `UNSTRUCTUREDIO_OCR_CLS_MODEL_DIR=/models/unstructuredio/paddleocr/ch_ppocr_mobile_v2.0_cls_infer`
- `UNSTRUCTUREDIO_TABLE_MODEL_PATH=/models/unstructuredio/table-transformer-structure-recognition`

路径说明：

- `operator_src/`、`test_cases/` 等仓库内目录均使用相对路径说明，迁移到其他机器后保持目录结构即可。
- `/models`、`/model` 是容器内模型挂载点，不是主机固定路径。验收方可把主机任意模型目录挂载到该容器内路径，或通过上述环境变量改成其他容器内路径。
- `/tmp` 仅用于运行时临时文件和 Paddle CPU 隔离目录，不承载交付数据；如运行环境限制 `/tmp`，可通过 `TMPDIR` 或 `OCR_ADAPTER_CPU_CUSTOM_DEVICE_ROOT` 调整。
- `/usr/local/Ascend/...` 是 Ascend 驱动、CANN、NNAL 的容器内标准库路径；如镜像路径不同，应先通过容器挂载或 `LD_LIBRARY_PATH` 提供等价路径。
- `HF_ENDPOINT` 默认指向 `https://hf-mirror.com`，只用于拦截/镜像 HuggingFace 请求；正式验收建议本地预置模型，避免运行时访问外网。

表格结构模型不存在时，算子会关闭 `infer_table_structure`，避免运行时访问远程模型；PDF 表格标题仍会做轻量补强和合并。

## NPU 运行依赖

严格 NPU 模式要求运行环境预置：

- Ascend CANN/driver，并能看到至少 1 张 NPU。
- `torch`、`torch-npu`、`torchvision`。
- `paddlepaddle`、`paddle-custom-npu`、`paddleocr`。
- `unstructured`、`unstructured-inference`、`pdf2image`、`pypdfium2`、`pikepdf`、`pi_heif`、`opencv-python-headless`。
- `einops`、`loguru` 和 YOLOX 源码目录。
- DOCX/DOC 严格模式额外要求 `LibreOffice/soffice`。

910b-jss 临时 `huizhi` 容器当前已验证 Torch-NPU 可用，`torch.npu.is_available()` 为 True；YOLOX PT 版面模型可走 Torch-NPU；表格结构识别 `microsoft/table-transformer-structure-recognition` 已验证模型参数、输入张量和输出张量均在 `npu:0`，warmup 后单次前向约 0.028 秒。该临时容器中的 `paddlepaddle==3.3.1`、`paddle-custom-npu==3.3.0` 在加载 NPU custom device 时触发 `aclInit/rtGetDevMsg` 初始化失败。已在独立临时容器 `huizhi-paddle30-venv` 中按 Paddle 官方推荐组合验证 `paddlepaddle==3.0.0`、`paddle-custom-npu==3.0.0`、`paddleocr==2.7.3`，仍失败于同一 `rtGetDevMsg/aclInit` 调用。自检脚本已注入 Ascend/NNAL 动态库路径，因此该问题不是模型路径或 `LD_LIBRARY_PATH` 缺失，而是当前主机驱动/CANN/设备信息接口与 Paddle custom NPU runtime 不兼容。代码会在严格模式下直接失败，普通模式下明确 fallback，不会伪装成 OCR NPU 成功。

## 如何生成 DataMate 上传包

压缩 `operator_src/` 目录中的以下内容生成 `unstructuredio.zip`：

- `metadata.yml`
- `process.py`
- `__init__.py`
- `requirements.txt`
- `README.md`
- `adapters/`

不要把 `tests/`、`test_cases/`、`check_npu_runtime.py`、`run_strict_pdf_docx_smoke.py` 放入 DataMate 算子上传包。

## 平台测试流程

1. 在 DataMate 算子市场上传 `unstructuredio.zip`。
2. 新建数据处理任务，选择 `unstructuredio` 算子。
3. 上传 `test_cases/example_input/` 下的 PDF 或 DOCX 样本。
4. 普通功能测试使用默认参数；严格 NPU 验收测试设置 `requireNpuModels=true`。
5. 下载输出 JSON，检查 `elements[].category`、`text`、`page_number`、`coordinates`、`text_as_html` 和顶层 `mode`。

## 环境自检

交付源码目录提供 `operator_src/check_npu_runtime.py`，用于检查 Python 依赖、模型路径、NPU 组件和 `soffice`：

```bash
cd operator_src
python check_npu_runtime.py
```

该脚本只用于验收环境检查，不放入 DataMate 上传包。脚本采用子进程隔离方式分别检查 Torch-NPU 与 Paddle-NPU，避免两个 NPU 栈在同一 Python 进程内互相污染。

完整 NPU 依赖和 `soffice` 就绪后，可运行严格模式 smoke 测试：

```bash
cd operator_src
python run_strict_pdf_docx_smoke.py ../test_cases/example_input/attention_is_all_you_need.pdf ../test_cases/example_input/docx_corpus_sample_1.docx
```

PDF 期望输出 `mode=pdf-npu-ocr-hi_res`；DOCX 期望输出 `mode=docx-visual-pdf-npu-ocr-hi_res`。
