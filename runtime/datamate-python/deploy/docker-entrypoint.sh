#!/bin/bash
set -e

echo "=========================================="
echo "Label Studio Adapter Starting..."
echo "=========================================="

# Label Studio 本地存储基础路径（从环境变量获取，默认值）
LABEL_STUDIO_LOCAL_BASE="${LABEL_STUDIO_LOCAL_BASE:-/label-studio/local_files}"

echo "=========================================="
echo "Ensuring Label Studio local storage directories exist..."
echo "Base path: ${LABEL_STUDIO_LOCAL_BASE}"
echo "=========================================="

# 创建必要的目录
mkdir -p "${LABEL_STUDIO_LOCAL_BASE}/dataset"
mkdir -p "${LABEL_STUDIO_LOCAL_BASE}/upload"

echo "✓ Directory 'dataset' ready: ${LABEL_STUDIO_LOCAL_BASE}/dataset"
echo "✓ Directory 'upload' ready: ${LABEL_STUDIO_LOCAL_BASE}/upload"

echo "=========================================="
echo "Directory initialization completed"
echo "=========================================="

# 等待数据库就绪（如果配置了数据库）
if [ -n "$MYSQL_HOST" ] || [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for database to be ready..."
    sleep 5
fi

# 运行数据库迁移
echo "=========================================="
echo "Running database migrations..."
echo "=========================================="
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Database migrations completed successfully"
else
    echo "⚠️  WARNING: Database migrations failed"
    echo "    The application may not work correctly"
fi

echo "=========================================="

# 启动应用
echo "Starting Label Studio Adapter..."
echo "Host: ${HOST:-0.0.0.0}"
echo "Port: ${PORT:-18000}"
echo "Debug: ${DEBUG:-false}"
echo "Label Studio URL: ${LABEL_STUDIO_BASE_URL}"
echo "=========================================="

# 转换 LOG_LEVEL 为小写（uvicorn 要求小写）
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# 使用 uvicorn 启动应用
exec uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-18000}" \
    --log-level "${LOG_LEVEL_LOWER}" \
    ${DEBUG:+--reload}
