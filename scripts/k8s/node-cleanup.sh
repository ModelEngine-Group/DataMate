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
SELECTED_NODES_FILE="/tmp/datamate-selected-nodes.txt"
LABEL_KEY="node-role.kubernetes.io/datamate"
LABEL_VALUE="true"
TAINT_EFFECT="NoSchedule"
TAINT_APPLIED=false

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
    # Try to read from saved file
    if [ -f "$SELECTED_NODES_FILE" ]; then
        echo -e "${YELLOW}Reading saved configuration from $SELECTED_NODES_FILE${NC}"
        source "$SELECTED_NODES_FILE"
        SELECTED_NODES_STR=$(head -n 1 "$SELECTED_NODES_FILE")
        IFS=' ' read -ra SELECTED_NODES <<< "$SELECTED_NODES_STR"
    else
        # Find nodes with the datamate label
        echo -e "${YELLOW}Finding nodes with $LABEL_KEY label...${NC}"
        NODES=$(kubectl get nodes -l "$LABEL_KEY=$LABEL_VALUE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')
        if [ "$NODES" = "" ]; then
            echo -e "${YELLOW}No nodes found with $LABEL_KEY label.${NC}"
            exit 0
        fi
        SELECTED_NODES=()
        for NODE in $NODES; do
            SELECTED_NODES+=("$NODE")
        done
    fi
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
if [ "$TAINT_APPLIED" = true ]; then
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

# Remove taints if they were applied
if [ "$TAINT_APPLIED" = true ] || [ "$PROVIDED_NODES" != "" ]; then
    for NODE in "${SELECTED_NODES[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY-RUN] kubectl taint node $NODE $LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT-"
        else
            kubectl taint node "$NODE" "$LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT-" --overwrite || true
            echo -e "  ${GREEN}✓${NC} Removed taint from $NODE"
        fi
    done
fi

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"

# Remove the saved file
if [ -f "$SELECTED_NODES_FILE" ]; then
    rm "$SELECTED_NODES_FILE"
    echo -e "${GREEN}Removed $SELECTED_NODES_FILE${NC}"
fi

exit 0
