# QwenVL service image for DataMate video operators
#
# Build example:
#   docker build -f scripts/images/qwen-vl-service/Dockerfile -t datamate-qwen-vl-service .
#
# Notes:
# 1. This image is used for the standalone QwenVL HTTP service.
# 2. Replace the base image according to the actual runtime environment.
# 3. If the service runs on Ascend / NPU, the base image must provide the
#    corresponding device runtime.

ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/workspace/datamate \
    QWEN_SERVER_PORT=18080 \
    QWEN_MODEL_DIR=/mnt/models/qwen/Qwen2.5-VL-7B-Instruct

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

# Copy service script
COPY scripts/images/qwen-vl-service/qwen_vl_server.py ${APP_HOME}/qwen_vl_server.py
COPY scripts/images/qwen-vl-service/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Install dependencies inside image.
# If the actual deployment environment uses a dedicated runtime image
# that already contains the required packages, this section can be adjusted.
RUN pip install \
    Flask \
    requests \
    Pillow \
    transformers \
    qwen-vl-utils \
    safetensors \
    tokenizers \
    accelerate \
    torch

EXPOSE 18080

CMD ["/usr/local/bin/start.sh"]
