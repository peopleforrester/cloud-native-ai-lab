# JobSet

## What is it?
JobSet is a Kubernetes API for running groups of related Jobs as a single unit. In distributed machine learning training, a single training run often requires multiple groups of Pods — some running parameter servers, others running workers — that must start together, communicate with each other, and fail or restart as a coordinated group. JobSet manages that coordination so you do not have to.

## What problem does it solve?
Before JobSet, running a distributed training job on Kubernetes meant creating multiple separate Job objects and writing custom glue to coordinate their lifecycle. If one worker group crashed, you had to detect it yourself and decide whether to restart everything or just the failed piece. JobSet treats the entire collection of Jobs as a single atomic unit with coordinated startup, failure handling, and restart policies. It is to multi-Job workloads what a Deployment is to a set of identical Pods — a higher-level abstraction that handles the orchestration for you.

## Where does it fit in the stack?
JobSet defines the shape of a distributed training run (how many workers, how many parameter servers), while Kueue decides when that run gets admitted to the cluster and DRA allocates the GPUs it needs.

## Current status
- **CNCF status:** Not a CNCF project — maintained under kubernetes-sigs
- **Latest version:** v0.11.1
- **Key CRDs:** JobSet

## Get started
- Official docs: [https://jobset.sigs.k8s.io](https://jobset.sigs.k8s.io)
- GitHub: [https://github.com/kubernetes-sigs/jobset](https://github.com/kubernetes-sigs/jobset)
- Related lab: [labs/03-jobset-training](../../labs/03-jobset-training)

## Last verified
March 2026 — all facts checked against official sources.
