FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY runtime/label-studio-adapter/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY runtime/label-studio-adapter .

# 复制并设置 entrypoint 脚本权限
COPY runtime/label-studio-adapter/deploy/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 8088

# 使用 entrypoint 脚本启动
ENTRYPOINT ["/docker-entrypoint.sh"]