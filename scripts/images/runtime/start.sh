#!/bin/bash

set -e

cp -r /opt/runtime/user/* /opt/runtime/datamate/ops/user

echo "Starting main application..."
exec "$@"
