# data_synthesis 算子源码

本目录是 DataMate 平台上传包中的算子源码。

## 功能

- 读取平台传入的一个文本文件。
- 调用独立部署的 `data_synthesis` 服务。
- 将服务返回的 QA、CoT、Preference 合成结果写成平台输出 JSON 文件。

## 关键参数

- `serviceUrl`
  独立服务 HTTP 地址，默认使用容器网络服务名 `http://data-synthesis-service:18080`。
- `taskTypes`
  生成任务类型，默认 `QA,CoT,Preference`。
- `includeMetrics`
  是否在输出中包含质量指标。
- `timeoutSec`
  调用服务的超时时间。
