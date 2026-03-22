#!/usr/bin/env bash
# ABOUTME: Bootstrap script for the AI workshop kind cluster.
# ABOUTME: Creates the cluster, installs cert-manager, and reports progress.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="ai-workshop"
CERT_MANAGER_VERSION="v1.17.1"

# --- Helper functions --------------------------------------------------------

info()  { printf "\033[1;34m[INFO]\033[0m  %s\n" "$*"; }
ok()    { printf "\033[1;32m[OK]\033[0m    %s\n" "$*"; }
fail()  { printf "\033[1;31m[FAIL]\033[0m  %s\n" "$*"; exit 1; }

check_tool() {
    local tool="$1"
    if ! command -v "$tool" &>/dev/null; then
        fail "'$tool' is not installed. Please install it before running this script."
    fi
    ok "$tool found: $(command -v "$tool")"
}

# --- Step 1: Check prerequisites ---------------------------------------------

info "Step 1/3: Checking prerequisites..."
check_tool docker
check_tool kind
check_tool kubectl
check_tool helm

# Make sure the Docker daemon is actually running.
if ! docker info &>/dev/null; then
    fail "Docker is installed but the daemon is not running. Start Docker and try again."
fi
ok "Docker daemon is running."

# --- Step 2: Create the kind cluster -----------------------------------------

info "Step 2/3: Creating kind cluster '$CLUSTER_NAME'..."

# If the cluster already exists, skip creation so the script is idempotent.
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    info "Cluster '$CLUSTER_NAME' already exists — skipping creation."
else
    info "Pulling node images and starting containers (this may take 1-3 minutes)..."
    kind create cluster --config "${SCRIPT_DIR}/kind-cluster.yaml" --wait 120s
    ok "Kind cluster '$CLUSTER_NAME' created."
fi

# Point kubectl at the new cluster.
kubectl cluster-info --context "kind-${CLUSTER_NAME}" >/dev/null 2>&1 \
    || fail "Cannot connect to the cluster. Check 'kind get clusters' output."
ok "kubectl context set to kind-${CLUSTER_NAME}."

# --- Step 3: Install cert-manager --------------------------------------------

info "Step 3/3: Installing cert-manager ${CERT_MANAGER_VERSION}..."

# Add the Jetstack Helm repo (cert-manager publisher).
helm repo add jetstack https://charts.jetstack.io --force-update >/dev/null 2>&1
helm repo update >/dev/null 2>&1
ok "Helm repo 'jetstack' added and updated."

# Install or upgrade cert-manager. The --wait flag blocks until pods are ready.
info "Deploying cert-manager (this may take 1-2 minutes)..."
helm upgrade --install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version "${CERT_MANAGER_VERSION}" \
    --set crds.enabled=true \
    --wait \
    --timeout 120s \
    >/dev/null 2>&1
ok "cert-manager ${CERT_MANAGER_VERSION} is running."

# --- Done --------------------------------------------------------------------

echo ""
info "============================================"
ok   "Setup complete!"
info "============================================"
echo ""
info "Cluster: $CLUSTER_NAME"
info "Nodes:   $(kubectl get nodes --no-headers | wc -l | tr -d ' ') (1 control-plane + 2 workers)"
info "Run ./verify.sh to confirm everything is healthy."
