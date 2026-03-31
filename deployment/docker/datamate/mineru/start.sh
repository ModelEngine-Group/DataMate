#!/bin/bash
set -e

NUM_INSTANCES=${NUM_INSTANCES:-3}
BASE_PORT=${BASE_PORT:-8000}

echo "[$(date)] Starting ${NUM_INSTANCES} MinerU Pipeline instances on ports ${BASE_PORT}-$((BASE_PORT + NUM_INSTANCES - 1))"

PIDS=()
for i in $(seq 0 $((NUM_INSTANCES - 1))); do
  PORT=$((BASE_PORT + i))
  echo "[$(date)] Starting instance ${i} on port ${PORT}"
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
