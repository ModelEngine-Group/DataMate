#!/bin/bash
set -e

if [-d $LOCAL_FILES_DOCUMENT_ROOT ] && $LOCAL_FILES_SERVING_ENABLED; then
  echo "Using local document root: $LOCAL_FILES_DOCUMENT_ROOT"
fi

# 启动应用
echo "=========================================="
echo "Starting Label Studio Adapter..."
echo "Host: ${HOST:-0.0.0.0}"
echo "Port: ${PORT:-18000}"
echo "Debug: ${DEBUG:-false}"

# 转换 LOG_LEVEL 为小写（uvicorn 要求小写）
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# 使用 uvicorn 启动应用
exec uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-18000}" \
    --log-level "${LOG_LEVEL_LOWER}" \
    ${DEBUG:+--reload}
