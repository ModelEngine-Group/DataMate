#!/bin/bash
set -e

NUM_INSTANCES=${NUM_INSTANCES:-3}
BASE_PORT=${BASE_PORT:-8000}
DEVICE_IDS=${DEVICE_IDS:-0}

IFS=',' read -ra DEVICES <<< "$DEVICE_IDS"

echo "[$(date)] Starting ${NUM_INSTANCES} MinerU Pipeline instances, devices: [${DEVICE_IDS}]"

PIDS=()
for i in $(seq 0 $((NUM_INSTANCES - 1))); do
  PORT=$((BASE_PORT + i))
  DEVICE=${DEVICES[$((i % ${#DEVICES[@]}))]}
  echo "[$(date)] Starting instance ${i} on port ${PORT}, device ${DEVICE}"
  ASCEND_RT_VISIBLE_DEVICES=${DEVICE} \
    mineru-api \
      --host 0.0.0.0 \
      --port "${PORT}" &
  PIDS+=($!)
done

echo "[$(date)] All instances started. PIDs: ${PIDS[*]}"

wait -n "${PIDS[@]}"
EXIT_CODE=$?
echo "[$(date)] A process exited with code ${EXIT_CODE}, shutting down all instances"
kill "${PIDS[@]}" 2>/dev/null || true
exit ${EXIT_CODE}
