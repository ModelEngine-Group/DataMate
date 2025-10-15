FROM maven:3-amazoncorretto-21-debian AS builder

COPY backend/ /opt/backend
COPY scripts/images/backend/settings.xml /opt/backend

RUN cd /opt/backend && \
    mvn -U clean package -s settings.xml -Dmaven.test.skip=true


FROM openjdk:21-jdk-slim

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y vim wget curl nfs-common rsync && \
    apt-get clean && \
    rm -rf /var/lib/apy/lists/*

COPY --from=builder /opt/backend/services/main-application/target/data-engine.jar /opt/backend/data-engine.jar
COPY editions/community/config/application.yml /opt/backend/application.yml
COPY editions/community/config/log4j2.xml /opt/backend/log4j2.xml

CMD ["java", "-jar", "/opt/backend/data-engine.jar"]
