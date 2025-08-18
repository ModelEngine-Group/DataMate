FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl vim libgl1 libgl1-mesa-glx libglib2.0-0 procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip config --user set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    pip config --user set global.trusted-host mirrors.aliyun.com && \
    pip install --upgrade setuptools && \
    pip install -U 'mineru[core]==2.1.0' --break-system-packages && \
    pip install torch==2.7.1+cpu -f https://download.pytorch.org/whl/torch/ && \
    pip install torchvision==0.22.1+cpu -f https://download.pytorch.org/whl/torchvision && \
    pip install requests==2.27.1 torch_npu==2.7.1rc1 numpy==1.26.0 decorator==5.2.1 einops==0.8.1 attrs==25.3.0 && \
    pip cache purge

ENV CURL_CA_BUNDLE=""
ENV TORCH_DEVICE_BACKEND_AUTOLOAD=0

RUN /bin/bash -c "mineru-models-download -s modelscope -m all"

ENV MINERU_MODEL_SOURCE=local
