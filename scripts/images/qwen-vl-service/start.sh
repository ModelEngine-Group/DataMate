#!/usr/bin/env bash
set -euo pipefail

export QWEN_SERVER_HOST="${QWEN_SERVER_HOST:-0.0.0.0}"
export QWEN_SERVER_PORT="${QWEN_SERVER_PORT:-18080}"

exec python /workspace/datamate/qwen_vl_server.py
