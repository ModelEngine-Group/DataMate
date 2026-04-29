# QwenVL service image for DataMate video operators
#
# This Dockerfile provides the image build entry for the standalone QwenVL service.
#
# Notes:
# 1. The actual deployment environment uses Ascend / NPU with torch_npu and CANN.
# 2. Replace BASE_IMAGE with the actual Ascend-compatible runtime image in your environment.
# 3. Model weights are mounted from host storage and are not copied into the image.
# 4. The model path is configured by QWEN_MODEL_DIR and should be adjusted at deployment time.
# 5. The default BASE_IMAGE is only a generic placeholder for repository delivery.

ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/workspace/datamate \
    QWEN_SERVER_HOST=0.0.0.0 \
    QWEN_SERVER_PORT=18080 \
    QWEN_MODEL_DIR=/mnt/models/qwen/Qwen/Qwen2.5-VL-7B-Instruct

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

# Python packages aligned to the observed service environment.
RUN pip install \
    Flask==3.1.3 \
    requests==2.32.5 \
    Pillow==12.1.0 \
    transformers==5.2.0 \
    safetensors==0.7.0 \
    tokenizers==0.22.2 \
    accelerate==1.12.0 \
    torch==2.9.0

COPY scripts/images/qwen-vl-service/qwen_vl_server.py ${APP_HOME}/qwen_vl_server.py
COPY scripts/images/qwen-vl-service/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 18080

CMD ["/usr/local/bin/start.sh"]
