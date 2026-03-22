# Lab 00: Environment Setup

## What you'll learn

- How to create a kind (Kubernetes IN Docker) cluster configured for AI workload labs
- How to install shared prerequisites like cert-manager
- How to verify your environment is ready for the remaining labs

## Prerequisites

- Docker installed and running
- ~8 GB RAM available for the cluster
- Internet connection for pulling container images
- A terminal with `bash` available

## Background

Throughout this workshop, we use **kind** (Kubernetes IN Docker) to run a local
Kubernetes cluster entirely inside Docker containers. Kind is ideal for learning
because it gives you a real, conformant Kubernetes cluster without needing cloud
infrastructure or bare-metal servers. You can create and tear down clusters in
seconds, experiment freely, and start over whenever you need to.

The cluster configuration in this lab creates one control-plane node and two
worker nodes. The workers are labeled with `node.kubernetes.io/gpu-type:
simulated` to mimic nodes that have GPUs attached. Real AI and ML workloads
depend on GPUs for training and inference, and Kubernetes uses node labels to
schedule pods onto the right hardware. By adding these labels now, later labs
can demonstrate scheduling, resource management, and topology-aware placement
without requiring actual GPU hardware.

We also label the two workers with different topology zones (`zone-a` and
`zone-b`). In production clusters, zones represent failure domains — separate
racks, availability zones, or data centers. Several labs use zone-aware
scheduling to show how Kubernetes distributes AI workloads for resilience.

**An honest note about limitations:** These labs simulate GPU concepts using
CPU-based workloads. You will not see real GPU memory allocation, CUDA kernels,
or hardware acceleration. The goal is to learn the Kubernetes primitives —
scheduling, queuing, resource claims, inference serving, and routing — that
apply identically whether the underlying hardware is simulated or real. When you
move to a cluster with actual GPUs, the only change is swapping simulated labels
and resources for real device plugins.

> **Kubernetes version note:** This lab uses `kindest/node` images for
> Kubernetes 1.33. If you want to use a different version, update the `image:`
> lines in `kind-cluster.yaml`.

## Exercise

### Step 1: Install prerequisites

If you already have these tools installed, skip to Step 2. Otherwise, install
each one:

**kind** — creates local Kubernetes clusters using Docker containers:

```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS (Intel)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-darwin-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS (Apple Silicon)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-darwin-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

**kubectl** — the Kubernetes command-line tool:

```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl

# macOS
brew install kubectl
```

**Helm** — the Kubernetes package manager (used to install cert-manager and
other components):

```bash
# Linux / macOS
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Verify each tool is available:

```bash
kind version
kubectl version --client
helm version
```

### Step 2: Create the cluster

Run the setup script from this directory:

```bash
cd labs/00-setup
./setup.sh
```

The script performs these actions in order:

1. Checks that `docker`, `kind`, `kubectl`, and `helm` are installed.
2. Creates a kind cluster named `ai-workshop` using the configuration in
   `kind-cluster.yaml`. This pulls the Kubernetes node images and starts three
   Docker containers (one control plane, two workers).
3. Installs **cert-manager** via Helm. Cert-manager automates TLS certificate
   management inside the cluster. Later labs (especially KServe for inference
   serving) require it as a dependency.

The full setup takes 2–5 minutes depending on your internet speed and whether
Docker has cached the images from a previous run.

### Step 3: Verify the cluster

Run the verification script:

```bash
./verify.sh
```

This checks that:

- The kind cluster is running and `kubectl` can reach it
- All three nodes are in `Ready` state
- The worker nodes have the expected GPU and zone labels
- Cert-manager pods are running in the `cert-manager` namespace

## Verify it worked

You can also verify manually. Run:

```bash
kubectl get nodes --show-labels
```

You should see output similar to:

```
NAME                        STATUS   ROLES           AGE   VERSION
ai-workshop-control-plane   Ready    control-plane   2m    v1.33.x
ai-workshop-worker          Ready    <none>          2m    v1.33.x
ai-workshop-worker2         Ready    <none>          2m    v1.33.x
```

The two worker nodes should have labels including:

- `node.kubernetes.io/gpu-type=simulated`
- `topology.kubernetes.io/zone=zone-a` (worker) or `zone-b` (worker2)

## What just happened?

You now have a local Kubernetes cluster with:

- **3 nodes** — one control plane for cluster management, two workers for
  running workloads
- **Simulated GPU topology** — worker nodes labeled as if they have GPUs, in
  two separate availability zones
- **cert-manager** — TLS certificate automation ready for KServe and other
  components
- **NodePort access** — ports 30000–30002 mapped from your host into the
  cluster for accessing services

This cluster is the foundation for every lab that follows. Each subsequent lab
installs its own components (Kueue, DRA, JobSet, KServe, etc.) on top of this
base environment.

## Clean up

When you are finished with all the labs, or if you need to start fresh:

```bash
./teardown.sh
```

This deletes the kind cluster and all resources inside it. You can re-run
`setup.sh` at any time to recreate it.

## Next step

Proceed to [Lab 01: Kueue Basics](../01-kueue-basics/README.md) to learn how
Kubernetes queues and prioritizes AI workloads.
