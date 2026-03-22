# Cloud Native AI Lab

A hands-on lab for learning AI workloads on Kubernetes — from GPU scheduling to model serving to AI agents.

Created as a companion to a Cloud Native University talk at [KubeCon + CloudNativeCon Europe 2026](https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/) in Amsterdam, designed as a long-lived community resource.

## Who is this for?

Kubernetes practitioners who are new to AI/ML workloads. If you know pods, deployments, services, and namespaces, you have everything you need to start. This lab does **not** assume any machine learning knowledge.

## Learning path

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌───────────┐
│  Setup  │───▶│  Kueue   │───▶│   DRA   │───▶│  JobSet  │───▶│  KServe  │───▶│ Gateway API │───▶│ kagent +  │
│ Lab 00  │    │  Lab 01  │    │ Lab 02  │    │  Lab 03  │    │  Lab 04  │    │   Lab 05    │    │ MCP Lab06 │
└─────────┘    └──────────┘    └─────────┘    └──────────┘    └──────────┘    └─────────────┘    └───────────┘
  Cluster        GPU job         Device        Distributed      Model          Inference          AI agents
  setup          scheduling      allocation    training         serving        routing            and tools
```

## Labs

| Lab | Title | What you'll learn |
|-----|-------|-------------------|
| [00](labs/00-setup/README.md) | Environment Setup | Create a kind cluster configured for AI workload labs |
| [01](labs/01-kueue-basics/README.md) | Kueue Basics | Fair sharing, admission control, and preemption for GPU-like workloads |
| [02](labs/02-dra-resource-claims/README.md) | DRA Resource Claims | Declarative device allocation — how Kubernetes replaces the old device plugin model |
| [03](labs/03-jobset-training/README.md) | JobSet Training | Coordinated multi-pod training with failure handling |
| [04](labs/04-kserve-inference/README.md) | KServe Inference | Deploy a model, serve it behind an API, and watch it autoscale |
| [05](labs/05-gateway-routing/README.md) | Gateway API Inference Routing | Model-aware traffic routing with InferenceObjective and InferencePool |
| [06](labs/06-kagent-mcp/README.md) | kagent and MCP | Deploy AI agents on Kubernetes with the Model Context Protocol |

### Optional: real GPU clusters

These labs create cloud resources that cost real money. Use them to run Labs 01-06 with actual GPUs.

| Cloud | Lab |
|-------|-----|
| AWS EKS | [labs/optional/eks-gpu-cluster](labs/optional/eks-gpu-cluster/README.md) |
| Google GKE | [labs/optional/gke-gpu-cluster](labs/optional/gke-gpu-cluster/README.md) |
| Azure AKS | [labs/optional/aks-gpu-cluster](labs/optional/aks-gpu-cluster/README.md) |

## Reference materials

One-page summaries of every project covered in the labs:

| Project | What it does | Status |
|---------|-------------|--------|
| [DRA](docs/projects/dra.md) | Declarative GPU allocation | Core K8s (GA in 1.34) |
| [Kueue](docs/projects/kueue.md) | Job queuing and fair sharing | CNCF Incubating |
| [JobSet](docs/projects/jobset.md) | Distributed training orchestration | kubernetes-sigs (v0.11.1) |
| [LeaderWorkerSet](docs/projects/leaderworkerset.md) | Multi-host inference topology | kubernetes-sigs (v0.8.0) |
| [KServe](docs/projects/kserve.md) | Model serving platform | CNCF Incubating (v0.17.0) |
| [Knative](docs/projects/knative.md) | Scale-to-zero serverless | CNCF Graduated |
| [llm-d](docs/projects/llm-d.md) | Distributed LLM inference | Launched by Red Hat (v0.5) |
| [Gateway API Inference](docs/projects/gateway-api-inference.md) | Model-aware routing | GA (InferenceObjective + InferencePool) |
| [kagent](docs/projects/kagent.md) | Kubernetes-native AI agents | CNCF Sandbox |
| [MCP](docs/projects/mcp.md) | Model Context Protocol | AAIF / Linux Foundation |
| [AAIF](docs/projects/aaif.md) | Agentic AI Foundation | Linux Foundation |

Full reports:
- [Cloud-Native AI Landscape Report](docs/landscape-report.md) — comprehensive ecosystem overview (March 2026)
- [Talk Outline](docs/talk-outline.md) — the 15-minute KubeCon EU 2026 talk

## Prerequisites

- [kind](https://kind.sigs.k8s.io/) v0.20+
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/) 3.x
- ~8GB RAM for the kind cluster
- Docker installed and running

## Quick start

```bash
git clone https://github.com/peopleforrester/cloud-native-ai-lab.git
cd cloud-native-ai-lab
cd labs/00-setup && ./setup.sh
```

Then follow the [learning path checklist](checklist.md).

## What works on kind vs. what needs GPUs

| Feature | Works on kind? | Notes |
|---------|---------------|-------|
| Kueue fair sharing and preemption | Yes | Uses CPU/memory quotas |
| DRA resource claims | Partial | Conceptual walkthrough; optional DRA example driver |
| JobSet coordinated startup | Yes | Uses busybox to simulate training |
| KServe model serving | Yes | Small sklearn model on CPU |
| Gateway API inference routing | Partial | Annotated manifests; full demo needs GPU backends |
| kagent and MCP | Yes | CRD installation and resource creation |

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md). All work targets the `staging` branch.

## Credit

**Author:** Michael Forrester — KodeKloud. Research and content developed with [Claude](https://claude.ai) (Anthropic).

## License

This project is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.
