FROM maven:3-openjdk-8-slim AS builder

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/alibaba/DataX.git

COPY runtime/datax/ DataX/

RUN cd DataX && \
    sed -i "s/com.mysql.jdbc.Driver/com.mysql.cj.jdbc.Driver/g" \
    plugin-rdbms-util/src/main/java/com/alibaba/datax/plugin/rdbms/util/DataBaseType.java && \
    mvn -U clean package assembly:assembly -Dmaven.test.skip=true


FROM openjdk:8-jdk-slim

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-pip python-is-python3 vim wget curl nfs-common rsync && \
    apt-get clean && \
    rm -rf /var/lib/apy/lists/*

RUN pip config --user set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    pip config --user set global.trusted-host mirrors.aliyun.com && \
    pip install fastapi uvicorn[standard] && \
    pip cache purge

COPY --from=builder /DataX/target/datax/datax /opt/datax

COPY scripts/images/datax/app.py /opt/datax/bin/app.py
