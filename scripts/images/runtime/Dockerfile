FROM ghcr.io/astral-sh/uv:python3.11-bookworm

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops
COPY runtime/ops/user /opt/runtime/user
COPY scripts/images/runtime/start.sh /opt/runtime/start.sh

ENV PYTHONPATH=/opt/runtime/datamate/

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update \
    && apt install -y libgl1 libglib2.0-0 vim libmagic1 libreoffice dos2unix

WORKDIR /opt/runtime

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e . --system \
    && uv pip install -r /opt/runtime/datamate/ops/requirements.txt --system

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && chmod +x /opt/runtime/start.sh \
    && dos2unix /opt/runtime/start.sh

EXPOSE 8081

ENTRYPOINT ["/opt/runtime/start.sh"]
