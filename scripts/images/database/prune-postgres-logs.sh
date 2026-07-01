#!/bin/bash

set -euo pipefail

LOG_DIR="${POSTGRES_LOG_DIR:-/var/log/datamate/database}"
LOG_ROTATION_BACKUP_COUNT="${LOG_ROTATION_BACKUP_COUNT:-30}"
LOG_ROTATION_INTERVAL_SECONDS="${LOG_ROTATION_INTERVAL_SECONDS:-300}"

prune_once() {
    [ -d "$LOG_DIR" ] || return 0

    mapfile -t files < <(
        find "$LOG_DIR" -maxdepth 1 -type f -name 'postgresql-*.log' -printf '%T@ %p\n' 2>/dev/null \
            | sort -rn \
            | sed 's/^[^ ]* //'
    )

    local index
    for ((index = LOG_ROTATION_BACKUP_COUNT; index < ${#files[@]}; index++)); do
        rm -f "${files[$index]}"
    done
}

if [ "${1:-}" = "--once" ]; then
    prune_once
    exit 0
fi

while true; do
    prune_once
    sleep "$LOG_ROTATION_INTERVAL_SECONDS"
done
