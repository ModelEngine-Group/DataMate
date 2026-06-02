# unstructuredio NPU 环境自检报告

## 自检环境

- 服务器：910b-jss
- 测试容器：huizhi
- 测试目录：/home/o_pengjunjie/huizhi
- NPU 选择：ASCEND_RT_VISIBLE_DEVICES=6

## 已验证通过

- Torch-NPU 可用：`torch_npu==2.7.1` 可正常 import。
- Torch NPU 设备可用：`torch.npu.is_available()` 返回 True。
- YOLOX PT 版面模型文件存在：`/home/o_pengjunjie/huizhi/unstructuredio_models/yolox_l.pt`。
- YOLOX 源码目录存在：`/home/o_pengjunjie/huizhi/unstructuredio_models/YOLOX-main`。
- PaddleOCR 本地模型目录存在：det、rec、cls 三类模型均已放置。
- `check_npu_runtime.py` 已采用子进程隔离检查 Torch-NPU 与 Paddle-NPU，并注入 Ascend/NNAL 动态库路径，避免同进程冲突和库路径误判。`process.py` 主进程和 `ocr_npu_adapter.py` worker 也已统一注入 Ascend/NNAL 动态库路径。

## 当前未通过项

### PaddleOCR-NPU

当前 `huizhi` 容器中版本如下：

- `paddlepaddle==3.3.1`
- `paddle-custom-npu==3.3.0`
- `paddleocr==2.7.3`
- CANN/driver：CANN 8.5.1，driver 25.5.2

现象：加载 `paddle-custom-npu` 时进入 `aclInit/rtGetDevMsg` 初始化失败：

```text
Call aclInit(nullptr) failed : 500000 at file /paddle/backends/npu/runtime/runtime.cc line 403
```

已确认 `check_npu_runtime.py` 会注入 Ascend/NNAL 动态库路径，因此该问题不是模型路径缺失，也不是 `libmki.so` / `LD_LIBRARY_PATH` 缺失，而是当前 Paddle custom NPU 组件与容器/驱动组合的兼容问题。

补充验证：已在独立临时容器 `huizhi-paddle30-venv` 中创建隔离 venv，并按 Paddle 官方 NPU 推荐组合安装：

- `paddlepaddle==3.0.0`
- `paddle-custom-npu==3.0.0`
- `paddleocr==2.7.3`

该组合仍在 `rtGetDevMsg/aclInit` 阶段失败，错误同样为：

```text
chipType=0 does not support get device msg feature
Call aclInit(nullptr) failed : 500000 at file /paddle/backends/npu/runtime/runtime.cc line 403
```

因此当前阻塞点不是算子代码、OCR 模型路径、动态库路径，也不是单纯的 Paddle 3.3/3.0 版本选择，而是 910b-jss 当前主机驱动/CANN/设备信息接口与 Paddle custom NPU runtime 不兼容。

### DOCX 严格模式

当前 `huizhi` 容器没有 `soffice` / LibreOffice。DOCX/DOC 严格模式需要先转 PDF 再复用 PDF NPU 链路，因此缺少 `soffice` 时会直接失败，不会静默回退 CPU fast path。

## 算子行为

- 普通模式：优先尝试 NPU 链路；NPU/OCR 不可用时回退 `fast/auto`，并在 `mode` 中标识 fallback。
- 严格模式：设置 `requireNpuModels=true` 或 `UNSTRUCTUREDIO_REQUIRE_NPU_MODELS=1` 后，任何 NPU 组件不可用都会直接失败；DOCX/DOC 严格模式只接受完整 `pdf-npu-ocr-hi_res` 视觉链路，不接受只有版面 NPU、OCR 未走 NPU 的结果。
- 当前交付不会把 PaddleOCR-NPU 误报为成功。

## 建议验收环境要求

- 使用与 Paddle 官方 NPU wheel 匹配的 CANN/driver/container 组合，或直接使用 Paddle 官方 NPU 标准镜像。
- 预置 `paddlepaddle`、`paddle-custom-npu`、`paddleocr`，并通过 `python check_npu_runtime.py` 验证 `paddle` 与 `paddleocr` 均可 import。
- DOCX/DOC 严格验收需安装 `LibreOffice/soffice`。
- 模型路径按 README 说明挂载到 `/models/unstructuredio/...` 或用环境变量覆盖。
