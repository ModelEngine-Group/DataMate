# data_synthesis_service 镜像构建目录

本目录用于构建 `data_synthesis` 独立服务镜像。

## 内容

- `Dockerfile`
  独立服务镜像构建文件。

## 构建上下文

构建镜像时需要将以下源码目录放入同一构建上下文：

- `data_synthesis/`
- `data_synthesis_service/`

当前交付目录不内置大模型文件。运行镜像时需要将验收方本机模型目录挂载到容器内 `/model`，并通过环境变量指定具体模型路径。

镜像基础环境完全对标 910b-jss 已验证镜像 `huizhi:test-v018`，固定使用 `quay.io/ascend/vllm-ascend:v0.18.0rc1`，对应 Python `3.11.14`、CANN `8.5.1`。镜像默认安装 `service_patch/data_synthesis_service/requirements.txt`，其中锁定 `vllm==0.18.0+empty`、`vllm_ascend==0.18.0rc1`、`torch==2.9.0+cpu`、`torch_npu==2.9.0.post1+gitee7ba04`。基础接口冒烟测试可使用 `requirements-base.txt`，但正式验收推理不能使用基础依赖替代。

构建时使用 `pip install --no-deps`，原因是 910b-jss 的 vLLM-Ascend 基础镜像已经内置并验证了一组可工作的依赖闭包。不要让 pip 在构建阶段重新解析 vLLM、vLLM-Ascend、torch-npu 的传递依赖，否则可能改变已验证环境。

## 构建步骤

```bash
docker build -t data-synthesis-service:latest -f service_image/Dockerfile .
```

## 启动步骤

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
  -e DATA_EVALUATOR_MODEL_PATH=/model/Qwen/Qwen2.5-7B-Instruct \
  data-synthesis-service:latest
```

说明：

- `<host-model-dir>` 是验收机器上的模型目录。
- `<datamate-network>` 是 DataMate 容器可访问的 Docker 网络。
- `/model` 是容器内挂载点。
- 上例对标 910b-jss 第 6 号 NPU；如使用其他 NPU，需要同步调整 `--device /dev/davinciX`、`ASCEND_VISIBLE_DEVICES` 和 `ASCEND_RT_VISIBLE_DEVICES`。
- Ascend driver、`npu-smi`、`dcmi` 挂载项对标 910b-jss 的已验证启动方式，正式 NPU 推理不要省略。

路径说明：

- 本目录下的 Dockerfile、README 均使用相对构建上下文，迁移机器后保持 `service_patch/` 与 `service_image/` 的目录结构即可。
- `/model` 是服务容器内模型挂载点，不是主机固定路径；主机模型目录由 `-v <host-model-dir>:/model:ro` 指定。
- `/usr/local/Ascend/...`、`/usr/local/bin/npu-smi`、`/usr/local/dcmi` 是宿主机 Ascend 驱动组件路径；如果验收机器安装路径不同，需要按实际位置调整挂载参数。
- `/tmp/requirements*.txt` 只在镜像构建阶段临时使用，不是运行时数据路径。
- DataMate 算子访问服务时默认使用 Docker 网络名 `http://data-synthesis-service:18080`；实际服务名或端口不同时，通过算子参数 `serviceUrl` 覆盖。

## 健康检查

```bash
curl http://<service-host>:18080/health
```

服务默认监听 `18080` 端口。DataMate 算子通过 `serviceUrl` 参数访问该服务；如果实际服务名或端口不同，修改平台参数即可。
