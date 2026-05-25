#!/bin/bash
# DataMate Secrets Helper
# Manages SOPS-encrypted secrets for Helm deployment.
# Docker users do NOT need this script - use .env file instead.

set -e

SOPS_KEY_FILE="${SOPS_KEY_FILE:-$PWD/.sops-keys/key.txt}"
SOPS_CONFIG="${SOPS_CONFIG:-$PWD/.sops.yaml}"

# Check required tools
check_tools() {
    local missing=""
    command -v sops >/dev/null 2>&1 || missing="$missing sops"
    command -v age >/dev/null 2>&1 || missing="$missing age"
    command -v age-keygen >/dev/null 2>&1 || missing="$missing age-keygen"
    if [ -n "$missing" ]; then
        echo "Error: Required tools not found:$missing"
        echo "Install with: brew install sops age"
        exit 1
    fi
}

# Check or generate age key
ensure_key() {
    if [ ! -f "$SOPS_KEY_FILE" ]; then
        echo "Age key not found at $SOPS_KEY_FILE"
        echo "Generating a new one..."
        mkdir -p "$(dirname "$SOPS_KEY_FILE")"
        age-keygen -o "$SOPS_KEY_FILE"
        echo "Key generated. Keep this file secure and never commit it."
    fi
    export SOPS_AGE_KEY_FILE="$SOPS_KEY_FILE"
}

case "$1" in
    encrypt)
        check_tools
        if [ -z "$2" ]; then
            echo "Usage: $0 encrypt <file.yaml>"
            exit 1
        fi
        sops --encrypt --in-place "$2"
        echo "Encrypted: $2"
        ;;
    decrypt)
        check_tools
        if [ -z "$2" ]; then
            echo "Usage: $0 decrypt <file.yaml>"
            exit 1
        fi
        sops --decrypt --in-place "$2"
        echo "Decrypted: $2"
        ;;
    view)
        check_tools
        if [ -z "$2" ]; then
            echo "Usage: $0 view <file.yaml>"
            exit 1
        fi
        sops --decrypt "$2"
        ;;
    helm-upgrade)
        # Usage: scripts/secrets.sh helm-upgrade <chart> <namespace> [extra-helm-args...]
        check_tools
        ensure_key
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 helm-upgrade <chart> <namespace> [extra-helm-args...]"
            exit 1
        fi
        CHART="$2"
        NAMESPACE="$3"
        SECRETS_FILE="deployment/helm/$CHART/secrets.yaml"
        shift 3

        if [ ! -f "$SECRETS_FILE" ]; then
            echo "Warning: No secrets file at $SECRETS_FILE, deploying without secrets."
            helm upgrade --install "$CHART" "deployment/helm/$CHART" -n "$NAMESPACE" "$@"
        else
            TMP_FILE=$(mktemp)
            sops --decrypt "$SECRETS_FILE" > "$TMP_FILE"
            helm upgrade --install "$CHART" "deployment/helm/$CHART" -n "$NAMESPACE" -f "$TMP_FILE" "$@"
            rm "$TMP_FILE"
            echo "Deployed $CHART with decrypted secrets."
        fi
        ;;
    *)
        echo "DataMate Secrets Helper"
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  encrypt <file.yaml>          Encrypt a YAML file in-place"
        echo "  decrypt <file.yaml>          Decrypt a YAML file in-place"
        echo "  view <file.yaml>             Print decrypted content"
        echo "  helm-upgrade <chart> <ns>    Decrypt secrets and helm upgrade --install"
        echo ""
        echo "Docker users: skip this script, use 'cp .env.example .env' instead."
        exit 1
        ;;
esac