#!/usr/bin/env bash
# ABOUTME: Creates an AKS cluster with an NVIDIA T4 GPU node pool for running GPU workloads.
# ABOUTME: Includes progress indicators, prerequisite validation, and NVIDIA device plugin setup.

set -euo pipefail

# --- Configuration ---
RESOURCE_GROUP="kubecon-gpu-lab-rg"
CLUSTER_NAME="kubecon-gpu-lab"
LOCATION="eastus"
VM_SIZE_SYSTEM="Standard_DS2_v2"
VM_SIZE_GPU="Standard_NC4as_T4_v3"
MIN_GPU_NODES=1
MAX_GPU_NODES=2
DISK_SIZE_GB=100
K8S_VERSION="1.31"

# --- Color output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- Prerequisites check ---
info "Checking prerequisites..."

if ! command -v az &>/dev/null; then
    error "az CLI not found. Install it from https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

if ! command -v kubectl &>/dev/null; then
    error "kubectl not found. Install it from https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check az login status
if ! az account show &>/dev/null; then
    error "Not logged in to Azure. Run: az login"
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
info "Using subscription: ${SUBSCRIPTION}"
info "Location: ${LOCATION}"
info "GPU VM size: ${VM_SIZE_GPU} (1x NVIDIA T4, 16 GB)"

echo ""
warn "This will create GPU instances that cost real money."
warn "A Standard_NC4as_T4_v3 instance costs approximately \$0.53/hour."
echo ""
read -rp "Continue? (y/N) " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
    info "Aborted."
    exit 0
fi

# --- Step 1: Create resource group ---
info "[Step 1/5] Creating resource group '${RESOURCE_GROUP}'..."
az group create \
    --name "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    --output none
info "Resource group created."

# --- Step 2: Create AKS cluster with system node pool ---
info "[Step 2/5] Creating AKS cluster '${CLUSTER_NAME}' with system node pool..."
info "  This takes 5-10 minutes..."
az aks create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${CLUSTER_NAME}" \
    --location "${LOCATION}" \
    --kubernetes-version "${K8S_VERSION}" \
    --node-count 2 \
    --node-vm-size "${VM_SIZE_SYSTEM}" \
    --os-disk-size-gb 50 \
    --network-plugin azure \
    --generate-ssh-keys \
    --output none
info "AKS cluster created."

# --- Step 3: Add GPU node pool ---
info "[Step 3/5] Adding GPU node pool with ${VM_SIZE_GPU}..."
info "  This takes 5-10 minutes..."
az aks nodepool add \
    --resource-group "${RESOURCE_GROUP}" \
    --cluster-name "${CLUSTER_NAME}" \
    --name gpupool \
    --node-count "${MIN_GPU_NODES}" \
    --min-count "${MIN_GPU_NODES}" \
    --max-count "${MAX_GPU_NODES}" \
    --enable-cluster-autoscaler \
    --node-vm-size "${VM_SIZE_GPU}" \
    --os-disk-size-gb "${DISK_SIZE_GB}" \
    --node-taints "nvidia.com/gpu=true:NoSchedule" \
    --labels "accelerator=nvidia" \
    --output none
info "GPU node pool created."

# --- Step 4: Configure kubectl ---
info "[Step 4/5] Configuring kubectl credentials..."
az aks get-credentials \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${CLUSTER_NAME}" \
    --overwrite-existing
info "kubectl configured."

# --- Step 5: Install NVIDIA device plugin ---
info "[Step 5/5] Installing NVIDIA device plugin..."
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.0/deployments/static/nvidia-device-plugin.yml
info "NVIDIA device plugin installed."

# Wait for the device plugin to be ready
info "Waiting for NVIDIA device plugin pods to be ready..."
kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=120s || \
    warn "Device plugin not fully ready yet. GPU drivers may still be installing."

# --- Verification ---
echo ""
info "Cluster is ready. Verifying GPU nodes..."
echo ""
kubectl get nodes -l accelerator=nvidia
echo ""
info "GPU resources:"
kubectl describe nodes -l accelerator=nvidia \
    | grep -A 3 "nvidia.com/gpu" || warn "GPU resources not yet visible (driver may still be installing)"
echo ""
info "Setup complete."
info "To tear down: az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
