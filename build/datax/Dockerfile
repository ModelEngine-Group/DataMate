FROM maven:3-openjdk-8-slim AS builder

RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/alibaba/DataX.git

COPY datax/ DataX/

RUN cd DataX && \
    mvn -U clean package assembly:assembly -Dmaven.test.skip=true


FROM openjdk:8-jdk-slim

RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-pip python-is-python3 vim wget curl nfs-common rsync && \
    apt-get clean && \
    rm -rf /var/lib/apy/lists/*

RUN pip config --user set global.index https://mirrors.huaweicloud.com/repository/pypi && \
    pip config --user set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config --user set global.trusted-host mirrors.huaweicloud.com && \
    pip install fastapi uvicorn && \
    pip cache purge

COPY --from=builder /DataX/target/datax/datax /opt/datax

COPY app.py /opt/datax/bin/app.py