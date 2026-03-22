# Lab: GKE GPU Cluster (Optional)

**WARNING: This lab creates GPU instances that cost real money. An NVIDIA L4 GPU on GKE costs approximately $0.70/hour (plus VM costs). Remember to tear down when finished.**

## What you'll learn

- How to create a GKE cluster with a GPU-enabled node pool
- How to run Labs 01-06 with real GPU hardware on Google Cloud

## Prerequisites

- A Google Cloud account with billing enabled
- `gcloud` CLI installed and configured (`gcloud auth login`, `gcloud config set project <PROJECT_ID>`)
- Sufficient GPU quota in your chosen region (check: `gcloud compute regions describe <REGION>`)
- `kubectl` installed
- Willingness to spend money on GPU instances

## Background

GKE has first-class support for GPU workloads. GPU drivers are automatically
installed on GPU node pools, and GKE integrates with NVIDIA's device plugin
out of the box. This makes GKE one of the simplest platforms for running
GPU-accelerated Kubernetes workloads.

We use NVIDIA L4 GPUs (`g2-standard-8`), which provide 24 GB of GPU memory at a
lower cost than A100 or H100 instances. L4s are widely available and sufficient
for inference with models up to ~13B parameters.

## Exercise

### Step 1: Review the setup script

Examine `gke-setup.sh` in this directory. The script creates:

- A GKE Standard cluster with a default CPU node pool
- A GPU node pool with NVIDIA L4 GPUs
- Configures kubectl to use the new cluster

### Step 2: Create the GKE cluster

Make the script executable and run it:

```bash
chmod +x gke-setup.sh
./gke-setup.sh
```

The script takes 10-15 minutes to complete. It shows progress as each step
finishes.

### Step 3: Verify GPU availability

```bash
kubectl get nodes -l cloud.google.com/gke-accelerator=nvidia-l4

kubectl describe node $(kubectl get nodes -l cloud.google.com/gke-accelerator=nvidia-l4 -o name | head -1) \
  | grep -A 5 "Allocatable:"
```

You should see `nvidia.com/gpu: 1` in the allocatable resources.

### Step 4: Run the labs with real GPUs

With GPU nodes available, adjust lab manifests to request GPU resources:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

See the EKS lab README for specific guidance on which labs benefit from GPUs.

## Verify it worked

```bash
# Cluster is running
gcloud container clusters describe kubecon-gpu-lab --zone us-central1-a --format='value(status)'

# GPU nodes are in the pool
kubectl get nodes -l cloud.google.com/gke-accelerator=nvidia-l4

# GPUs are schedulable
kubectl describe nodes | grep "nvidia.com/gpu"
```

## What just happened?

You created a GKE cluster with a dedicated GPU node pool. GKE automatically
installed the NVIDIA GPU drivers and device plugin, making L4 GPUs available
as schedulable Kubernetes resources.

## Clean up

**Do this when you are finished to avoid ongoing charges:**

```bash
gcloud container clusters delete kubecon-gpu-lab \
  --zone us-central1-a \
  --quiet
```

This takes 5-10 minutes. Verify in the GCP Console that the cluster and
associated resources (VMs, disks) are deleted.

**Cost reminder:** GPU VMs are billed per second. Tear down promptly when done.

## Next step

Return to the core labs and run them with real GPU hardware.
