# Lab: EKS GPU Cluster (Optional)

**WARNING: This lab creates GPU instances that cost real money. A g5.xlarge instance costs approximately $1.01/hour. Remember to tear down when finished.**

## What you'll learn

- How to create an EKS cluster with GPU-enabled node groups
- How to install the NVIDIA DRA driver for GPU resource management
- How to run Labs 01-06 with real GPU hardware

## Prerequisites

- An AWS account with permissions to create EKS clusters and EC2 instances
- `eksctl` installed ([installation guide](https://eksctl.io/installation/))
- `aws` CLI installed and configured with valid credentials
- `kubectl` installed
- Willingness to spend money on GPU instances

## Background

The core labs (00-06) run on kind without GPUs, using CPU-only workloads and
conceptual walkthroughs where GPUs would be needed. This optional lab creates
a real EKS cluster with NVIDIA GPU nodes so you can run the full labs with
actual GPU acceleration.

We use `g5.xlarge` instances (1x NVIDIA A10G, 24 GB GPU memory) which are the
most cost-effective GPU instances for experimentation on AWS. The cluster
configuration uses a managed node group with 1-2 nodes to minimize cost while
providing enough capacity to run inference workloads.

## Exercise

### Step 1: Review the eksctl configuration

Examine `eksctl-config.yaml` in this directory. Key settings:

- **Region**: us-east-1 (best GPU instance availability; change if needed)
- **Node type**: g5.xlarge (1x A10G GPU, 4 vCPUs, 16 GB RAM)
- **Scaling**: 1 node minimum, 2 nodes maximum
- **EBS storage**: 100 GB gp3 per node (models need disk space)

### Step 2: Create the EKS cluster

```bash
eksctl create cluster -f eksctl-config.yaml
```

This takes 15-20 minutes. eksctl will create the VPC, subnets, EKS control
plane, and managed node group.

Verify the cluster is ready:

```bash
kubectl get nodes
```

You should see one node with instance type `g5.xlarge`.

### Step 3: Install the NVIDIA GPU Operator

The GPU Operator installs the NVIDIA drivers, device plugin, and container
toolkit automatically:

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --set driver.enabled=true \
  --set toolkit.enabled=true \
  --wait --timeout=10m
```

Verify GPUs are available:

```bash
kubectl get nodes -o json | \
  jq '.items[].status.capacity["nvidia.com/gpu"]'
```

You should see `"1"` for each GPU node.

### Step 4: Install the NVIDIA DRA Driver (optional)

If you want to use Dynamic Resource Allocation (Lab 02) with real GPUs:

```bash
helm install nvidia-dra-driver nvidia/nvidia-dra-driver \
  --namespace nvidia-dra-driver \
  --create-namespace \
  --set driver.enabled=true \
  --wait --timeout=5m
```

> **Note:** DRA support requires Kubernetes 1.31+ and the DynamicResourceAllocation
> feature gate enabled. EKS 1.31+ has this available but it may need to be
> explicitly enabled. Check the EKS documentation for your version.

### Step 5: Run the labs with real GPUs

With GPU nodes available, you can now run the labs with actual GPU workloads:

- **Lab 01 (Kueue)**: Create ResourceFlavors for `nvidia.com/gpu` resources
- **Lab 02 (DRA)**: Use real GPU ResourceClaims instead of simulated ones
- **Lab 04 (KServe)**: Deploy GPU-accelerated model servers (e.g., Triton, vLLM)
- **Lab 05 (Gateway Routing)**: Run real inference backends for end-to-end routing

Adjust the manifests to request GPU resources:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

## Verify it worked

```bash
# Cluster is running
kubectl cluster-info

# GPU nodes are available
kubectl get nodes -l node.kubernetes.io/instance-type=g5.xlarge

# GPUs are allocatable
kubectl describe node | grep -A 5 "Allocatable:" | grep gpu
```

## What just happened?

You created a production-grade Kubernetes cluster on AWS with NVIDIA GPU nodes.
The GPU Operator handles driver installation and device plugin registration
automatically, making GPUs available as schedulable resources in your cluster.

## Clean up

**Do this when you are finished to avoid ongoing charges:**

```bash
# Delete any lab resources first
kubectl delete namespace inference kueue-system agents 2>/dev/null

# Delete the entire EKS cluster (includes all node groups)
eksctl delete cluster -f eksctl-config.yaml --disable-nodegroup-eviction
```

This takes 10-15 minutes. Verify in the AWS Console that:
- The EKS cluster is deleted
- All EC2 instances are terminated
- The associated VPC is removed

**Cost reminder:** A single g5.xlarge instance costs ~$1.01/hour (~$24/day).
Do not leave the cluster running overnight unless you intend to.

## Next step

Return to the core labs and run them with real GPU hardware.
