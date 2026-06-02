# unstructuredio 算子源码

本目录是 DataMate 平台上传包使用的算子源码。

## 功能

- 读取 DataMate 传入的 `filePath` 文件。
- 支持 PDF、DOCX、DOC 及 `unstructured` 可识别的其他文档格式。
- 输出 unstructured 风格 JSON。
- 核心字段包括 `index`、`category`、`text`、`page_number`、`coordinates`、`text_as_html`。

## 执行链路

- PDF 默认优先尝试 `YOLOX PT NPU + PaddleOCR NPU`，解析参数为 `hi_res + yolox + OCR force`。
- 版面检测由 `adapters/npu_adapter.py` 适配，使用 Torch-NPU 加载 YOLOX PT 权重。
- 表格结构识别优先使用本地 `microsoft/table-transformer-structure-recognition` 权重，通过 `TableTransformerConfig + state_dict` 手工加载到 NPU，并将输入张量迁移到同一设备。
- OCR 由 `adapters/ocr_npu_adapter.py` 适配，优先在独立子进程加载 PaddleOCR NPU，避免与主进程 Torch-NPU 冲突；主进程、OCR worker、自检脚本均会注入 Ascend/NNAL 动态库路径。
- 普通模式下，NPU/OCR 不可用或输出明显不合格时可回退到 `fast/auto`，保证工程可用。
- 严格模式下，设置 `requireNpuModels=true` 或 `UNSTRUCTUREDIO_REQUIRE_NPU_MODELS=1` 后，PDF 必须走完整 `pdf-npu-ocr-hi_res` 链路；OCR native/Tesseract fallback 被禁用，失败时直接报错。
- DOCX/DOC 严格模式先用 `LibreOffice/soffice` 转 PDF，再复用 PDF NPU 链路；运行环境必须提供 `soffice`，且只接受完整 `pdf-npu-ocr-hi_res`，不接受只有版面 NPU、OCR 未走 NPU 的结果。

## 适配源码

- `adapters/npu_adapter.py`：YOLOX PT 版面模型 NPU 适配、模型加载、Torch-NPU 推理和 `unstructured-inference` 兼容层。
- `adapters/ocr_npu_adapter.py`：PaddleOCR NPU 独立进程适配，并注入 `pytesseract` / `unstructured_paddleocr` 兼容接口代理。
- `adapters/requirements_npu_v1.2_stable.txt`：910B NPU 实验环境依赖版本参考。

## 模型路径

- `UNSTRUCTUREDIO_YOLOX_MODEL_PATH`：默认 `/models/unstructuredio/yolox_l.pt`。
- `UNSTRUCTUREDIO_YOLOX_SRC_PATH`：默认优先查找算子内 `adapters/YOLOX-main`，也支持 `/models/unstructuredio/YOLOX-main`。
- `UNSTRUCTUREDIO_OCR_MODEL_ROOT`：默认 `/models/unstructuredio/paddleocr`。
- `UNSTRUCTUREDIO_OCR_DET_MODEL_DIR`：默认 `/models/unstructuredio/paddleocr/ch_PP-OCRv4_det_infer`。
- `UNSTRUCTUREDIO_OCR_REC_MODEL_DIR`：默认 `/models/unstructuredio/paddleocr/ch_PP-OCRv4_rec_infer`。
- `UNSTRUCTUREDIO_OCR_CLS_MODEL_DIR`：默认 `/models/unstructuredio/paddleocr/ch_ppocr_mobile_v2.0_cls_infer`。
- `UNSTRUCTUREDIO_TABLE_MODEL_PATH`：默认 `/models/unstructuredio/table-transformer-structure-recognition`。

表格结构模型不存在时会关闭 `infer_table_structure`，避免访问远程模型。

## 验证

本目录不随交付提交开发期单测代码；验收测试样例保留在上一级 `test_cases/` 目录。

验收环境自检：

```bash
python operator_src/check_npu_runtime.py
```

严格模式 PDF/DOCX smoke 测试：

```bash
python operator_src/run_strict_pdf_docx_smoke.py test_cases/example_input/attention_is_all_you_need.pdf test_cases/example_input/docx_corpus_sample_1.docx
```

`check_npu_runtime.py` 和 `run_strict_pdf_docx_smoke.py` 用于交付验收环境检查，不放入 DataMate 上传包。DOCX 严格模式要求系统存在 `soffice`。910b-jss 临时 `huizhi` 容器当前已验证 Torch-NPU/YOLOX PT 可用；表格结构识别模型已验证模型参数、输入张量和输出张量均在 `npu:0`，warmup 后单次前向约 0.028 秒；PaddleOCR-NPU 在该容器 `paddlepaddle==3.3.1/paddle-custom-npu==3.3.0` 下于 `aclInit/rtGetDevMsg` 阶段失败。另在独立临时容器中使用 Paddle 官方推荐 `paddlepaddle==3.0.0/paddle-custom-npu==3.0.0` 组合验证，仍失败于同一 `rtGetDevMsg/aclInit` 调用。自检脚本已注入 Ascend/NNAL 动态库路径，因此不是模型路径或 `LD_LIBRARY_PATH` 缺失。严格模式会直接失败，普通模式会明确 fallback。
