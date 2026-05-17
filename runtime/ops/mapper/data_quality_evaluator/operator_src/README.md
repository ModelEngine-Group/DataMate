# data_quality_evaluator 算子源码

本目录是 DataMate 平台上传包中的算子源码。

## 功能

- 读取平台传入的一个输入文件。
- 将文件内容作为待评估 JSON 文本。
- 调用独立服务的 `/evaluate-file` 接口。
- 将服务返回的评估结果写成平台输出 JSON 文件。

## 关键参数

- `serviceUrl`
  独立服务 HTTP 地址，默认使用容器网络服务名 `http://data-synthesis-service:18080`。
- `targetDimensions`
  评估维度，默认 `accuracy,relevance,safety,diversity,completeness`。
- `evaluatorBackend`
  评估后端，默认 `vllm`。
- `evaluatorModelPath`
  评估模型在服务容器内的路径。
