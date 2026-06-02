# data\_quality\_evaluator 算子

目录内容

-   `operator_src/` DataMate 平台轻量算子源码。
-   `service_patch/` 独立服务端评估接口相关代码。
-   `example_input/` 手工联调输入样例。
-   `test_cases/` 公开数据集来源说明、轻量评估样例和测试步骤。

## 开源模型链接

-   评估模型 `Qwen/Qwen2.5-7B-Instruct`： [https://huggingface.co/Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct")

说明：数据质量评估使用 `Qwen2.5-7B-Instruct`。

## 独立服务部署

数据质量评估算子复用 `data_synthesis_service` 独立服务，但调用的是 `/evaluate-file` 接口。

依赖说明：

-   `operator_src/requirements.txt` 是 DataMate 轻量算子依赖，只包含 HTTP 调用所需依赖，不包含 `vllm`。
-   `service_patch/data_synthesis_service/requirements.txt` 是独立服务生产依赖。
-   服务基础镜像固定为 `quay.io/ascend/vllm-ascend:v0.18.0rc1`，对应 Python `3.11.14`、CANN `8.5.1`。
-   关键版本包括 `vllm==0.18.0+empty`、`vllm_ascend==0.18.0rc1`、`torch==2.9.0+cpu`、`torch_npu==2.9.0.post1+gitee7ba04`。
-   `service_patch/data_synthesis_service/requirements-base.txt` 只用于无模型的接口冒烟测试，不用于正式验收推理。

推荐模型环境变量：

```bash
DATA_EVALUATOR_MODEL_PATH=/model/Qwen/Qwen2.5-7B-Instruct
DATA_EVALUATOR_BACKEND=vllm
```

`/model` 是容器内模型挂载点。验收方可把本机任意模型目录挂载到容器内 `/model`，或在平台参数 `evaluatorModelPath` 中改为其他容器内路径。

使用 `service_patch/data_synthesis_service/Dockerfile` 构建正式 NPU 服务时，默认已经使用 910b-jss 对标基础镜像和 `requirements.txt`。如要覆盖基础镜像，必须保证新镜像与 `quay.io/ascend/vllm-ascend:v0.18.0rc1` 的 CANN/Python/vLLM 版本一致。

路径说明：

- 仓库内 `operator_src/`、`service_patch/`、`test_cases/` 均按相对路径组织，迁移到其他机器后保持目录结构即可。
- `serviceUrl` 默认值与数据合成一致，为 `http://data-synthesis-service:18080`，表示 Docker 网络服务名；可在 DataMate 算子参数中改为实际可访问地址。
- `/model` 是独立服务容器内模型挂载点，不是主机固定路径；评估模型具体位置由 `DATA_EVALUATOR_MODEL_PATH` 或平台参数 `evaluatorModelPath` 覆盖。
- Dockerfile 中的 `/tmp/requirements*.txt` 只是镜像构建阶段临时文件，不是运行时输入输出路径。

## 如何生成 DataMate 上传包

压缩 `operator_src/` 目录中的全部文件，生成 `data_quality_evaluator.zip` 后上传 DataMate。

压缩包根目录应直接包含：

-   `metadata.yml`
-   `process.py`
-   `__init__.py`
-   `requirements.txt`
-   `README.md`

`service_patch/`、`example_input/`、`test_cases/` 只用于服务部署和验收测试，不放入 DataMate 算子上传包。

## 平台测试

1.  启动带评估接口的独立服务，并确保 DataMate 运行环境能访问 `serviceUrl`。
2.  在 DataMate 算子市场上传按上述规则生成的上传包。
3.  新建任务，上传 `test_cases/example_input/public_eval_cases.json`。
4.  算子参数使用 `targetDimensions=accuracy,relevance,safety,diversity,completeness` 和 `evaluatorBackend=vllm`。
5.  运行任务并下载输出 JSON。
6.  按 `test_cases/README.md` 检查每条记录是否包含 5 个维度评分、理由和汇总信息。
