# Lab 01: Kueue Basics

## What you'll learn

- How Kueue provides fair sharing, admission control, and preemption for
  Kubernetes workloads
- How to create ResourceFlavors, ClusterQueues, and LocalQueues
- How priority-based preemption works when queues are full
- Why Kueue matters for managing expensive GPU-like workloads at scale

## Prerequisites

- Lab 00 completed — a running kind cluster named `ai-workshop`
- `helm` installed and available on your PATH
- `kubectl` configured to talk to the `ai-workshop` cluster

## Background

Kubernetes has a built-in scheduler that decides which node runs each pod, but
it has no concept of "waiting in line." If you submit 500 GPU training jobs and
your cluster only has capacity for 10, the scheduler will start binding pods
immediately. The ones that fit will run; the rest will sit in `Pending` state
with no ordering, no fairness, and no visibility into when they might run. In a
shared cluster, this creates chaos — one team can monopolize all the GPUs while
others wait indefinitely.

**Kueue** is a Kubernetes-native job queueing system that solves this problem.
Think of it this way: if the Kubernetes scheduler is a highway, Kueue adds toll
booths and HOV lanes. It intercepts jobs before they reach the scheduler,
checks them against quota policies, and only admits jobs when there is actual
capacity available. Jobs that cannot run yet wait in a queue with well-defined
ordering rather than flooding the scheduler with un-schedulable pods.

Fair sharing is one of Kueue's core features. You define quotas per team or
project — say, team-a gets 4 CPUs and team-b gets 2 CPUs. Kueue enforces
these limits at admission time, not at scheduling time. This means team-a
cannot accidentally (or intentionally) consume team-b's allocation. Each team
gets a guaranteed share of the cluster, and Kueue tracks usage in real time
to make admission decisions.

Preemption adds another layer. When a high-priority job arrives and the queue
is full, Kueue can evict lower-priority jobs to make room. This is critical
in production AI/ML workflows — a time-sensitive inference model retrain
should not wait behind a batch of exploratory notebooks. Kueue handles the
eviction and re-queuing automatically, so the lower-priority jobs resume once
capacity frees up.

**No GPU required.** All exercises in this lab use CPU and memory quotas to
demonstrate Kueue's behavior. The concepts apply identically to GPU resources —
when you move to a cluster with real GPUs, you simply add GPU resource types to
your ClusterQueue definitions.

## Exercise

### Step 1: Install Kueue

Install Kueue into the cluster using the official OCI Helm chart:

```bash
helm install kueue oci://registry.k8s.io/kueue/charts/kueue \
  --version 0.16.4 \
  -n kueue-system \
  --create-namespace \
  --wait --timeout 5m
```

Wait for the Kueue controller to become ready:

```bash
kubectl -n kueue-system wait --for=condition=Available \
  deployment/kueue-controller-manager --timeout=120s
```

### Step 2: Create a ResourceFlavor

A ResourceFlavor describes a type of resource available in the cluster. In
production, you might have flavors like `a100-gpu` or `spot-cpu`. Here we
create a simple default CPU flavor:

```bash
kubectl apply -f manifests/resource-flavor.yaml
```

### Step 3: Create ClusterQueues for two teams

ClusterQueues define the resource budgets. Team-a gets more capacity than
team-b to demonstrate fair sharing:

```bash
kubectl apply -f manifests/cluster-queue-a.yaml
kubectl apply -f manifests/cluster-queue-b.yaml
```

Inspect the queues:

```bash
kubectl get clusterqueues
```

You should see both queues with their configured resource limits.

### Step 4: Create namespaces and LocalQueues

LocalQueues live in a namespace and point to a ClusterQueue. Users submit jobs
to LocalQueues — they never interact with ClusterQueues directly:

```bash
kubectl create namespace team-a-ns
kubectl create namespace team-b-ns
kubectl apply -f manifests/local-queue-a.yaml
kubectl apply -f manifests/local-queue-b.yaml
```

### Step 5: Submit jobs and observe fair sharing

Submit a job to team-a's queue:

```bash
kubectl apply -f manifests/sample-job.yaml -n team-a-ns
```

Watch the job get admitted:

```bash
kubectl -n team-a-ns get jobs -w
```

Check the ClusterQueue usage — Kueue tracks admitted workloads:

```bash
kubectl get clusterqueue team-a-cq -o yaml | grep -A 10 "flavorsUsage"
```

Submit a job to team-b's queue to see both teams running concurrently:

```bash
kubectl create -f manifests/sample-job-b.yaml -n team-b-ns
```

### Step 6: Submit a high-priority job to demonstrate preemption

First, create the PriorityClasses, then submit a high-priority job:

```bash
kubectl apply -f manifests/priority-classes.yaml
kubectl create -f manifests/priority-job.yaml -n team-a-ns
```

Watch the workloads to see preemption in action:

```bash
kubectl -n team-a-ns get workloads -w
```

Kueue will evict the lower-priority workload to make room for the
high-priority one. The evicted job returns to the queue and resumes when
capacity becomes available.

## Verify it worked

Run the following commands to confirm everything is set up correctly:

```bash
# Kueue controller is running
kubectl -n kueue-system get pods

# Both ClusterQueues exist and are active
kubectl get clusterqueues

# Both LocalQueues exist in their namespaces
kubectl get localqueues -A

# Jobs were admitted and ran
kubectl get jobs -n team-a-ns
kubectl get jobs -n team-b-ns
```

You should see:

- Kueue controller pods in `Running` state
- Two ClusterQueues (`team-a-cq` and `team-b-cq`)
- Two LocalQueues (`team-a-lq` and `team-b-lq`) in their respective namespaces
- Completed or running jobs in both namespaces

## What just happened?

You deployed a complete Kueue job queueing system with:

- **ResourceFlavor** — a named type of compute resource (default CPU)
- **ClusterQueues** — cluster-wide resource budgets with different quotas for
  two teams (team-a: 4 CPU / 8Gi, team-b: 2 CPU / 4Gi)
- **LocalQueues** — namespace-scoped entry points where users submit jobs
- **Fair sharing** — each team gets its guaranteed allocation without
  interfering with the other
- **Preemption** — high-priority jobs can evict lower-priority ones when
  resources are scarce

In a real cluster with GPUs, you would add `nvidia.com/gpu` to the
ClusterQueue resource groups and create ResourceFlavors for different GPU
types. The queueing and preemption mechanics work exactly the same way.

## Clean up

Remove all lab resources:

```bash
kubectl delete namespace team-a-ns team-b-ns
helm uninstall kueue -n kueue-system
kubectl delete namespace kueue-system
kubectl delete resourceflavor default-cpu
```

## Next step

Proceed to [Lab 02: DRA Resource Claims](../02-dra-resource-claims/README.md)
to learn how Dynamic Resource Allocation provides fine-grained device
management for GPUs and other hardware accelerators.
