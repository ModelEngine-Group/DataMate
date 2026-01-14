FROM maven:3-eclipse-temurin-21 AS builder
COPY backend/ /opt/backend

RUN cd /opt/backend/ && \
    mvn -U clean package -Dmaven.test.skip=true


FROM eclipse-temurin:21-jdk

RUN apt-get update && \
    apt-get install -y vim wget curl rsync python3 python3-pip python-is-python3 dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/backend/services/main-application/target/datamate.jar /opt/backend/datamate.jar

COPY scripts/images/backend/start.sh /opt/backend/start.sh

COPY runtime/ops/examples/test_operator/test_operator.tar /opt/backend/test_operator.tar

RUN dos2unix /opt/backend/start.sh \
    && chmod +x /opt/backend/start.sh \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

EXPOSE 8080

ENTRYPOINT ["/opt/backend/start.sh"]

CMD ["java", "-Duser.timezone=Asia/Shanghai", "-jar", "/opt/backend/datamate.jar"]
