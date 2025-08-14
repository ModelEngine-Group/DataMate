FROM openjdk:17-jre-slim

LABEL maintainer="Data Engine Platform Team <dev@dataengine.com>"
LABEL description="Data Management Service - 数据管理服务"

# 设置工作目录
WORKDIR /app

# 创建应用用户
RUN groupadd -r dataengine && useradd -r -g dataengine dataengine

# 创建必要的目录
RUN mkdir -p /app/uploads /app/logs && \
    chown -R dataengine:dataengine /app

# 复制应用JAR文件
COPY target/data-management-service-*-exec.jar app.jar

# 设置文件权限
RUN chown dataengine:dataengine app.jar

# 切换到应用用户
USER dataengine

# 暴露端口
EXPOSE 8092

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8092/actuator/health || exit 1

# 设置JVM参数
ENV JAVA_OPTS="-Xms512m -Xmx1024m -XX:+UseG1GC -XX:+UseContainerSupport"

# 启动应用
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
