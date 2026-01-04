#!/bin/bash

set -e

umask 0022

echo "Starting main application..."
exec "$@"
