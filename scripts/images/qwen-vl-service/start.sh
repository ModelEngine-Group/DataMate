#!/usr/bin/env bash
set -euo pipefail

export QWEN_SERVER_HOST="${QWEN_SERVER_HOST:-0.0.0.0}"
export QWEN_SERVER_PORT="${QWEN_SERVER_PORT:-18080}"
export QWEN_MODEL_DIR="${QWEN_MODEL_DIR:-/models/VideoOps/qwen/Qwen2.5-VL-7B-Instruct}"

exec python /workspace/datamate/qwen_vl_server.py
