#!/bin/bash

set -e

mkdir -p /opt/runtime/datamate/ops/user
find /opt/runtime/user -mindepth 1 -maxdepth 1 -type d -print0 | while IFS= read -r -d '' op_dir; do
  rm -rf "/opt/runtime/datamate/ops/user/$(basename "${op_dir}")"
  cp -r "${op_dir}" /opt/runtime/datamate/ops/user/
done
find /opt/runtime/user -mindepth 1 -maxdepth 1 -type f -print0 | while IFS= read -r -d '' op_file; do
  cp -f "${op_file}" /opt/runtime/datamate/ops/user/
done

echo "Starting main application..."
exec "$@"
