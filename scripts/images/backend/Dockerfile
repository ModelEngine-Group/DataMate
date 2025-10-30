FROM maven:3-openjdk-8-slim AS datax-builder

RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/alibaba/DataX.git

COPY runtime/datax/ DataX/

RUN cd DataX && \
    sed -i "s/com.mysql.jdbc.Driver/com.mysql.cj.jdbc.Driver/g" \
    plugin-rdbms-util/src/main/java/com/alibaba/datax/plugin/rdbms/util/DataBaseType.java && \
    mvn -U clean package assembly:assembly -Dmaven.test.skip=true

FROM maven:3-amazoncorretto-21-debian AS builder

COPY backend/ /opt/backend

RUN cd /opt/backend && \
    mvn -U clean package -Dmaven.test.skip=true


FROM openjdk:21-jdk-slim

RUN apt-get update && \
    apt-get install -y vim wget curl nfs-common rsync python3 python3-pip python-is-python3 dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/backend/services/main-application/target/data-mate.jar /opt/backend/data-mate.jar
COPY --from=datax-builder /DataX/target/datax/datax /opt/datax

COPY editions/community/config/application.yml /opt/backend/application.yml
COPY editions/community/config/log4j2.xml /opt/backend/log4j2.xml
COPY scripts/images/backend/start.sh /opt/backend/start.sh

RUN dos2unix /opt/backend/start.sh \
    && chmod +x /opt/backend/start.sh \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

EXPOSE 8080

ENTRYPOINT ["/opt/backend/start.sh"]

CMD ["java", "-Duser.timezone=Asia/Shanghai", "-jar", "/opt/backend/data-mate.jar"]
