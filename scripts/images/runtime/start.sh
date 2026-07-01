#!/bin/bash

set -e

cp -r /opt/runtime/user/* /opt/runtime/datamate/ops/user

if [ "${LOG_ROTATION_ENABLED:-true}" = "true" ]; then
  LOG_ROTATION_PATH="${LOG_ROTATION_PATH:-/tmp/ray}" /usr/local/bin/log-rotate-copytruncate.sh "${LOG_ROTATION_PATH:-/tmp/ray}" &
fi

echo "Starting main application..."
exec "$@"
