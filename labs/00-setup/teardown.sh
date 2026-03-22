#!/usr/bin/env bash
# ABOUTME: Teardown script for the AI workshop kind cluster.
# ABOUTME: Deletes the cluster and confirms removal.

set -euo pipefail

CLUSTER_NAME="ai-workshop"

info() { printf "\033[1;34m[INFO]\033[0m  %s\n" "$*"; }
ok()   { printf "\033[1;32m[OK]\033[0m    %s\n" "$*"; }

info "Deleting kind cluster '$CLUSTER_NAME'..."

if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    info "Cluster '$CLUSTER_NAME' does not exist — nothing to delete."
    exit 0
fi

kind delete cluster --name "$CLUSTER_NAME"
ok "Cluster '$CLUSTER_NAME' deleted."
info "All resources inside the cluster have been removed."
info "Run ./setup.sh to recreate the cluster at any time."
