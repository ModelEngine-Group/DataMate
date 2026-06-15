FROM ubuntu:22.04-arm64

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY} \
    NO_PROXY=${NO_PROXY} \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/workspace/datamate \
    QWEN_SERVER_HOST=0.0.0.0 \
    QWEN_SERVER_PORT=18080 \
    QWEN_MODEL_DIR=/models/VideoOps/qwen/Qwen2.5-VL-7B-Instruct

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.10 /usr/bin/python \
    && python -m pip install --upgrade pip setuptools wheel

RUN python -m pip install \
    torch==2.9.0 \
    torchvision==0.24.0 \
    torch-npu==2.9.0 \
    transformers==5.2.0 \
    qwen-vl-utils==0.0.14 \
    Flask==3.1.3 \
    Pillow==12.1.1 \
    accelerate==1.12.0 \
    safetensors==0.7.0 \
    tokenizers==0.22.2 \
    requests

COPY qwen_vl_server.py ${APP_HOME}/qwen_vl_server.py
COPY start.sh /usr/local/bin/start.sh

RUN chmod +x /usr/local/bin/start.sh

EXPOSE 18080

CMD ["/usr/local/bin/start.sh"]
