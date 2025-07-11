FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl vim libgl1 libgl1-mesa-glx libglib2.0-0 procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip config --user set global.index https://mirrors.huaweicloud.com/repository/pypi && \
    pip config --user set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config --user set global.trusted-host mirrors.huaweicloud.com && \
    pip install --upgrade setuptools && \
    pip install -U 'mineru[core]==2.1.0' --break-system-packages && \
    pip install requests==2.27.1 torch_npu==2.7.1rc1 numpy==1.26.0 decorator==5.2.1 einops==0.8.1 attrs==25.3.0

ENV CURL_CA_BUNDLE=""
ENV TORCH_DEVICE_BACKEND_AUTOLOAD=0

RUN /bin/bash -c "mineru-models-download -s huggingface -m all"

ENV MINERU_MODEL_SOURCE=local
