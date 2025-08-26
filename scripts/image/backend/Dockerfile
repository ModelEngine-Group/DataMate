FROM maven:3-openjdk-21-slim AS builder

COPY backend/ /opt/backend
COPY scripts/image/backend/settings.xml /opt/backend

RUN cd /opt/backend && \
    mvn -U clean package -s settings.xml


FROM openjdk:21-jdk-slim

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y vim wget curl nfs-common rsync && \
    apt-get clean && \
    rm -rf /var/lib/apy/lists/*

COPY --from=builder /opt/backend/interfaces/target/interfaces-1.0.0.jar /opt/backend/interfaces-1.0.0.jar

CMD ["java", "-jar", "/opt/backend/interfaces-1.0.0.jar"]
