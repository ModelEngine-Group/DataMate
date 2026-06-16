#!/bin/bash
### Collect secrets for DataMate installation.
###
### Usage:
###   scripts/k8s/collect-secrets.sh [--component datamate|milvus] [--namespace <ns>]
###
### Modes (auto-detected):
###   1. Sealed-secrets mode:  controller running + kubeseal available → encrypt → apply SealedSecret
###   2. Plain mode:           no controller → Helm creates Secret with base64 (dev mode)
###
### Password priority:  .env file values > interactive prompt > auto-generated
###
### Output: writes shell script variables to stdout (eval by caller)

# NOTE: NOT using 'set -e' because interactive prompts (read) can fail
# when stdin is not a TTY. We validate critical values explicitly instead.

COMPONENT="${1:-datamate}"
NAMESPACE="${NAMESPACE:-datamate}"
ENV_FILE="${ENV_FILE:-.env}"

# Parse --component and --namespace from args if passed differently
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --component) COMPONENT="$2"; shift 2 ;;
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# ========== Detect Mode ==========
detect_sealed_secrets() {
    kubectl get deployment -n "$NAMESPACE" sealed-secrets >/dev/null 2>&1 && return 0
    kubectl get deployment -n kube-system sealed-secrets >/dev/null 2>&1 && return 0
    kubectl get pod -n "$NAMESPACE" -l app.kubernetes.io/name=sealed-secrets --no-headers 2>/dev/null | grep -q Running && return 0
    return 1
}

KUBESEAL="$(command -v kubeseal 2>/dev/null || echo "")"
[ -z "$KUBESEAL" ] && KUBESEAL="$HOME/bin/kubeseal"
[ ! -x "$KUBESEAL" ] && [ -x "./tools/bin/kubeseal" ] && KUBESEAL="./tools/bin/kubeseal"
[ ! -x "$KUBESEAL" ] && [ -x "../tools/bin/kubeseal" ] && KUBESEAL="../tools/bin/kubeseal"

# Auto-download kubeseal if controller exists but binary is missing
if detect_sealed_secrets && [ ! -x "$KUBESEAL" ]; then
    echo "[INFO] Sealed Secrets controller detected, but kubeseal not found. Downloading..." >&2
    KUBESEAL_URL="https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.2/kubeseal-0.27.2-$(uname -s | tr '[:upper:]' '[:lower:]')-$(dpkg --print-architecture 2>/dev/null || uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')"
    KUBESEAL_DIR="$HOME/bin"
    mkdir -p "$KUBESEAL_DIR"
    curl -sSL "$KUBESEAL_URL" -o "$KUBESEAL_DIR/kubeseal" && chmod +x "$KUBESEAL_DIR/kubeseal"
    KUBESEAL="$KUBESEAL_DIR/kubeseal"
    echo "[INFO] Installed kubeseal to $KUBESEAL" >&2
fi

if detect_sealed_secrets && [ -x "$KUBESEAL" ]; then
    MODE="sealed"
else
    MODE="plain"
fi

echo "# DataMate secrets collection — component: $COMPONENT, mode: $MODE" >&2

# ========== Helper ==========
random_hex() {
    openssl rand -hex 16 2>/dev/null || python3 -c "import secrets;print(secrets.token_hex(16))"
}

seal_secret() {
    local name="$1" output="$2"
    shift 2
    local raw="${TMP_DIR}/${name}-raw.yaml"
    {
        echo "apiVersion: v1"
        echo "kind: Secret"
        echo "metadata:"
        echo "  name: ${name}"
        echo "  namespace: ${NAMESPACE}"
        echo "type: Opaque"
        echo "stringData:"
        for pair in "$@"; do
            key="${pair%%=*}"
            value="${pair#*=}"
            echo "  ${key}: \"${value}\""
        done
    } > "$raw"
    "$KUBESEAL" --controller-name=sealed-secrets --namespace="${NAMESPACE}" -o yaml -f "$raw" > "$output"
    echo "[INFO] Created SealedSecret: $output" >&2
}

# ========== Load .env (targeted: only reads known secret keys) ==========
if [ -f "$ENV_FILE" ]; then
    echo "[INFO] Loading secrets from ${ENV_FILE}..." >&2

    # Read .env line by line, only extract vars matching our known keys.
    # Ignores comments, blank lines, and unrelated vars like pgsql_host/shell vars.
    while IFS='=' read -r key value; do
        # Skip blank lines and comments
        [ -z "$key" ] && continue
        case "$key" in
            \#*) continue ;;
        esac
        # Strip leading/trailing whitespace from key
        key="$(echo "$key" | xargs)"

        case "$key" in
            DB_PASSWORD|CERT_PASS|DOMAIN|HOME_PAGE_URL|JWT_SECRET|\
            LABEL_STUDIO_PASSWORD|LABEL_STUDIO_USER_TOKEN|POSTGRE_PASSWORD|\
            MINIO_ACCESS_KEY|MINIO_SECRET_KEY)
                val="$value"
                case "$val" in
                    \'*|\"*) val="${val:1}" ;;
                esac
                case "$val" in
                    *\'|*\") val="${val:0:-1}" ;;
                esac
                printf -v "$key" '%s' "$val"
                ;;
        esac
    done < "$ENV_FILE"

    [ -n "$DB_PASSWORD" ] && echo "[INFO] Loaded DB_PASSWORD from $ENV_FILE" >&2
    [ -n "$CERT_PASS" ]   && echo "[INFO] Loaded CERT_PASS from $ENV_FILE" >&2
    [ -n "$JWT_SECRET" ]  && echo "[INFO] Loaded JWT_SECRET from $ENV_FILE" >&2
else
    echo "[WARN] No .env file found at $(pwd)/${ENV_FILE} — will prompt for secrets" >&2
fi

# ========== Datamate ==========
if [ "$COMPONENT" = "datamate" ]; then
    # Collect
    [ -z "$DB_PASSWORD" ] && read -rsp "Enter DB_PASSWORD: " DB_PASSWORD && echo "" >&2
    [ -z "$JWT_SECRET" ]  && JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets;print(secrets.token_hex(32))") && echo "[INFO] Auto-generated JWT_SECRET" >&2
    [ -z "$DOMAIN" ]     && read -rp "Enter DOMAIN (enter to skip): " DOMAIN >&2
    [ -z "$CERT_PASS" ]  && read -rsp "Enter CERT_PASS (enter to skip): " CERT_PASS && echo "" >&2
    HOME_PAGE_URL="${HOME_PAGE_URL:-/data/management}"
    [ -z "$LABEL_STUDIO_PASSWORD" ]   && read -rsp "Enter LABEL_STUDIO_PASSWORD (enter to skip): " LABEL_STUDIO_PASSWORD && echo "" >&2
    [ -z "$LABEL_STUDIO_USER_TOKEN" ] && LABEL_STUDIO_USER_TOKEN=$(random_hex)$(random_hex) && echo "[INFO] Auto-generated LABEL_STUDIO_USER_TOKEN" >&2

    # ===== MANDATORY CHECK: DB_PASSWORD must not be empty =====
    if [ -z "$DB_PASSWORD" ]; then
        echo "[FATAL] DB_PASSWORD is empty! Cannot install without a database password." >&2
        echo "[FATAL] Set DB_PASSWORD in .env or ensure interactive prompts work." >&2
        echo "SECRETS_CREATE=SKIP"
        echo "HELM_VALUES_FILE="
        exit 0
    fi

    if [ "$MODE" = "sealed" ]; then
        # Clean up any old stale Secret (prevents Helm conflict)
        if kubectl get secret datamate-conf -n "$NAMESPACE" >/dev/null 2>&1; then
            echo "[INFO] Removing old datamate-conf Secret..." >&2
            kubectl delete secret datamate-conf -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1
        fi
        # Clean up old SealedSecret (apply is idempotent, but belt-and-suspenders)
        kubectl delete sealedsecret datamate-conf -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1 || true

        # Datamate-conf
        seal_secret "datamate-conf" "${TMP_DIR}/datamate-sealed.yaml" \
            "DB_PASSWORD=${DB_PASSWORD}" \
            "CERT_PASS=${CERT_PASS}" \
            "DOMAIN=${DOMAIN}" \
            "HOME_PAGE_URL=${HOME_PAGE_URL}" \
            "JWT_SECRET=${JWT_SECRET}" \
            "LABEL_STUDIO_PASSWORD=${LABEL_STUDIO_PASSWORD}" \
            "LABEL_STUDIO_USER_TOKEN=${LABEL_STUDIO_USER_TOKEN}"
        kubectl apply -f "${TMP_DIR}/datamate-sealed.yaml" -n "$NAMESPACE" >/dev/null
        # Add Helm ownership labels so 'helm install --force' accepts the Secret
        kubectl wait --for=jsonpath='{.data.DB_PASSWORD}' --timeout=30s secret/datamate-conf -n "$NAMESPACE" >/dev/null 2>&1 || true
        kubectl annotate secret datamate-conf -n "$NAMESPACE" \
            meta.helm.sh/release-name=datamate \
            meta.helm.sh/release-namespace="${NAMESPACE}" \
            --overwrite >/dev/null 2>&1
        kubectl label secret datamate-conf -n "$NAMESPACE" \
            app.kubernetes.io/managed-by=Helm \
            --overwrite >/dev/null 2>&1

        # Label Studio
        if [ -n "$LABEL_STUDIO_PASSWORD" ]; then
            POSTGRE_PASSWORD="${POSTGRE_PASSWORD:-$DB_PASSWORD}"
            seal_secret "label-studio-env" "${TMP_DIR}/label-studio-sealed.yaml" \
                "POSTGRE_PASSWORD=${POSTGRE_PASSWORD}" \
                "LABEL_STUDIO_PASSWORD=${LABEL_STUDIO_PASSWORD}" \
                "LABEL_STUDIO_USER_TOKEN=${LABEL_STUDIO_USER_TOKEN}"
            kubectl apply -f "${TMP_DIR}/label-studio-sealed.yaml" -n "$NAMESPACE" >/dev/null
        fi

        echo "SECRETS_CREATE=false"
        echo "HELM_VALUES_FILE="
    else
        # Plain — delete any old SealedSecret and stale Secret first
        kubectl delete sealedsecret datamate-conf -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1 || true
        if kubectl get secret datamate-conf -n "$NAMESPACE" >/dev/null 2>&1; then
            echo "[INFO] Removing old datamate-conf Secret..." >&2
            kubectl delete secret datamate-conf -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1
        fi

        # Write extra values to /tmp (survives script exit for Helm to read)
        values_file="/tmp/datamate-secret-values-$$.yaml"
        cat > "$values_file" <<VALUES_EOF
public:
  secrets:
    data:
      DB_PASSWORD: "${DB_PASSWORD}"
      JWT_SECRET: "${JWT_SECRET}"
      CERT_PASS: "${CERT_PASS}"
      DOMAIN: "${DOMAIN}"
      HOME_PAGE_URL: "${HOME_PAGE_URL}"
      LABEL_STUDIO_PASSWORD: "${LABEL_STUDIO_PASSWORD}"
      LABEL_STUDIO_USER_TOKEN: "${LABEL_STUDIO_USER_TOKEN}"
VALUES_EOF

        echo "[INFO] Wrote plain secret values to ${values_file}" >&2
        echo "SECRETS_CREATE=true"
        echo "HELM_VALUES_FILE=${values_file}"
    fi

# ========== Milvus ==========
elif [ "$COMPONENT" = "milvus" ]; then
    # Only needed if secret doesn't already exist
    if kubectl get secret milvus-minio-secret -n "$NAMESPACE" >/dev/null 2>&1; then
        echo "# milvus-minio-secret already exists — skipping" >&2
        exit 0
    fi

    [ -z "$MINIO_ACCESS_KEY" ] && MINIO_ACCESS_KEY=$(random_hex) && echo "[INFO] Auto-generated MINIO_ACCESS_KEY" >&2
    [ -z "$MINIO_SECRET_KEY" ] && MINIO_SECRET_KEY=$(random_hex)$(random_hex) && echo "[INFO] Auto-generated MINIO_SECRET_KEY" >&2

    if [ "$MODE" = "sealed" ]; then
        seal_secret "milvus-minio-secret" "${TMP_DIR}/milvus-sealed.yaml" \
            "accesskey=${MINIO_ACCESS_KEY}" \
            "secretkey=${MINIO_SECRET_KEY}"
        kubectl apply -f "${TMP_DIR}/milvus-sealed.yaml" -n "$NAMESPACE" >/dev/null
        kubectl wait --for=jsonpath='{.data.accesskey}' --timeout=30s secret/milvus-minio-secret -n "$NAMESPACE" >/dev/null 2>&1 || true
        kubectl annotate secret milvus-minio-secret -n "$NAMESPACE" \
            meta.helm.sh/release-name=milvus-minio \
            meta.helm.sh/release-namespace="${NAMESPACE}" \
            --overwrite >/dev/null 2>&1
    else
        kubectl create secret generic milvus-minio-secret \
            --from-literal=accesskey="$MINIO_ACCESS_KEY" \
            --from-literal=secretkey="$MINIO_SECRET_KEY" \
            -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
        echo "[INFO] Created milvus-minio-secret (plain)" >&2
    fi
fi
