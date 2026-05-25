# Secrets Management Setup Guide

This document describes the tools and configuration required for managing encrypted secrets in DataMate.

## Required Tools

### Homebrew Packages (macOS)

| Tool | Version | Purpose | Install Command |
|------|---------|---------|-----------------|
| age | 1.3.1 | Encryption tool for secrets | `brew install age` |
| sops | 3.13.1 | Secrets encryption manager | `brew install sops` |
| helm | 4.1.0+ | Kubernetes package manager | `brew install helm` |

### Helm Plugins

| Plugin | Version | Purpose | Install Method |
|--------|---------|---------|----------------|
| helm-secrets | 4.6.0 | Helm integration with sops | Manual clone (see below) |

**Note:** Helm 4.x has compatibility issues with helm-secrets plugin. Use manual installation:

```bash
cd /Users/macoo/Library/helm/plugins
git clone --depth 1 --branch v4.6.0 https://github.com/jkroepke/helm-secrets.git helm-secrets
```

If plugin fails to load, edit `plugin.yaml` to remove the `command:` field and use only `platformCommand:`.

## Project Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `.sops.yaml` | SOPS encryption rules | Project root |
| `.sops-keys/key.txt` | Age encryption key (private) | Project root (gitignored) |
| `secrets.yaml` | Encrypted secrets per chart | `deployment/helm/<chart>/` |

## Quick Setup

### 1. Install Required Tools

```bash
# macOS (Homebrew)
brew install age sops helm

# Helm plugin (manual)
cd ~/Library/helm/plugins
git clone --depth 1 --branch v4.6.0 https://github.com/jkroepke/helm-secrets.git helm-secrets
```

### 2. Generate Age Key (if not exists)

```bash
mkdir -p .sops-keys
age-keygen -o .sops-keys/key.txt
```

**Important:** Backup the key file securely. It cannot be recovered if lost.

### 3. Update `.sops.yaml` with Your Public Key

```yaml
creation_rules:
  - path_regex: deployment/helm/.*\.yaml$
    age: <your-public-key-from-key.txt>
```

### 4. Create/Encrypt Secrets Files

```bash
# Set environment variable
export SOPS_AGE_KEY_FILE=.sops-keys/key.txt

# Encrypt existing file
sops --encrypt --in-place deployment/helm/datamate/secrets.yaml

# Or create new encrypted file
sops deployment/helm/datamate/secrets.yaml
```

## Usage

### View Decrypted Secrets

```bash
SOPS_AGE_KEY_FILE=.sops-keys/key.txt sops --decrypt deployment/helm/datamate/secrets.yaml
```

### Deploy with Secrets

```bash
# Using helper script
./scripts/secrets.sh helm-install datamate datamate

# Manual method
TMP_FILE=$(mktemp)
SOPS_AGE_KEY_FILE=.sops-keys/key.txt sops --decrypt deployment/helm/datamate/secrets.yaml > $TMP_FILE
helm install datamate deployment/helm/datamate -n datamate -f $TMP_FILE
rm $TMP_FILE
```

### Docker Compose

```bash
# Copy and edit .env
cp deployment/docker/datamate/.env.example deployment/docker/datamate/.env

# Edit with your secrets
vim deployment/docker/datamate/.env

# Deploy
docker compose -f deployment/docker/datamate/docker-compose.yml up -d
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SOPS_AGE_KEY_FILE` | Path to age private key |
| `SOPS_CONFIG` | Path to .sops.yaml (optional) |

## Security Notes

1. **Never commit `.sops-keys/` directory** - It's in `.gitignore`
2. **Backup your age key** - Store in secure location (password manager, encrypted backup)
3. **Use strong passwords** - Generate with `openssl rand -base64 32`
4. **Rotate keys periodically** - Especially after team changes

## Troubleshooting

### Plugin Load Error

If helm plugin shows "both platformCommand and command are set":
```bash
# Edit plugin.yaml
vim ~/Library/helm/plugins/helm-secrets/plugin.yaml
# Remove the "command:" line, keep only "platformCommand:"
```

### Decryption Failed

```bash
# Check key file exists
ls -la .sops-keys/key.txt

# Verify key matches encrypted file's recipient
grep "recipient:" deployment/helm/datamate/secrets.yaml
```

### Key Rotation

```bash
# Generate new key
age-keygen -o .sops-keys/key-new.txt

# Update .sops.yaml with new public key

# Re-encrypt all secrets
for f in deployment/helm/*/secrets.yaml; do
  SOPS_AGE_KEY_FILE=.sops-keys/key.txt sops --decrypt $f > /tmp/plain.yaml
  SOPS_AGE_KEY_FILE=.sops-keys/key-new.txt sops --encrypt /tmp/plain.yaml > $f
done

# Replace old key
mv .sops-keys/key-new.txt .sops-keys/key.txt
```