# Kueue

## What is it?
Kueue is a Kubernetes-native job queueing system that controls when and where GPU workloads are admitted to a cluster. Think of it as a traffic controller for GPU jobs — it decides which jobs run now, which wait, and how resources are fairly shared across teams. It does not replace the kube-scheduler; it sits in front of it, gating admission based on quotas, priorities, and available capacity.

## What problem does it solve?
Without Kueue, submitting GPU jobs to a shared cluster is a free-for-all. Teams over-request resources, lower-priority jobs block higher-priority ones, and nobody gets fair access. Cluster admins end up building ad-hoc scripts to manage quotas, or they over-provision hardware to avoid conflicts. Kueue provides admission control, fair sharing, preemption, and topology-aware scheduling out of the box — the same kind of workload management that HPC batch schedulers like Slurm have provided for decades, but built for Kubernetes.

## Where does it fit in the stack?
Kueue manages the queue and admission decisions for GPU workloads, sitting above DRA (which handles the actual hardware allocation) and working alongside JobSet (which defines multi-pod training jobs).

## Current status
- **CNCF status:** Incubating
- **Latest version:** v0.17.0
- **Key CRDs:** ClusterQueue, LocalQueue, ResourceFlavor, Workload

## Get started
- Official docs: [https://kueue.sigs.k8s.io](https://kueue.sigs.k8s.io)
- GitHub: [https://github.com/kubernetes-sigs/kueue](https://github.com/kubernetes-sigs/kueue)
- Related lab: [labs/01-kueue-basics](../../labs/01-kueue-basics)

## Last verified
March 2026 — all facts checked against official sources.
