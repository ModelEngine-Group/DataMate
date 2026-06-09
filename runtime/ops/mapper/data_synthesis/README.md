# data_synthesis 交付目录

本目录包含 DataMate 数据合成算子源码、独立服务补丁、镜像构建文件和测试样例。

## DataMate 上传包

上传到 DataMate 时，只压缩 `operator_src` 目录内文件：

- `__init__.py`
- `metadata.yml`
- `process.py`
- `requirements.txt`
- `README.md`

平台算子默认调用独立服务：

```text
http://data-synthesis-service-vllm-18081:18103
```

## 独立服务部署

服务代码在 `service_patch`，镜像说明在 `service_image`。建议容器名使用 `data-synthesis-service-vllm-18081`，端口使用 `18081`，避免与平台已有 `18080` 服务冲突。

示例：

```bash
docker build -t data-synthesis-service:latest -f service_image/Dockerfile .
docker run -d --name data-synthesis-service-vllm-18081 \
  --network datamate-network \
  -p 18103:18103 \
  -e DATA_SYNTHESIS_SERVICE_PORT=18103 \
  -e no_proxy="localhost,127.0.0.1,data-synthesis-service-vllm-18081" \
  -v /mnt/nvme0n1/zcj-data/models:/model \
  data-synthesis-service:latest
```

健康检查：

```bash
curl --noproxy "*" http://127.0.0.1:18103/health
```

## 模型

数据合成默认使用开源模型 `Qwen/Qwen3-4B-Instruct-2507`。模型放在宿主机模型目录后，通过容器 `/model/...` 路径访问，默认路径为 `/model/Qwen/Qwen3-4B-Instruct-2507`。

## 测试样例

`test_cases/example_input` 下提供 30 个中文文本样例。平台测试时上传任一 `.txt` 文件，参数保持：

```text
taskTypes=QA,CoT,Preference
includeMetrics=false
```
