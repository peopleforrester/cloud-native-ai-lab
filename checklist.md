# Cloud Native AI Learning Path

A step-by-step progression through the labs and reference materials in this repository.

## Step 1: Set up your environment

- [ ] Install prerequisites: [kind](https://kind.sigs.k8s.io/), [kubectl](https://kubernetes.io/docs/tasks/tools/), [Helm](https://helm.sh/docs/intro/install/)
- [ ] Create the lab cluster ([Lab 00](labs/00-setup/README.md))
- [ ] Verify the cluster is running with `kubectl get nodes`

## Step 2: Learn GPU scheduling fundamentals

- [ ] Read: [docs/projects/dra.md](docs/projects/dra.md) — how Kubernetes allocates GPUs
- [ ] Read: [docs/projects/kueue.md](docs/projects/kueue.md) — how workloads get queued and scheduled
- [ ] Complete: [Lab 01 — Kueue Basics](labs/01-kueue-basics/README.md)
- [ ] Complete: [Lab 02 — DRA Resource Claims](labs/02-dra-resource-claims/README.md)
- [ ] You now understand: how Kubernetes schedules AI workloads

## Step 3: Understand distributed training

- [ ] Read: [docs/projects/jobset.md](docs/projects/jobset.md) — coordinating multi-node training jobs
- [ ] Read: [docs/projects/leaderworkerset.md](docs/projects/leaderworkerset.md) — leader-worker topology for inference
- [ ] Complete: [Lab 03 — JobSet Training](labs/03-jobset-training/README.md)
- [ ] You now understand: how distributed training jobs are orchestrated on Kubernetes

## Step 4: Deploy and serve a model

- [ ] Read: [docs/projects/kserve.md](docs/projects/kserve.md) — the model serving platform
- [ ] Read: [docs/projects/knative.md](docs/projects/knative.md) — scale-to-zero for inference
- [ ] Read: [docs/projects/llm-d.md](docs/projects/llm-d.md) — distributed LLM inference
- [ ] Complete: [Lab 04 — KServe Inference](labs/04-kserve-inference/README.md)
- [ ] You now understand: how models get deployed, served, and autoscaled on Kubernetes

## Step 5: Route inference traffic intelligently

- [ ] Read: [docs/projects/gateway-api-inference.md](docs/projects/gateway-api-inference.md) — model-aware routing
- [ ] Complete: [Lab 05 — Gateway API Inference Routing](labs/05-gateway-routing/README.md)
- [ ] You now understand: how Kubernetes routes requests to the right model backend

## Step 6: Meet AI agents and MCP

- [ ] Read: [docs/projects/kagent.md](docs/projects/kagent.md) — Kubernetes-native AI agents
- [ ] Read: [docs/projects/mcp.md](docs/projects/mcp.md) — the Model Context Protocol
- [ ] Read: [docs/projects/aaif.md](docs/projects/aaif.md) — the Agentic AI Foundation
- [ ] Complete: [Lab 06 — kagent and MCP](labs/06-kagent-mcp/README.md)
- [ ] You now understand: how AI agents connect to tools via MCP on Kubernetes

## Step 7: Go deeper

- [ ] Read the full [Landscape Report](docs/landscape-report.md) for the complete picture
- [ ] Review the [Talk Outline](docs/talk-outline.md) for a condensed narrative
- [ ] Try the optional GPU labs on a real cloud cluster:
  - [ ] [EKS GPU Cluster](labs/optional/eks-gpu-cluster/README.md)
  - [ ] [GKE GPU Cluster](labs/optional/gke-gpu-cluster/README.md)
  - [ ] [AKS GPU Cluster](labs/optional/aks-gpu-cluster/README.md)

## Step 8: Contribute

- [ ] Join the [AI Gateway Working Group](https://github.com/kubernetes-sigs/wg-ai-gateway) — announced March 9, 2026
- [ ] Contribute to one of the open-source projects covered in the labs
- [ ] File an issue or submit a PR to this repository
- [ ] Share what you learned — write a blog post, give a talk, or teach a colleague
