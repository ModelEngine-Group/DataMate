#!/bin/bash

set -e

/usr/local/bin/prune-postgres-logs.sh &

exec docker-entrypoint.sh "$@"
