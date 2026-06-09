# data_quality_evaluator_service 独立服务

该目录是数据质量评估算子的独立 FastAPI 服务代码，只提供质量评估能力。

## 接口

- `GET /health`
- `POST /evaluate-file`

## 启动

```bash
python -m uvicorn data_quality_evaluator_service.app:app --host 0.0.0.0 --port 18112
```

正式容器建议使用 `data-quality-evaluator-service` 作为容器名，并加入 DataMate 所在 Docker 网络。DataMate 算子默认访问：

```text
http://data-quality-evaluator-service:18112
```

## 依赖

`requirements.txt` 对标已验证的 Ascend/vLLM 环境；DataMate 算子本体不安装 vLLM，只通过 HTTP 调用该独立服务。

## 模型路径

通过环境变量指定模型路径：

- `DATA_QUALITY_EVALUATOR_MODEL_PATH`：数据质量评估模型，默认 `/model/Qwen/Qwen2.5-7B-Instruct`。

容器内建议设置：

```bash
export no_proxy="localhost,127.0.0.1,data-quality-evaluator-service"
```
