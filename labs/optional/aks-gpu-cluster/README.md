# Lab: AKS GPU Cluster (Optional)

**WARNING: This lab creates GPU instances that cost real money. An NC6s_v3 instance (1x V100 GPU) costs approximately $3.06/hour. Standard_NC4as_T4_v3 (1x T4) costs approximately $0.53/hour. Remember to tear down when finished.**

## What you'll learn

- How to create an AKS cluster with a GPU-enabled node pool
- How to install the NVIDIA device plugin for GPU scheduling
- How to run Labs 01-06 with real GPU hardware on Azure

## Prerequisites

- An Azure account with an active subscription
- `az` CLI installed and logged in (`az login`)
- Sufficient GPU VM quota in your chosen region (check in the Azure Portal under Subscription > Usage + quotas)
- `kubectl` installed
- Willingness to spend money on GPU instances

## Background

Azure Kubernetes Service (AKS) supports GPU workloads through the
NC-series, ND-series, and NV-series VM families. For inference experimentation,
the `Standard_NC4as_T4_v3` (1x NVIDIA T4, 16 GB GPU memory) offers a good
balance of capability and cost. For training or larger models, the
`Standard_NC6s_v3` (1x V100, 16 GB) provides more compute.

AKS does not install GPU drivers automatically on all VM types. The setup
script in this lab installs the NVIDIA device plugin as a DaemonSet, which
handles driver installation and GPU registration with the kubelet.

## Exercise

### Step 1: Review the setup script

Examine `aks-setup.sh` in this directory. The script creates:

- A resource group for the lab
- An AKS cluster with a system (CPU) node pool
- A GPU node pool with NVIDIA T4 GPUs
- The NVIDIA device plugin DaemonSet
- Configures kubectl to use the new cluster

### Step 2: Create the AKS cluster

Make the script executable and run it:

```bash
chmod +x aks-setup.sh
./aks-setup.sh
```

The script takes 10-15 minutes to complete. It shows progress indicators as
each step finishes.

### Step 3: Verify GPU availability

```bash
kubectl get nodes -l accelerator=nvidia

kubectl describe node $(kubectl get nodes -l accelerator=nvidia -o name | head -1) \
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

Add tolerations for the GPU taint:

```yaml
tolerations:
  - key: "nvidia.com/gpu"
    operator: "Exists"
    effect: "NoSchedule"
```

## Verify it worked

```bash
# Cluster is running
az aks show --resource-group kubecon-gpu-lab-rg --name kubecon-gpu-lab \
  --query "provisioningState" -o tsv

# GPU nodes are available
kubectl get nodes -l accelerator=nvidia

# GPUs are schedulable
kubectl describe nodes | grep "nvidia.com/gpu"
```

## What just happened?

You created an AKS cluster with a dedicated GPU node pool. The NVIDIA device
plugin DaemonSet registers T4 GPUs as schedulable resources, making them
available to pods that request `nvidia.com/gpu` in their resource limits.

## Clean up

**Do this when you are finished to avoid ongoing charges:**

```bash
# Delete the entire resource group (includes AKS cluster and all resources)
az group delete --name kubecon-gpu-lab-rg --yes --no-wait
```

This takes 5-10 minutes. The `--no-wait` flag returns immediately; the deletion
continues in the background. Verify in the Azure Portal that the resource group
is gone.

**Cost reminder:** GPU VMs are billed per second while running. Tear down
promptly when done.

## Next step

Return to the core labs and run them with real GPU hardware.
