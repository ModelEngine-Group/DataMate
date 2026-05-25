#!/bin/bash

SOPS_KEY_FILE="${SOPS_KEY_FILE:-$PWD/.sops-keys/key.txt}"
SOPS_CONFIG="${SOPS_CONFIG:-$PWD/.sops.yaml}"

if [ ! -f "$SOPS_KEY_FILE" ]; then
    echo "Error: SOPS age key file not found at $SOPS_KEY_FILE"
    echo "Please generate a key first: age-keygen -o .sops-keys/key.txt"
    exit 1
fi

export SOPS_AGE_KEY_FILE="$SOPS_KEY_FILE"

case "$1" in
    encrypt)
        if [ -z "$2" ]; then
            echo "Usage: $0 encrypt <file.yaml>"
            exit 1
        fi
        sops --encrypt --in-place "$2"
        echo "Encrypted: $2"
        ;;
    decrypt)
        if [ -z "$2" ]; then
            echo "Usage: $0 decrypt <file.yaml>"
            exit 1
        fi
        sops --decrypt --in-place "$2"
        echo "Decrypted: $2"
        ;;
    view)
        if [ -z "$2" ]; then
            echo "Usage: $0 view <file.yaml>"
            exit 1
        fi
        sops --decrypt "$2"
        ;;
    helm-install)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 helm-install <chart> <namespace> [--secrets-file <file>]"
            exit 1
        fi
        CHART="$2"
        NAMESPACE="$3"
        SECRETS_FILE="${4:-deployment/helm/$CHART/secrets.yaml}"
        
        TMP_FILE=$(mktemp)
        sops --decrypt "$SECRETS_FILE" > "$TMP_FILE"
        helm install "$CHART" "deployment/helm/$CHART" -n "$NAMESPACE" -f "$TMP_FILE"
        rm "$TMP_FILE"
        echo "Deployed $CHART to $NAMESPACE"
        ;;
    helm-upgrade)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 helm-upgrade <chart> <namespace> [--secrets-file <file>]"
            exit 1
        fi
        CHART="$2"
        NAMESPACE="$3"
        SECRETS_FILE="${4:-deployment/helm/$CHART/secrets.yaml}"
        
        TMP_FILE=$(mktemp)
        sops --decrypt "$SECRETS_FILE" > "$TMP_FILE"
        helm upgrade "$CHART" "deployment/helm/$CHART" -n "$NAMESPACE" -f "$TMP_FILE"
        rm "$TMP_FILE"
        echo "Upgraded $CHART in $NAMESPACE"
        ;;
    *)
        echo "DataMate SOPS Secret Management"
        echo ""
        echo "Usage:"
        echo "  $0 encrypt <file.yaml>       - Encrypt a secrets file"
        echo "  $0 decrypt <file.yaml>       - Decrypt a secrets file"
        echo "  $0 view <file.yaml>          - View decrypted secrets (no modification)"
        echo "  $0 helm-install <chart> <ns> - Install chart with decrypted secrets"
        echo "  $0 helm-upgrade <chart> <ns> - Upgrade chart with decrypted secrets"
        echo ""
        echo "Environment variables:"
        echo "  SOPS_KEY_FILE  - Path to age key file (default: .sops-keys/key.txt)"
        echo "  SOPS_CONFIG    - Path to .sops.yaml (default: .sops.yaml)"
        ;;
esac