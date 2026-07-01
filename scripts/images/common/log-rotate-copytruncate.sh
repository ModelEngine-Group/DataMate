#!/bin/bash

set -euo pipefail

run_once=false
if [ "${1:-}" = "--once" ]; then
    run_once=true
    shift
fi

LOG_ROOT="${1:-${LOG_ROTATION_PATH:-/tmp/ray}}"
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

is_backup_file() {
    local name
    name="$(basename "$1")"
    [[ "$name" =~ \.[0-9]+\.(log|out|err)$ ]]
}

rotate_file() {
    local file="$1"
    local max_bytes="$2"
    local backup_count="$3"

    [ -f "$file" ] || return 0
    is_backup_file "$file" && return 0

    local current_size
    current_size="$(file_size_bytes "$file")"
    [ "$current_size" -lt "$max_bytes" ] && return 0

    rm -f "$(backup_path "$file" "$backup_count")"

    local index
    for ((index = backup_count - 1; index >= 1; index--)); do
        local src dst
        src="$(backup_path "$file" "$index")"
        dst="$(backup_path "$file" "$((index + 1))")"
        [ -f "$src" ] && mv "$src" "$dst"
    done

    cp -p "$file" "$(backup_path "$file" 1)"
    : > "$file"
}

rotate_once() {
    [ -d "$LOG_ROOT" ] || return 0

    local max_bytes
    max_bytes="$(parse_size_bytes "$LOG_ROTATION_MAX_SIZE")"

    while IFS= read -r -d '' file; do
        rotate_file "$file" "$max_bytes" "$LOG_ROTATION_BACKUP_COUNT"
    done < <(
        find "$LOG_ROOT" -type f \( -name '*.log' -o -name '*.out' -o -name '*.err' \) -print0 2>/dev/null || true
    )
}

if [ "$run_once" = true ]; then
    rotate_once
    exit 0
fi

while true; do
    rotate_once
    sleep "$LOG_ROTATION_INTERVAL_SECONDS"
done
