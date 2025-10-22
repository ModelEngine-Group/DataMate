FROM python:3.11

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops

ENV PYTHONPATH=/opt/runtime/datamate/

RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt update \
    && apt install -y libgl1 libglib2.0-0 vim poppler-utils tesseract-ocr tesseract-ocr-chi-sim libmagic1t64 \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/runtime

ENV HF_HUB_DISABLE_XET=1

RUN pip install -e . -i https://mirrors.huaweicloud.com/repository/pypi/simple \
    && pip install -r /opt/runtime/datamate/ops/requirements.txt -i https://mirrors.huaweicloud.com/repository/pypi/simple \
    && pip cache purge

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
