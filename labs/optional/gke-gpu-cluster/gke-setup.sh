#!/usr/bin/env bash
# ABOUTME: Creates a GKE cluster with an NVIDIA L4 GPU node pool for running GPU workloads.
# ABOUTME: Includes progress indicators and validates prerequisites before starting.

set -euo pipefail

# --- Configuration ---
CLUSTER_NAME="kubecon-gpu-lab"
ZONE="us-central1-a"
MACHINE_TYPE_CPU="e2-standard-4"
MACHINE_TYPE_GPU="g2-standard-8"
GPU_TYPE="nvidia-l4"
GPU_COUNT=1
MIN_GPU_NODES=1
MAX_GPU_NODES=2
DISK_SIZE_GB=100

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

if ! command -v gcloud &>/dev/null; then
    error "gcloud CLI not found. Install it from https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v kubectl &>/dev/null; then
    error "kubectl not found. Install it from https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
    error "No GCP project set. Run: gcloud config set project <PROJECT_ID>"
    exit 1
fi

info "Using project: ${PROJECT_ID}"
info "Zone: ${ZONE}"
info "GPU type: ${GPU_TYPE} (${GPU_COUNT} per node)"

echo ""
warn "This will create GPU instances that cost real money."
warn "An NVIDIA L4 on GKE costs approximately \$0.70/hour plus VM costs."
echo ""
read -rp "Continue? (y/N) " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
    info "Aborted."
    exit 0
fi

# --- Step 1: Enable required APIs ---
info "[Step 1/4] Enabling required GCP APIs..."
gcloud services enable container.googleapis.com compute.googleapis.com \
    --project="${PROJECT_ID}" --quiet
info "APIs enabled."

# --- Step 2: Create the GKE cluster with a CPU node pool ---
info "[Step 2/4] Creating GKE cluster '${CLUSTER_NAME}' with CPU node pool..."
info "  This takes 5-10 minutes..."
gcloud container clusters create "${CLUSTER_NAME}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE_CPU}" \
    --num-nodes=2 \
    --disk-size="${DISK_SIZE_GB}" \
    --disk-type=pd-standard \
    --release-channel=regular \
    --workload-pool="${PROJECT_ID}.svc.id.goog" \
    --quiet
info "Cluster created."

# --- Step 3: Add GPU node pool ---
info "[Step 3/4] Adding GPU node pool with ${GPU_TYPE}..."
info "  This takes 5-10 minutes..."
gcloud container node-pools create gpu-pool \
    --cluster="${CLUSTER_NAME}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE_GPU}" \
    --accelerator="type=${GPU_TYPE},count=${GPU_COUNT}" \
    --num-nodes="${MIN_GPU_NODES}" \
    --min-nodes="${MIN_GPU_NODES}" \
    --max-nodes="${MAX_GPU_NODES}" \
    --enable-autoscaling \
    --disk-size="${DISK_SIZE_GB}" \
    --disk-type=pd-ssd \
    --node-taints="nvidia.com/gpu=true:NoSchedule" \
    --quiet
info "GPU node pool created."

# --- Step 4: Configure kubectl ---
info "[Step 4/4] Configuring kubectl credentials..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" \
    --zone="${ZONE}" --quiet
info "kubectl configured."

# --- Verification ---
echo ""
info "Cluster is ready. Verifying GPU nodes..."
echo ""
kubectl get nodes -l cloud.google.com/gke-accelerator="${GPU_TYPE}"
echo ""
info "GPU resources:"
kubectl describe nodes -l cloud.google.com/gke-accelerator="${GPU_TYPE}" \
    | grep -A 3 "nvidia.com/gpu" || warn "GPU resources not yet visible (driver may still be installing)"
echo ""
info "Setup complete. To tear down: gcloud container clusters delete ${CLUSTER_NAME} --zone ${ZONE} --quiet"
