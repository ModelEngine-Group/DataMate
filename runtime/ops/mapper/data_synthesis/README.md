# data\_synthesis 算子

## 目录内容

-   `operator_src/`：DataMate 平台轻量算子源码。
-   `service_patch/`：独立数据合成服务代码。
-   `service_image/`：独立服务镜像构建说明和 Dockerfile。
-   `example_input/`：手工联调输入样例。
-   `test_cases/`：公开数据集来源说明、轻量测试输入和测试步骤。

## 开源模型链接

-   医疗 SFT 模型：[https://www.modelscope.cn/models/zpeng1989/Medical\_Qwen3\_17B\_Large\_Language\_Model](https://www.modelscope.cn/models/zpeng1989/Medical_Qwen3_17B_Large_Language_Model "https://www.modelscope.cn/models/zpeng1989/Medical_Qwen3_17B_Large_Language_Model")
-   公开基座模型 `Qwen/Qwen3-1.7B`：[https://huggingface.co/Qwen/Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B "https://huggingface.co/Qwen/Qwen3-1.7B")

## 调用链路

1.  DataMate 平台上传轻量算子包 `data_synthesis.zip`。
2.  算子读取输入文本文件。
3.  算子通过 HTTP 调用独立服务 `POST /synthesize-file`。
4.  独立服务加载本地模型，生成 QA、CoT、Preference 三类结果。
5.  算子将服务返回的 JSON 写入平台输出文件。

## 依赖与环境

-   `operator_src/requirements.txt` 是 DataMate 轻量算子依赖，只包含 HTTP 调用所需依赖，不包含 `vllm`。
-   `service_patch/data_synthesis_service/requirements.txt` 是独立服务生产依赖。
-   服务基础镜像固定为 `quay.io/ascend/vllm-ascend:v0.18.0rc1`，对应 Python `3.11.14`、CANN `8.5.1`。
-   关键版本包括 `vllm==0.18.0+empty`、`vllm_ascend==0.18.0rc1`、`torch==2.9.0+cpu`、`torch_npu==2.9.0.post1+gitee7ba04`。
-   `service_patch/data_synthesis_service/requirements-base.txt` 只用于无模型接口冒烟测试，不用于正式验收推理。

## 独立服务部署

1.  将医疗 SFT 模型下载到验收机器任意目录。
2.  运行容器时将模型目录挂载到容器内 `/model`。
3.  使用 `service_image/Dockerfile` 构建独立服务镜像。
4.  启动服务后，通过 `serviceUrl` 让 DataMate 算子访问该服务。

构建镜像：

```bash
docker build -t data-synthesis-service:latest -f service_image/Dockerfile .
```

启动服务：

```bash
docker run -d --name data-synthesis-service \
  --privileged \
  --security-opt label=disable \
  --network <datamate-network> \
  -p 18080:18080 \
  --device /dev/davinci6 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/Ascend/driver/lib64/:/usr/local/Ascend/driver/lib64/:ro \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
  -v <host-model-dir>:/model:ro \
  -e ASCEND_VISIBLE_DEVICES=6 \
  -e ASCEND_RT_VISIBLE_DEVICES=6 \
  -e HCCL_OP_EXPANSION_MODE=AIV \
  -e DATA_SYNTHESIS_MODEL_PATH=/model/Qwen/Qwen3-1___7b-Medical-R1-sft \
  data-synthesis-service:latest
```

说明：

-   `<host-model-dir>` 是验收机器上的模型目录，按实际环境替换。
-   `<datamate-network>` 是 DataMate 容器可访问的 Docker 网络；如果不在同一网络，可把算子参数 `serviceUrl` 改成实际可访问地址。
-   `/model` 是容器内模型挂载点，不是主机固定路径。
-   NPU 启动参数默认第 6 号 NPU。使用其他 NPU 时，同步替换 `--device /dev/davinciX`、`ASCEND_VISIBLE_DEVICES` 和 `ASCEND_RT_VISIBLE_DEVICES`。

检查服务：

```bash
curl http://<service-host>:18080/health
```

## 服务接口

默认服务地址：

```text
http://data-synthesis-service:18080
```

主要接口：

-   `GET /health`
-   `POST /synthesize-file`
-   `POST /evaluate-file`

## 如何生成 DataMate 上传包

压缩 `operator_src/` 目录中的全部文件，生成 `data_synthesis.zip` 后上传 DataMate。

压缩包根目录应直接包含：

-   `metadata.yml`
-   `process.py`
-   `__init__.py`
-   `requirements.txt`
-   `README.md`

`service_patch/`、`service_image/`、`example_input/`、`test_cases/` 只用于服务部署和验收测试，不放入 DataMate 算子上传包。

## 平台测试

1.  部署独立服务并确认 `GET /health` 可访问。
2.  在 DataMate 算子市场上传按上述规则生成的上传包。
3.  新建任务，上传 `test_cases/example_input/` 下的文本样例。
4.  算子参数 `taskTypes` 使用 `QA,CoT,Preference`。
5.  运行任务并下载输出 JSON。
6.  按 `test_cases/README.md` 检查三类结果是否存在、字段是否完整，且结果由模型生成，失败时不会伪装为成功。