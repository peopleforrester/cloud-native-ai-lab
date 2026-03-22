# LeaderWorkerSet

## What is it?
LeaderWorkerSet is a Kubernetes API for managing long-running, multi-host workloads where one Pod acts as a leader and coordinates a group of worker Pods. It is designed for inference scenarios where a large language model is too big to fit on a single node and must be sharded across multiple GPUs on multiple machines. The leader Pod handles request routing while worker Pods each serve a shard of the model.

## What problem does it solve?
Deploying a model that spans multiple nodes is awkward with standard Kubernetes primitives. A Deployment treats all replicas as identical and interchangeable, but in sharded inference, each Pod holds a different piece of the model and the leader must know exactly which workers are available. StatefulSets get closer but still lack the leader-election and group-lifecycle semantics you need. LeaderWorkerSet provides a purpose-built abstraction: it maintains a stable leader, manages the worker group, and handles rolling updates and failure recovery while preserving the leader-worker topology.

## Where does it fit in the stack?
LeaderWorkerSet handles the Pod topology for multi-host inference workloads, complementing KServe (which manages the serving API, autoscaling, and traffic routing) and DRA (which allocates the GPUs each Pod needs).

## Current status
- **CNCF status:** Not a CNCF project — maintained under kubernetes-sigs
- **Latest version:** v0.8.0 (stable API, v1)
- **Key CRDs:** LeaderWorkerSet

## Get started
- Official docs: [https://github.com/kubernetes-sigs/lws/tree/main/docs](https://github.com/kubernetes-sigs/lws/tree/main/docs)
- GitHub: [https://github.com/kubernetes-sigs/lws](https://github.com/kubernetes-sigs/lws)
- Related lab: No dedicated lab — referenced in context of [labs/03-jobset-training](../../labs/03-jobset-training) and [labs/04-kserve-inference](../../labs/04-kserve-inference)

## Last verified
March 2026 — all facts checked against official sources.
