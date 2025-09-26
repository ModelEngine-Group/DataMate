FROM downloads.unstructured.io/unstructured-io/unstructured

RUN pip config --user set global.index https://mirrors.huaweicloud.com/repository/pypi && \
    pip config --user set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config --user set global.trusted-host mirrors.huaweicloud.com && \
    pip install fastapi uvicorn && \
    pip cache purge

COPY scripts/images/unstructured/app.py /app/app.py
