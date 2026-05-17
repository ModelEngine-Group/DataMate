FROM quay.io/ascend/vllm-ascend:v0.18.0rc1

WORKDIR /workspace

ENV PYTHONPATH=/workspace \
    DATA_SYNTHESIS_BACKEND=vllm \
    DATA_EVALUATOR_BACKEND=vllm \
    DATA_SYNTHESIS_MODEL_PATH=/model/Qwen/Qwen3-1___7b-Medical-R1-sft \
    DATA_SYNTHESIS_RUN_MODE=inprocess \
    HCCL_OP_EXPANSION_MODE=AIV

COPY service_patch/data_synthesis ./data_synthesis
COPY service_patch/data_synthesis_service ./data_synthesis_service
COPY service_patch/data_synthesis_service/requirements-base.txt /tmp/requirements-base.txt
COPY service_patch/data_synthesis_service/requirements.txt /tmp/requirements.txt
COPY service_patch/data_synthesis_service/requirements-npu.txt /tmp/requirements-npu.txt

RUN python -m pip install --no-cache-dir --no-deps -r /tmp/requirements.txt

EXPOSE 18080

CMD ["bash", "-lc", "set -e; unset ASCEND_LAUNCH_BLOCKING; export HCCL_OP_EXPANSION_MODE=AIV; source /usr/local/Ascend/ascend-toolkit/set_env.sh; exec python -m uvicorn data_synthesis_service.app:app --host 0.0.0.0 --port 18080"]
