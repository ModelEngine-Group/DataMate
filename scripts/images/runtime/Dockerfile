FROM ghcr.io/astral-sh/uv:python3.11-bookworm

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update \
    && apt install -y libgl1 libglib2.0-0 vim libmagic1 libreoffice dos2unix swig poppler-utils tesseract-ocr

RUN mkdir -p /home/models \
    && wget https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar \
    && tar -xf ch_ppocr_mobile_v2.0_cls_infer.tar -C /home/models \
    && rm -f ch_*.tar

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops
COPY runtime/ops/user /opt/runtime/user
COPY scripts/images/runtime/start.sh /opt/runtime/start.sh

ENV PYTHONPATH=/opt/runtime/datamate/
ENV UV_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ENV UV_INDEX_STRATEGY=unsafe-best-match

WORKDIR /opt/runtime

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e .[all] --system \
    && uv pip install -r /opt/runtime/datamate/ops/pyproject.toml --system \
    && uv pip uninstall torch torchvision --system \
    && python -m spacy download zh_core_web_sm \
    && echo "/usr/local/lib/ops/site-packages" > /usr/local/lib/python3.11/site-packages/ops.pth

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && chmod +x /opt/runtime/start.sh \
    && dos2unix /opt/runtime/start.sh

EXPOSE 8081

ENTRYPOINT ["/opt/runtime/start.sh"]
