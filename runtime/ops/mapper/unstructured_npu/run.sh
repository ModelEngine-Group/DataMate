#!/bin/bash

set -euo pipefail

# =========================================================
# Ascend NPU 极简启动脚本 (Fix std::bad_alloc)
# =========================================================

# 1. 定义库路径
JEMALLOC="/usr/lib/aarch64-linux-gnu/libjemalloc.so.2"
GOMP="/usr/lib/aarch64-linux-gnu/libgomp.so.1"

# 0. 切换到脚本目录，避免从其他目录启动时找不到文件
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 2. 检查库是否存在
if [ ! -f "$JEMALLOC" ]; then
    echo "❌ Error: jemalloc not found at $JEMALLOC"
    exit 1
fi

# 3. 设置 LD_PRELOAD (覆盖式设置，防止重复)
# 注意：jemalloc 必须排在第一位，libgomp 排第二解决 TLS 问题
export LD_PRELOAD="$JEMALLOC:$GOMP"

# 4. Jemalloc 优化参数 (关键：关闭后台线程，防止 NPU 驱动冲突)
export MALLOC_CONF="background_thread:false,dirty_decay_ms:0,muzzy_decay_ms:0"

# 5. NPU 环境变量
export FLAGS_use_system_allocator=1
export expandable_segments=True
export OMP_NUM_THREADS=1

# 6. Python 路径 (包含当前目录和 YOLOX)
export PYTHONPATH=$(pwd):$(pwd)/YOLOX-main:$PYTHONPATH

# 6.1 可选加载 Ascend 环境（若存在）
if [ -f /usr/local/Ascend/ascend-toolkit/set_env.sh ]; then
    # shellcheck disable=SC1091
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
elif [ -f /usr/local/Ascend/ascend-toolkit/latest/set_env.sh ]; then
    # shellcheck disable=SC1091
    source /usr/local/Ascend/ascend-toolkit/latest/set_env.sh
fi

# 6.2 参数帮助
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    echo "用法: bash run.sh [文件1] [文件2] ..."
    echo "示例: bash run.sh demo.pdf word测试.docx"
    echo "未传参时默认处理: attention.pdf"
    exit 0
fi

# 7. 运行
echo "🚀 Running Benchmark..."
echo "Using LD_PRELOAD=$LD_PRELOAD"

if ! command -v python >/dev/null 2>&1; then
    echo "❌ Error: python 命令不存在"
    exit 1
fi

if [ "$#" -eq 0 ]; then
    set -- "attention.pdf"
fi

fail_count=0
for input_file in "$@"; do
    if [ ! -f "$input_file" ]; then
        echo "❌ 文件不存在: $input_file"
        fail_count=$((fail_count + 1))
        continue
    fi

    echo "📄 Processing: $input_file"
    if ! python benchmark_npu.py "$input_file"; then
        echo "❌ 处理失败: $input_file"
        fail_count=$((fail_count + 1))
    fi
done

if [ "$fail_count" -gt 0 ]; then
    echo "⚠️ 完成，但有 $fail_count 个文件失败"
    exit 1
fi

echo "✅ 全部处理完成"