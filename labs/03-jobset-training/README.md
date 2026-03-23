# Lab 03: JobSet Training

## What you'll learn

- How JobSet coordinates multi-pod distributed training workloads
- How failure handling works when individual pods die during training
- How to integrate JobSet with Kueue for admission-controlled training jobs
- Why coordinated startup and gang scheduling matter for distributed workloads

## Prerequisites

- Lab 00 completed — a running kind cluster named `ai-workshop`
- Lab 01 completed — Kueue installed and configured (for Step 5)
- `kubectl` configured to talk to the `ai-workshop` cluster

## Background

Distributed machine learning training runs across multiple pods simultaneously.
A typical training job has a coordinator (sometimes called the driver or rank-0
worker) and several worker replicas. All pods must start together — if the
coordinator starts but two workers are stuck in `Pending`, the training process
hangs because it cannot begin until every participant has joined.

**JobSet** is a Kubernetes controller that solves this coordination problem.
Think of it as a Deployment's more disciplined cousin: while a Deployment is
happy as long as some pods are running, a JobSet insists that all pods start
together and treats the group as an atomic unit. If you have ever seen a
distributed training job hang because one pod could not be scheduled, JobSet
is the answer.

A JobSet contains one or more **ReplicatedJobs** — groups of identical pods
that serve a specific role. For example, you might have one ReplicatedJob for
the coordinator (1 replica) and another for workers (4 replicas). JobSet
ensures all replicas across all ReplicatedJobs start before any of them begin
doing real work. Each pod gets a stable hostname and can discover its peers
through a headless service that JobSet creates automatically.

Failure handling is where JobSet earns its keep. When a pod in a distributed
training job crashes, you usually want to restart the entire group — not just
the failed pod. A partially-running training job wastes resources because the
surviving pods are idle, waiting for a peer that will never rejoin. JobSet
lets you configure failure policies: restart the entire group, retry up to N
times, or fail permanently. This is fundamentally different from a regular Job,
which only manages individual pod retries.

JobSet also integrates with Kueue for admission control. By setting
`suspend: true` and adding Kueue queue labels, you can ensure that training
jobs only start when the cluster has enough capacity for all pods at once. This
prevents the common problem of partial scheduling, where half the pods start
and consume resources while the other half wait — wasting the resources held by
the running pods.

## Exercise

### Step 1: Install the JobSet controller

Install JobSet v0.11.1 using the official release manifests:

```bash
kubectl apply --server-side -f \
  https://github.com/kubernetes-sigs/jobset/releases/download/v0.11.1/manifests.yaml
```

Wait for the controller to be ready:

```bash
kubectl -n jobset-system wait --for=condition=Available \
  deployment/jobset-controller-manager --timeout=120s
```

### Step 2: Create a simple JobSet

Deploy a JobSet with two ReplicatedJobs simulating a distributed training
setup:

```bash
kubectl apply -f manifests/jobset-simple.yaml
```

This creates a JobSet with a `workers` ReplicatedJob containing 2 replicas.
Each worker runs a busybox container that simulates training work.

### Step 3: Observe coordinated startup

Watch all pods start together:

```bash
kubectl get pods -l jobset.sigs.k8s.io/jobset-name=training-sim -w
```

All pods should transition to `Running` at approximately the same time. JobSet
coordinates this by creating all child Jobs simultaneously.

Check the JobSet status:

```bash
kubectl get jobset training-sim -o yaml | grep -A 20 "status:"
```

List the child Jobs that JobSet created:

```bash
kubectl get jobs -l jobset.sigs.k8s.io/jobset-name=training-sim
```

### Step 4: Kill a pod and observe JobSet's response

Find one of the running pods and delete it:

```bash
POD=$(kubectl get pods -l jobset.sigs.k8s.io/jobset-name=training-sim \
  -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD"
```

Watch what happens:

```bash
kubectl get pods -l jobset.sigs.k8s.io/jobset-name=training-sim -w
```

The JobSet controller detects the failure and restarts the entire group. This
is the correct behavior for distributed training — a partial group is useless,
so JobSet tears down the survivors and recreates everything together.

Check the JobSet events:

```bash
kubectl describe jobset training-sim | tail -20
```

### Step 5: Create a JobSet with Kueue integration

This step requires Kueue to be installed. If you skipped Lab 01 or ran its
cleanup section, re-run Lab 01 Step 1 to reinstall Kueue before continuing.

Deploy a JobSet that uses Kueue for admission control:

```bash
kubectl apply -f manifests/jobset-with-kueue.yaml -n team-a-ns
```

The JobSet starts in a suspended state. Kueue evaluates whether team-a's queue
has enough capacity for all pods, and only admits the JobSet when resources are
available:

```bash
# Watch Kueue admit the workload
kubectl -n team-a-ns get workloads -w

# Once admitted, watch the pods start
kubectl -n team-a-ns get pods -w
```

This integration prevents partial scheduling — Kueue will not admit the JobSet
unless the cluster can run all pods simultaneously.

## Verify it worked

```bash
# JobSet controller is running
kubectl -n jobset-system get pods

# The simple JobSet completed or is running
kubectl get jobset training-sim

# Child jobs were created
kubectl get jobs -l jobset.sigs.k8s.io/jobset-name=training-sim

# If Kueue integration was tested, the workload was admitted
kubectl -n team-a-ns get workloads 2>/dev/null
```

You should see:

- JobSet controller pods in `Running` state
- The `training-sim` JobSet with a status of `Complete` or `Running`
- Two child Jobs (one per worker replica)
- If Kueue was used, a workload object showing admission status

## What just happened?

You deployed and tested JobSet, the Kubernetes controller for coordinated
multi-pod workloads:

- **Coordinated startup** — all pods in the JobSet start together as an atomic
  unit, preventing partial scheduling that wastes resources
- **Automatic peer discovery** — JobSet creates a headless service so pods can
  find each other by hostname, essential for distributed training frameworks
- **Failure handling** — when one pod dies, JobSet restarts the entire group
  rather than leaving surviving pods idle
- **Kueue integration** — by submitting JobSets in suspended state with queue
  labels, Kueue ensures the cluster has full capacity before admitting the
  training job

In production, the busybox containers would be replaced with real training
frameworks like PyTorch DistributedDataParallel or TensorFlow MultiWorkerMirrored.
The JobSet mechanics — coordinated startup, failure restart, and Kueue
admission — work identically regardless of what the containers run.

## Clean up

Remove all lab resources:

```bash
kubectl delete jobset training-sim --ignore-not-found
kubectl delete jobset training-with-kueue -n team-a-ns --ignore-not-found

# Remove the JobSet controller
kubectl delete -f \
  https://github.com/kubernetes-sigs/jobset/releases/download/v0.11.1/manifests.yaml
```

## Next step

Proceed to [Lab 04: KServe Inference](../04-kserve-inference/README.md) to
learn how to serve ML models on Kubernetes with autoscaling and canary
rollouts.
