FROM openjdk:8-jre-slim

RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-pip python-is-python3 vim wget curl && \
    apt-get clean && \
    rm -rf /var/lib/apy/lists/*

RUN wget https://datax-opensource.oss-cn-hangzhou.aliyuncs.com/202309/datax.tar.gz && \
    tar -zxvf datax.tar.gz -C /opt && \
    rm -rf datax.tar.gz