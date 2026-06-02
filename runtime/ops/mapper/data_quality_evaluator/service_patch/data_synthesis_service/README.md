# data_synthesis_service 服务补丁

本目录归档独立 HTTP 服务中与数据质量评估相关的代码。

## 接口

- `GET /health`
- `POST /synthesize-file`
- `POST /evaluate-file`

## 本地启动示例

```bash
python -m uvicorn data_synthesis_service.app:app --host 0.0.0.0 --port 18080
```

## 依赖

- `requirements.txt` 是独立服务生产依赖，完全对标 910b-jss 已验证镜像 `huizhi:test-v018`。
- 基础镜像固定为 `quay.io/ascend/vllm-ascend:v0.18.0rc1`，对应 Python `3.11.14`、CANN `8.5.1`。
- 关键版本包括 `vllm==0.18.0+empty`、`vllm_ascend==0.18.0rc1`、`torch==2.9.0+cpu`、`torch_npu==2.9.0.post1+gitee7ba04`。
- `requirements-base.txt` 只用于无模型接口冒烟测试。
- `requirements-npu.txt` 是兼容旧文档的别名，等价引用 `requirements.txt`。
- DataMate 算子本体依赖在 `operator_src/requirements.txt`，不应安装 vLLM。

正式 NPU 构建示例：

```bash
docker build -t data-synthesis-service:latest \
  -f data_synthesis_service/Dockerfile .
```

不传构建参数时默认使用 910b-jss 对标基础镜像并安装 `requirements.txt`。无模型接口冒烟测试可显式增加 `--build-arg REQUIREMENTS_FILE=requirements-base.txt`。

Dockerfile 使用 `pip install --no-deps`。这是为了保留 `quay.io/ascend/vllm-ascend:v0.18.0rc1` 中已经验证的 vLLM-Ascend 依赖闭包，避免 pip 重新解析传递依赖导致版本漂移。

## 模型路径

启动服务前通过环境变量指定容器内模型路径：

- `DATA_SYNTHESIS_MODEL_PATH`
- `DATA_EVALUATOR_MODEL_PATH`

默认模型挂载点为容器内 `/model`。

路径说明：

- `data_synthesis_service/` 与 `data_synthesis/` 是构建上下文中的相对源码目录。
- `/model` 是服务容器内模型挂载点，不是主机固定路径；主机模型目录由 Docker `-v` 参数挂载。
- `/tmp/requirements*.txt` 是 Dockerfile 构建阶段临时依赖文件路径。
- `/usr/local/Ascend/...` 是 vLLM-Ascend 基础镜像和宿主机驱动的容器内标准路径；非标准镜像需要提供等价路径。
