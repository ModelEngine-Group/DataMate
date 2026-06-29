#!/bin/bash

set -euo pipefail

LOG_DIR="${NGINX_LOG_DIR:-/var/log/datamate/frontend}"
LOG_ROTATION_MAX_SIZE="${LOG_ROTATION_MAX_SIZE:-100MB}"
LOG_ROTATION_BACKUP_COUNT="${LOG_ROTATION_BACKUP_COUNT:-30}"
LOG_ROTATION_INTERVAL_SECONDS="${LOG_ROTATION_INTERVAL_SECONDS:-300}"

parse_size_bytes() {
    local value
    value="$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')"
    value="${value// /}"
    case "$value" in
        *GB) echo $((${value%GB} * 1024 * 1024 * 1024)) ;;
        *G) echo $((${value%G} * 1024 * 1024 * 1024)) ;;
        *MB) echo $((${value%MB} * 1024 * 1024)) ;;
        *M) echo $((${value%M} * 1024 * 1024)) ;;
        *KB) echo $((${value%KB} * 1024)) ;;
        *K) echo $((${value%K} * 1024)) ;;
        *B) echo "${value%B}" ;;
        *) echo "$value" ;;
    esac
}

file_size_bytes() {
    wc -c < "$1" | tr -d ' '
}

backup_path() {
    local file="$1"
    local index="$2"
    local ext="${file##*.}"
    local stem="${file%.$ext}"
    echo "${stem}.${index}.${ext}"
}

rotate_file() {
    local file="$1"
    local max_bytes="$2"
    local backup_count="$3"

    [ -f "$file" ] || return 1

    local current_size
    current_size="$(file_size_bytes "$file")"
    [ "$current_size" -lt "$max_bytes" ] && return 1

    rm -f "$(backup_path "$file" "$backup_count")"

    local index
    for ((index = backup_count - 1; index >= 1; index--)); do
        local src dst
        src="$(backup_path "$file" "$index")"
        dst="$(backup_path "$file" "$((index + 1))")"
        [ -f "$src" ] && mv "$src" "$dst"
    done

    mv "$file" "$(backup_path "$file" 1)"
    install -o nginx -g nginx -m 0644 /dev/null "$file"
    return 0
}

rotate_once() {
    mkdir -p "$LOG_DIR"
    touch "$LOG_DIR/access.log" "$LOG_DIR/error.log"
    chown -R nginx:nginx "$LOG_DIR" 2>/dev/null || true

    local max_bytes
    max_bytes="$(parse_size_bytes "$LOG_ROTATION_MAX_SIZE")"

    local rotated=false
    for file in "$LOG_DIR/access.log" "$LOG_DIR/error.log"; do
        if rotate_file "$file" "$max_bytes" "$LOG_ROTATION_BACKUP_COUNT"; then
            rotated=true
        fi
    done

    if [ "$rotated" = true ]; then
        nginx -s reopen || true
    fi
}

if [ "${1:-}" = "--once" ]; then
    rotate_once
    exit 0
fi

while true; do
    rotate_once
    sleep "$LOG_ROTATION_INTERVAL_SECONDS"
done
