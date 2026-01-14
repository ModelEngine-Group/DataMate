FROM maven:3-eclipse-temurin-21 AS builder

COPY backend/ /opt/gateway

RUN cd /opt/gateway/ && \
    mvn -U clean package -Dmaven.test.skip=true


FROM eclipse-temurin:21-jdk

RUN apt-get update && \
    apt-get install -y vim wget curl dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/gateway/api-gateway/target/gateway.jar /opt/gateway/gateway.jar

COPY scripts/images/gateway/start.sh /opt/gateway/start.sh

RUN dos2unix /opt/gateway/start.sh \
    && chmod +x /opt/gateway/start.sh \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

EXPOSE 8080

ENTRYPOINT ["/opt/gateway/start.sh"]

CMD ["java", "-Duser.timezone=Asia/Shanghai", "-jar", "/opt/gateway/gateway.jar"]
