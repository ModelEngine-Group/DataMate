# data_synthesis 独立服务镜像

该目录提供独立 FastAPI 服务镜像构建文件。服务默认监听 `18081`，避免占用已有的 `18080`。

## 构建

```bash
docker build -t data-synthesis-service:latest -f service_image/Dockerfile .
```

## 启动

```bash
docker run -d --name data-synthesis-service-vllm-18081 \
  --network datamate-network \
  -p 18103:18103 \
  -e DATA_SYNTHESIS_SERVICE_PORT=18103 \
  -e DATA_SYNTHESIS_MODEL_PATH=/model/Qwen/Qwen3-4B-Instruct-2507 \
  -e DATA_EVALUATOR_MODEL_PATH=/model/Qwen/Qwen2.5-7B-Instruct \
  -e no_proxy="localhost,127.0.0.1,data-synthesis-service-vllm-18081" \
  -v /mnt/nvme0n1/zcj-data/models:/model \
  data-synthesis-service:latest
```

## 检查

```bash
curl --noproxy "*" http://127.0.0.1:18103/health
```

DataMate 算子默认服务地址：

```text
http://data-synthesis-service-vllm-18081:18103
```
