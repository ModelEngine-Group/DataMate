# data_synthesis 算子源码

该目录用于打包上传到 DataMate 平台。上传时压缩本目录内的 `__init__.py`、`metadata.yml`、`process.py`、`requirements.txt` 和 `README.md`。

## 功能

- 读取平台传入的一个文本文件。
- 调用独立部署的数据合成 HTTP 服务。
- 输出一个 JSON 文件，包含 `QA`、`CoT`、`Preference` 三类合成结果。

## 参数

- `serviceUrl`：独立服务地址，默认 `http://data-synthesis-service-vllm-18081:18103`。该端口专用于数据合成，避免占用 `18080`。
- `taskTypes`：生成类型，默认 `QA,CoT,Preference`。
- `includeMetrics`：是否附带质量指标，平台批量验收建议保持 `false`。
- `timeoutSec`：单次 HTTP 请求超时，默认 `3600` 秒。
- `lockWaitTimeoutSec`：Ray worker 等待单模型服务锁的最长时间，默认 `7200` 秒，用于覆盖平台批量样本串行排队，超时会直接失败并输出明确错误。

## 说明

DataMate 会通过 Ray 并发处理样本，独立服务内通常只常驻一个大模型实例。算子在 HTTP 调用前使用文件锁串行化请求，避免多 worker 同时请求导致模型服务队列堆积。
