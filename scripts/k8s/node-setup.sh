#!/bin/bash
#
# DataMate Node Setup Script
# Interactive script to select nodes with keyboard navigation (↑/↓ or j/k)
# Automatically applies labels and taints for DataMate deployment
#
# Usage: ./node-setup.sh [--dry-run] [--namespace NAMESPACE] [--skip-taint]
#

set -e

# ============================================================================
# Configuration
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fixed label and taint values (no prompts needed)
NAMESPACE="datamate"
LABEL_KEY="node-role.kubernetes.io/datamate"
LABEL_VALUE="true"
TAINT_EFFECT="NoSchedule"
DRY_RUN=false
SKIP_TAINT=false

# ============================================================================
# Argument Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --skip-taint)
                SKIP_TAINT=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_prerequisites() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}Error: kubectl is not installed${NC}"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
}

# ============================================================================
# Node Data Collection
# ============================================================================

fetch_nodes() {
    echo -e "${YELLOW}Fetching available nodes...${NC}"

    NODES=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')
    NODE_COUNT=$(echo "$NODES" | wc -l | tr -d ' ')

    if [ "$NODE_COUNT" -eq 0 ]; then
        echo -e "${RED}Error: No nodes found in the cluster${NC}"
        exit 1
    fi

    # Build node array with status info
    NODE_ARRAY=()
    NODE_STATUS=()
    NODE_HAS_LABEL=()

    for NODE in $NODES; do
        NODE_ARRAY+=("$NODE")

        # Get status
        STATUS=$(kubectl get node "$NODE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        NODE_STATUS+=("$STATUS")

        # Check if already labeled
        CURRENT_LABEL=$(kubectl get node "$NODE" -o jsonpath='{.metadata.labels.node-role\.kubernetes\.io/datamate}')
        if [ "$CURRENT_LABEL" = "true" ]; then
            NODE_HAS_LABEL+=("true")
        else
            NODE_HAS_LABEL+=("false")
        fi
    done
}

# ============================================================================
# Interactive Menu Functions
# ============================================================================

# Initialize selection state array
init_selection() {
    SELECTED=()
    for i in $(seq 1 $NODE_COUNT); do
        SELECTED+=("false")
    done
    CURRENT_INDEX=0
}

# Print the interactive menu
print_menu() {
    # Clear screen and print header
    echo -e "\033[2J\033[H"
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}  DataMate Node Setup${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""
    echo -e "${CYAN}Select nodes for DataMate deployment${NC}"
    echo ""

    # Print each node with selection marker
    for i in $(seq 0 $(($NODE_COUNT - 1))); do
        NODE="${NODE_ARRAY[$i]}"
        STATUS="${NODE_STATUS[$i]}"
        HAS_LABEL="${NODE_HAS_LABEL[$i]}"
        IS_SELECTED="${SELECTED[$i]}"

        # Status display
        if [ "$STATUS" = "True" ]; then
            STATUS_DISPLAY="${GREEN}Ready${NC}"
        else
            STATUS_DISPLAY="${RED}NotReady${NC}"
        fi

        # Label marker
        LABEL_MARKER=""
        if [ "$HAS_LABEL" = "true" ]; then
            LABEL_MARKER=" ${GREEN}[datamate]${NC}"
        fi

        # Selection marker
        if [ "$IS_SELECTED" = "true" ]; then
            MARKER="${GREEN}[x]${NC}"
        else
            MARKER="${NC}[ ]${NC}"
        fi

        # Highlight current row
        if [ "$i" -eq "$CURRENT_INDEX" ]; then
            echo -e "  ${YELLOW}→${NC} $MARKER ${CYAN}$NODE${NC} ($STATUS_DISPLAY)$LABEL_MARKER"
        else
            echo -e "    $MARKER $NODE ($STATUS_DISPLAY)$LABEL_MARKER"
        fi
    done

    echo ""
    echo -e "${YELLOW}Navigation:${NC} ↑/k: up  ↓/j: down  ${GREEN}space${NC}: toggle  ${GREEN}enter${NC}: confirm  ${RED}q${NC}: quit"
    echo ""

    # Show current selection count
    SELECTED_COUNT=0
    for s in "${SELECTED[@]}"; do
        if [ "$s" = "true" ]; then
            SELECTED_COUNT=$((SELECTED_COUNT + 1))
        fi
    done
    echo -e "${BLUE}Selected: ${SELECTED_COUNT}/${NODE_COUNT} nodes${NC}"
}

# Toggle selection at current index
toggle_selection() {
    if [ "${SELECTED[$CURRENT_INDEX]}" = "true" ]; then
        SELECTED[$CURRENT_INDEX]="false"
    else
        SELECTED[$CURRENT_INDEX]="true"
    fi
}

# Move cursor up
move_up() {
    if [ "$CURRENT_INDEX" -gt 0 ]; then
        CURRENT_INDEX=$((CURRENT_INDEX - 1))
    fi
}

# Move cursor down
move_down() {
    if [ "$CURRENT_INDEX" -lt $(($NODE_COUNT - 1)) ]; then
        CURRENT_INDEX=$((CURRENT_INDEX + 1))
    fi
}

# Get selected nodes list
get_selected_nodes() {
    SELECTED_NODES=()
    for i in $(seq 0 $(($NODE_COUNT - 1))); do
        if [ "${SELECTED[$i]}" = "true" ]; then
            SELECTED_NODES+=("${NODE_ARRAY[$i]}")
        fi
    done
}

# ============================================================================
# Keyboard Input Handling
# ============================================================================

# Read single keypress (with fallback for non-terminal environments)
read_key() {
    # Check if we're in a proper terminal
    if [ ! -t 0 ]; then
        # Not in terminal - use simple read mode
        read -r key
        echo "$key"
        return
    fi

    # Save current terminal settings
    old_stty=$(stty -g 2>/dev/null) || return 1

    # Set terminal to raw mode for single char read
    stty raw -echo 2>/dev/null

    # Read key
    key=$(dd bs=1 count=1 2>/dev/null)

    # Check for arrow keys (escape sequence)
    if [ "$key" = $'\x1b' ]; then
        # Read the next two chars for arrow key sequence
        read -rs -t0.1 -n2 key2 2>/dev/null || true
        key="${key}${key2}"
    fi

    # Restore terminal settings BEFORE processing
    stty "$old_stty" 2>/dev/null || true

    # In raw mode, Enter produces \r (carriage return), convert to \n for easier matching
    if [ "$key" = $'\x0d' ]; then
        key=$'\x0a'
    fi

    echo "$key"
}

# Main interactive loop
interactive_selection() {
    init_selection

    while true; do
        print_menu

        key=$(read_key)

        case "$key" in
            # Arrow up or 'k'
            $'\x1b[A'|k)
                move_up
                ;;
            # Arrow down or 'j'
            $'\x1b[B'|j)
                move_down
                ;;
            # Space - toggle selection
            ' ')
                toggle_selection
                ;;
            # Enter - confirm
            ''|$'\x0a')
                get_selected_nodes
                if [ ${#SELECTED_NODES[@]} -eq 0 ]; then
                    echo -e "${YELLOW}No nodes selected. Please select at least one node.${NC}"
                    sleep 1
                else
                    return 0
                fi
                ;;
            # Q - quit/skip
            q|Q)
                echo -e "\n${YELLOW}Skipping node setup.${NC}"
                echo ""
                echo "HELM_NODE_SELECTOR_ARGS="
                echo "HELM_TOLERATIONS_ARGS="
                exit 0
                ;;
        esac
    done
}

# ============================================================================
# Apply Configuration
# ============================================================================

apply_labels_and_taints() {
    echo ""
    echo -e "${GREEN}Applying configuration...${NC}"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "  Label: ${LABEL_KEY}=${LABEL_VALUE}"
    if [ "$SKIP_TAINT" = false ]; then
        echo "  Taint: ${LABEL_KEY}=${LABEL_VALUE}:${TAINT_EFFECT}"
    fi
    echo ""

    # Apply labels
    for NODE in "${SELECTED_NODES[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY-RUN] kubectl label node $NODE $LABEL_KEY=$LABEL_VALUE --overwrite"
        else
            kubectl label node "$NODE" "$LABEL_KEY=$LABEL_VALUE" --overwrite
            echo -e "  ${GREEN}✓${NC} Applied label to $NODE"
        fi
    done

    # Apply taints (unless skipped)
    if [ "$SKIP_TAINT" = false ]; then
        for NODE in "${SELECTED_NODES[@]}"; do
            if [ "$DRY_RUN" = true ]; then
                echo "[DRY-RUN] kubectl taint node $NODE $LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT --overwrite"
            else
                kubectl taint node "$NODE" "$LABEL_KEY=$LABEL_VALUE:$TAINT_EFFECT" --overwrite
                echo -e "  ${GREEN}✓${NC} Applied taint to $NODE"
            fi
        done
    fi

    echo ""
    echo -e "${GREEN}Configuration complete!${NC}"
}

# ============================================================================
# Generate Helm Arguments
# ============================================================================

generate_helm_args() {
    # Escape dots in label key for Helm (dots are interpreted as nested keys)
    LABEL_KEY_ESCAPED=$(echo "$LABEL_KEY" | sed 's/\./\\./g')

    # Use --set-string to force string type (avoids boolean interpretation)

    # Node selector args
    HELM_NODE_SELECTOR_ARGS="--set-string global.nodeSelector.${LABEL_KEY_ESCAPED}=${LABEL_VALUE}"

    SERVICES="backend backend-python database frontend gateway runtime"
    for SERVICE in $SERVICES; do
        HELM_NODE_SELECTOR_ARGS="$HELM_NODE_SELECTOR_ARGS --set-string ${SERVICE}.nodeSelector.${LABEL_KEY_ESCAPED}=${LABEL_VALUE}"
    done

    # Tolerations args (if taint applied)
    if [ "$SKIP_TAINT" = false ]; then
        HELM_TOLERATIONS_ARGS="--set-string global.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string global.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string global.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string global.tolerations[0].effect=${TAINT_EFFECT}"

        for SERVICE in $SERVICES; do
            HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ${SERVICE}.tolerations[0].key=${LABEL_KEY}"
            HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ${SERVICE}.tolerations[0].operator=Equal"
            HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ${SERVICE}.tolerations[0].value=${LABEL_VALUE}"
            HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ${SERVICE}.tolerations[0].effect=${TAINT_EFFECT}"
        done

        # Ray cluster
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.head.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.head.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.head.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.head.tolerations[0].effect=${TAINT_EFFECT}"

        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.worker.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.worker.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.worker.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.worker.tolerations[0].effect=${TAINT_EFFECT}"

        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.npuGroup.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.npuGroup.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.npuGroup.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.npuGroup.tolerations[0].effect=${TAINT_EFFECT}"

        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.gpuGroup.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.gpuGroup.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.gpuGroup.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string ray-cluster.additionalWorkerGroups.gpuGroup.tolerations[0].effect=${TAINT_EFFECT}"

        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string kuberay-operator.tolerations[0].key=${LABEL_KEY}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string kuberay-operator.tolerations[0].operator=Equal"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string kuberay-operator.tolerations[0].value=${LABEL_VALUE}"
        HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS --set-string kuberay-operator.tolerations[0].effect=${TAINT_EFFECT}"
    else
        HELM_TOLERATIONS_ARGS=""
    fi

    echo ""
    echo -e "${BLUE}Helm installation arguments:${NC}"
    echo ""

    # Write Helm args to temp file for Makefile to source
    HELM_ARGS_FILE="/tmp/datamate-helm-args.sh"
    cat > "$HELM_ARGS_FILE" <<EOF
export HELM_NODE_SELECTOR_ARGS="$HELM_NODE_SELECTOR_ARGS"
export HELM_TOLERATIONS_ARGS="$HELM_TOLERATIONS_ARGS"
EOF
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    parse_args "$@"

    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}  DataMate Node Setup${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    # Ask if user wants to configure nodes
    echo "Configure dedicated nodes for DataMate deployment?"
    echo "This will apply labels and taints to selected nodes."
    echo ""
    echo "1. Yes - Configure nodes interactively"
    echo "2. No - Use default scheduling (recommended for development)"
    echo ""
    echo -n "Enter choice [default: 2]: "

    if [ ! -t 0 ]; then
        # Not in terminal - use simple read
        read -r choice
    else
        # In terminal - can use keyboard navigation
        choice=""
        read -r choice
    fi

    # Default to "No" if empty or not "1"
    if [ -z "$choice" ] || [ "$choice" != "1" ]; then
        echo ""
        echo -e "${YELLOW}Skipping node configuration. Using default scheduling.${NC}"
        echo ""
        # Create empty args file
        HELM_ARGS_FILE="/tmp/datamate-helm-args.sh"
        cat > "$HELM_ARGS_FILE" <<EOF
export HELM_NODE_SELECTOR_ARGS=""
export HELM_TOLERATIONS_ARGS=""
EOF
        echo -e "${GREEN}Helm arguments written to $HELM_ARGS_FILE${NC}"
        exit 0
    fi

    echo ""

    check_prerequisites
    fetch_nodes
    interactive_selection
    apply_labels_and_taints
    generate_helm_args

    exit 0
}

# Run main function
main "$@"
