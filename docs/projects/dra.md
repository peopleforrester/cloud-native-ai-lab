# Dynamic Resource Allocation (DRA)

## What is it?
Dynamic Resource Allocation is a core Kubernetes feature that lets workloads request hardware accelerators (like GPUs) using the same declarative style you already use for CPU and memory. Instead of asking for "2 GPUs" as an opaque integer, you describe what you actually need — specific capabilities, interconnects, minimum VRAM — and the scheduler finds hardware that matches. DRA is to GPUs what resource requests and limits are to CPU and memory.

## What problem does it solve?
Before DRA, Kubernetes used the device plugin model to allocate GPUs. Device plugins treat GPUs as identical, countable slots — you could ask for "2 GPUs" but you could not say "2 GPUs connected via NVLink with at least 40 GB VRAM each." If you needed topology-aware placement or attribute-based selection, you were stuck writing custom schedulers or node affinity hacks. DRA replaces that rigid model with a structured, attribute-aware allocation system where both the workload author and the cluster admin express requirements declaratively, and the scheduler handles the matching.

## Where does it fit in the stack?
DRA sits at the Kubernetes scheduler level — it is the foundation that Kueue, JobSet, and KServe build on to actually acquire GPU resources for training and inference workloads.

## Current status
- **CNCF status:** Not a standalone CNCF project — this is a core Kubernetes API feature
- **Latest version:** GA in Kubernetes 1.34 (August 2025), locked in Kubernetes 1.35 (December 2025)
- **Key CRDs:** ResourceClaim, ResourceClaimTemplate, DeviceClass
- **Cloud support:** EKS, GKE, and AKS all support DRA

## Get started
- Official docs: [https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- GitHub: [https://github.com/kubernetes/kubernetes](https://github.com/kubernetes/kubernetes) (part of core Kubernetes)
- Related lab: [labs/02-dra-resource-claims](../../labs/02-dra-resource-claims)

## Last verified
March 2026 — all facts checked against official sources.
