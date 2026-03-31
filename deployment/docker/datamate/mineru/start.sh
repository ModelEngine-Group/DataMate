#!/bin/bash
set -e

INSTANCES_PER_DEVICE=${INSTANCES_PER_DEVICE:-3}
BASE_PORT=${BASE_PORT:-8000}
DEVICE_IDS=${DEVICE_IDS:-0}

IFS=',' read -ra DEVICES <<< "$DEVICE_IDS"
NUM_DEVICES=${#DEVICES[@]}
TOTAL_INSTANCES=$((NUM_DEVICES * INSTANCES_PER_DEVICE))

echo "[$(date)] Starting ${NUM_DEVICES} devices × ${INSTANCES_PER_DEVICE} instances = ${TOTAL_INSTANCES} total"

PIDS=()
for d in $(seq 0 $((NUM_DEVICES - 1))); do
  DEVICE=${DEVICES[$d]}
  for p in $(seq 0 $((INSTANCES_PER_DEVICE - 1))); do
    IDX=$((d * INSTANCES_PER_DEVICE + p))
    PORT=$((BASE_PORT + IDX))
    echo "[$(date)] Starting instance ${IDX} on port ${PORT}, device ${DEVICE}"
    ASCEND_RT_VISIBLE_DEVICES=${DEVICE} \
      mineru-api \
        --host 0.0.0.0 \
        --port "${PORT}" &
    PIDS+=($!)
  done
done

echo "[$(date)] All ${TOTAL_INSTANCES} instances started. PIDs: ${PIDS[*]}"

wait -n "${PIDS[@]}"
EXIT_CODE=$?
echo "[$(date)] A process exited with code ${EXIT_CODE}, shutting down all instances"
kill "${PIDS[@]}" 2>/dev/null || true
exit ${EXIT_CODE}
