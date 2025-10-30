FROM python:3.11

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops
COPY runtime/ops/user /opt/runtime/user
COPY scripts/images/runtime/start.sh /opt/runtime/start.sh

ENV PYTHONPATH=/opt/runtime/datamate/

RUN apt update \
    && apt install -y libgl1 libglib2.0-0 vim libmagic1t64  libreoffice\
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/runtime

RUN pip install -e . --trusted-host mirrors.huaweicloud.com -i https://mirrors.huaweicloud.com/repository/pypi/simple \
    && pip install -r /opt/runtime/datamate/ops/requirements.txt --trusted-host mirrors.huaweicloud.com -i https://mirrors.huaweicloud.com/repository/pypi/simple \
    && pip cache purge

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && chmod +x /opt/runtime/start.sh

EXPOSE 8081

ENTRYPOINT ["/opt/runtime/start.sh"]
