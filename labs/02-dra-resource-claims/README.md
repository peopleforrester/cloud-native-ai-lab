# Lab 02: DRA Resource Claims

## What you'll learn

- How Dynamic Resource Allocation (DRA) replaces the legacy device plugin model
- How to write ResourceClaims, ResourceClaimTemplates, and DeviceClasses
- How declarative device allocation gives pods fine-grained control over
  hardware selection
- The difference between structured parameters and opaque claim allocation

## Prerequisites

- Lab 00 completed — a running kind cluster named `ai-workshop`
- `kubectl` configured to talk to the `ai-workshop` cluster

## Background

Kubernetes has supported GPUs and other hardware accelerators through **device
plugins** since version 1.8. Device plugins work, but they have a fundamental
limitation: they treat devices as opaque integers. When a pod requests
`nvidia.com/gpu: 1`, the kubelet hands it one GPU — any GPU. The pod cannot
express preferences like "give me a GPU with at least 40 GB of memory" or
"give me two GPUs connected by NVLink." It is like walking into a restaurant
and ordering "1 food" — you will get something, but you have no say in what.

**Dynamic Resource Allocation (DRA)** replaces this model with a declarative,
expressive system. DRA lets pods describe exactly what they need through
**ResourceClaims**, and it lets cluster administrators describe what is
available through **DeviceClasses**. Think of DeviceClasses as the menu, and
ResourceClaims as your order. You can specify device attributes (memory size,
architecture, compute capability), and the DRA controller matches your request
against the available inventory.

DRA reached beta status in Kubernetes 1.32 with the "structured parameters"
model. In this model, device attributes are published as structured data that
the scheduler can evaluate directly — no external controller needed for basic
matching. This is a significant improvement over the earlier "classic DRA"
model where an external controller had to handle every allocation request.

**An honest note about this lab:** DRA requires a resource driver that
publishes device information to the cluster. On a kind cluster without real
GPUs, you would need to install the `dra-example-driver` from the Kubernetes
repository. This driver simulates devices but requires building from source and
can be fragile across Kubernetes versions. This lab is structured in two parts:
Part A walks through annotated manifests so you understand the DRA resource
model conceptually, and Part B provides optional instructions for installing
the example driver if you want a hands-on experience.

## Exercise

### Part A: Conceptual walkthrough with annotated manifests

DRA uses four main resource types. Read through each manifest to understand the
resource model before attempting to apply them.

#### Step 1: Understand DeviceClass

Review the DeviceClass manifest:

```bash
cat manifests/device-class.yaml
```

A DeviceClass defines a category of devices that exist in the cluster. It
specifies selectors that match against device attributes published by a
resource driver. In a real cluster, the GPU driver would publish attributes
like `memory`, `architecture`, and `computeCapability` for each physical GPU.

#### Step 2: Understand ResourceClaim

Review the ResourceClaim manifest:

```bash
cat manifests/resource-claim.yaml
```

A ResourceClaim is how a pod requests a specific device. It references a
DeviceClass and can add additional constraints. Think of it as the pod's
"order" from the device "menu."

#### Step 3: Understand ResourceClaimTemplate

Review the ResourceClaimTemplate manifest:

```bash
cat manifests/resource-claim-template.yaml
```

A ResourceClaimTemplate creates a fresh ResourceClaim for each pod. This is
useful with Deployments or Jobs where each replica needs its own dedicated
device. Without templates, multiple pods would fight over the same claim.

#### Step 4: Understand the Pod spec

Review the pod manifest:

```bash
cat manifests/pod-with-claim.yaml
```

The pod references its ResourceClaim by name. The kubelet ensures the claimed
device is available to the container before starting it. In a real GPU
scenario, this would mean the GPU is allocated, its device node is mounted
into the container, and the appropriate driver libraries are available.

### Part B: Optional — hands-on with the DRA example driver

> **Warning:** The DRA example driver requires cloning the Kubernetes
> repository and building the driver image. This can take significant time and
> disk space. Only proceed if you want the hands-on experience.

#### Step 1: Clone and build the example driver

```bash
git clone --depth 1 https://github.com/kubernetes/kubernetes.git
cd kubernetes/test/e2e/dra/test-driver
# Build the driver image — this requires Go 1.22+ installed
make build
# Load the image into your kind cluster
kind load docker-image registry.k8s.io/dra-example-driver:latest \
  --name ai-workshop
```

#### Step 2: Deploy the driver

```bash
# The driver deployment manifests are in the Kubernetes repo
kubectl apply -f deploy/
```

#### Step 3: Apply the lab manifests

Once the driver is running and has published device resources:

```bash
kubectl apply -f manifests/device-class.yaml
kubectl apply -f manifests/resource-claim.yaml
kubectl apply -f manifests/pod-with-claim.yaml
```

#### Step 4: Observe allocation

```bash
kubectl get resourceclaim gpu-claim -o yaml
kubectl get pod gpu-consumer -o wide
```

The ResourceClaim status will show which device was allocated. The pod will
be scheduled to the node that has that device.

## Verify it worked

**For Part A (conceptual):** You have reviewed and understand the four DRA
resource types. You can explain the relationship between DeviceClass,
ResourceClaim, ResourceClaimTemplate, and Pod.

**For Part B (hands-on):** If you installed the example driver:

```bash
# The driver pods are running
kubectl get pods -l app=dra-example-driver

# The ResourceClaim has been allocated
kubectl get resourceclaim gpu-claim -o jsonpath='{.status.allocation}'

# The pod is running with the claimed device
kubectl get pod gpu-consumer
```

## What just happened?

You explored Kubernetes Dynamic Resource Allocation, the system replacing
legacy device plugins for managing hardware accelerators:

- **DeviceClass** — defines a category of devices (e.g., "simulated GPU")
  with attribute-based selectors
- **ResourceClaim** — a pod's request for a specific device, supporting
  attribute constraints like memory size or architecture
- **ResourceClaimTemplate** — generates per-pod claims for multi-replica
  workloads like Deployments and Jobs
- **Pod integration** — pods reference claims in their spec, and the kubelet
  ensures devices are allocated before container startup

DRA's structured parameters model lets the Kubernetes scheduler evaluate
device requests directly, without calling out to external controllers for
basic matching. This improves scheduling performance and reduces operational
complexity compared to the older opaque-parameter approach.

## Clean up

Remove any resources you created:

```bash
kubectl delete pod gpu-consumer --ignore-not-found
kubectl delete resourceclaim gpu-claim --ignore-not-found
kubectl delete resourceclaimtemplate gpu-claim-template --ignore-not-found
kubectl delete deviceclass simulated-gpu --ignore-not-found
```

If you installed the DRA example driver:

```bash
kubectl delete -f deploy/   # from the Kubernetes repo test-driver directory
```

## Next step

Proceed to [Lab 03: JobSet Training](../03-jobset-training/README.md) to learn
how JobSet coordinates multi-pod distributed training workloads on Kubernetes.
