ARG BASE_IMAGE=quay.io/ascend/vllm-ascend:v0.18.0rc1
FROM ${BASE_IMAGE}

WORKDIR /app

COPY data_synthesis_service/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --no-deps -r /tmp/requirements.txt

COPY data_synthesis /app/data_synthesis
COPY data_synthesis_service /app/data_synthesis_service

ENV PYTHONPATH=/app
EXPOSE 18103

CMD ["bash", "-lc", "set -e; unset ASCEND_LAUNCH_BLOCKING; export HCCL_OP_EXPANSION_MODE=AIV; source /usr/local/Ascend/ascend-toolkit/set_env.sh; exec python -m uvicorn data_synthesis_service.app:app --host 0.0.0.0 --port ${DATA_SYNTHESIS_SERVICE_PORT:-18103}"]
