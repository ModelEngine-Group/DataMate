#!/bin/bash
#
# DataMate Node Cleanup Script
# Remove labels and taints from nodes that were configured for DataMate deployment
#
# Usage: ./node-cleanup.sh [--dry-run] [--nodes NODE1,NODE2]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DRY_RUN=false
NAMESPACE="datamate"
LABEL_KEY="node-role.kubernetes.io/datamate"
LABEL_VALUE="true"
TAINT_EFFECT="NoSchedule"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --nodes)
            PROVIDED_NODES="$2"
            shift 2
            ;;
        --label-key)
            LABEL_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DataMate Node Cleanup${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if connected to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Determine nodes to clean up
if [ "$PROVIDED_NODES" != "" ]; then
    # Use provided nodes
    IFS=',' read -ra SELECTED_NODES <<< "$PROVIDED_NODES"
else
    # Find nodes with the datamate label directly from Kubernetes
    echo -e "${YELLOW}Finding nodes with $LABEL_KEY=$LABEL_VALUE label...${NC}"
    NODES=$(kubectl get nodes -l "$LABEL_KEY=$LABEL_VALUE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')

    if [ -z "$NODES" ]; then
        echo -e "${GREEN}No nodes found with $LABEL_KEY=$LABEL_VALUE label.${NC}"
        echo -e "${YELLOW}Cleanup not needed - no nodes were labeled.${NC}"
        exit 0
    fi

    SELECTED_NODES=()
    while IFS= read -r NODE; do
        if [ -n "$NODE" ]; then
            SELECTED_NODES+=("$NODE")
        fi
    done <<< "$NODES"
fi

if [ ${#SELECTED_NODES[@]} -eq 0 ]; then
    echo -e "${YELLOW}No nodes to clean up.${NC}"
    exit 0
fi

echo -e "${GREEN}Nodes to clean up:${NC}"
for NODE in "${SELECTED_NODES[@]}"; do
    echo "  - $NODE"
done

echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Label to remove: $LABEL_KEY"

# Check if any node has the taint
HAS_TAINTS=false
for NODE in "${SELECTED_NODES[@]}"; do
    TAINT_COUNT=$(kubectl get node "$NODE" -o jsonpath='{range .spec.taints[*]}{.key}{"\n"}{end}' | grep -c "^${LABEL_KEY}$" || echo "0")
    if [ "$TAINT_COUNT" -gt 0 ]; then
        HAS_TAINTS=true
        break
    fi
done

if [ "$HAS_TAINTS" = true ]; then
    echo "  Taint to remove: $LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT"
fi
echo ""

read -p "Remove labels and taints? (y/n) [y]: " CONFIRM
CONFIRM=${CONFIRM:-y}

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Removing configuration...${NC}"

# Remove labels from selected nodes
for NODE in "${SELECTED_NODES[@]}"; do
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] kubectl label node $NODE $LABEL_KEY-"
    else
        kubectl label node "$NODE" "$LABEL_KEY-" --overwrite
        echo -e "  ${GREEN}✓${NC} Removed label from $NODE"
    fi
done

# Remove taints (check if node has the taint)
for NODE in "${SELECTED_NODES[@]}"; do
    # Check if node has the taint
    HAS_TAINT=$(kubectl get node "$NODE" -o jsonpath='{range .spec.taints[*]}{.key}{"\n"}{end}' | grep -c "^${LABEL_KEY}$" || echo "0")

    if [ "$HAS_TAINT" -gt 0 ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY-RUN] kubectl taint node $NODE $LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT-"
        else
            kubectl taint node "$NODE" "$LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT-" --overwrite || true
            echo -e "  ${GREEN}✓${NC} Removed taint from $NODE"
        fi
    else
        echo -e "  ${YELLOW}○${NC} No taint to remove from $NODE"
    fi
done

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"

# Clean up Helm args temp file if it exists
if [ -f /tmp/datamate-helm-args.sh ]; then
    rm /tmp/datamate-helm-args.sh
    echo -e "${GREEN}Removed /tmp/datamate-helm-args.sh${NC}"
fi

exit 0
