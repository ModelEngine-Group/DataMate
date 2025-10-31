FROM python:3.11-slim

COPY runtime/mineru /opt/runtime/datamate/mineru

RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y curl vim libgl1 libglx0 libopengl0 libglib2.0-0 procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip config --user set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config --user set global.trusted-host mirrors.huaweicloud.com && \
    pip install --upgrade setuptools && \
    pip install -U 'mineru[core]==2.5.4' --break-system-packages && \
    pip cache purge

ENV CURL_CA_BUNDLE=""
ENV TORCH_DEVICE_BACKEND_AUTOLOAD=0

RUN /bin/bash -c "mineru-models-download -s modelscope -m all"

ENV MINERU_MODEL_SOURCE=local
