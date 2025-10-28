FROM python:3.11

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops

ENV PYTHONPATH=/opt/runtime/datamate/

RUN apt update \
    && apt install -y libgl1 libglib2.0-0 vim poppler-utils tesseract-ocr tesseract-ocr-chi-sim libmagic1t64  libreoffice\
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/runtime

ENV HF_HUB_DISABLE_XET=1

RUN pip install -e . \
    && pip install -r /opt/runtime/datamate/ops/requirements.txt \
    && pip cache purge

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

EXPOSE 8081
