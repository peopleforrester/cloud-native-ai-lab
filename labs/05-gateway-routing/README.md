# Lab 05: Gateway API Inference Routing

## What you'll learn

- What the Gateway API Inference Extension adds to standard Kubernetes networking
- The InferencePool and InferenceObjective CRDs and what each field means
- How model-aware routing differs from traditional load balancing
- How intelligent traffic management works for inference workloads

## Prerequisites

- Lab 04 completed (familiarity with KServe and InferenceService concepts)
- Lab 00 completed (kind cluster running)

## Background

A regular Kubernetes load balancer treats every request the same — it picks a
backend pod using round-robin, least-connections, or random selection. It has no
idea what model is running on each pod, how much GPU memory is available, or
whether a pod already has the requested model loaded in memory. For inference
workloads, this is wasteful. A request for `llama-3-70b` might land on a pod
that has `mistral-7b` loaded, forcing an expensive model swap.

The **Gateway API Inference Extension** solves this by making the gateway
model-aware. It extends the standard Kubernetes Gateway API (the successor to
Ingress) with two new CRDs: **InferencePool** and **InferenceObjective**. These
tell the gateway which models are available, where they run, and how to route
requests intelligently.

An **InferencePool** represents a group of pods serving one or more models. Think
of it as a specialized BackendRef — instead of pointing at a generic Service, it
describes a pool of inference servers (like vLLM or Triton) along with their
capabilities. The pool's selector picks pods by label, and the extension's
endpoint picker considers factors like model affinity, queue depth, and KV-cache
utilization when choosing which pod handles each request.

An **InferenceObjective** (renamed from InferenceModel at GA) defines what a
consumer wants: a model name, a target latency, and a criticality level. It maps
a user-facing model name to one or more backend models in a pool. This lets you
do things like route `our-coding-model` to different backing models based on
criticality — critical requests go to a dedicated pool while best-effort requests
share a spot pool. The gateway reads the model name from the request body
(OpenAI-compatible format) and routes accordingly.

> **Honest note about this lab:** Fully demonstrating model-aware routing
> requires running real inference backends with GPU resources. On a kind cluster
> without GPUs, we cannot run actual model servers that respond to routed
> requests. This lab is structured as a **conceptual walkthrough with annotated
> manifests** — you will understand what each resource does and how they connect,
> and you can apply these manifests on a GPU-enabled cluster (see the optional
> cloud GPU labs) for a live demonstration.

## Exercise

### Step 1: Understand what Gateway API Inference Extension does

The Gateway API Inference Extension sits between clients and inference servers:

```
Client Request (with model name in body)
         │
         ▼
┌─────────────────────┐
│   Gateway (Envoy)   │  ← reads model name from request body
│   + Inference Ext   │  ← looks up InferenceObjective for that model
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   InferencePool     │  ← selects best pod based on model affinity,
│   (pod selector)    │     queue depth, KV-cache utilization
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Inference Server   │  ← vLLM, Triton, or other serving runtime
│  (model loaded)     │
└─────────────────────┘
```

Without this extension, the gateway would round-robin across all pods — even pods
that do not have the requested model loaded. With it, routing is intelligent.

### Step 2: Create the namespace and Gateway

Open `manifests/gateway.yaml`. This manifest creates the `inference-demo`
namespace, a standard Gateway API Gateway, and an HTTPRoute that references the
InferencePool as a backend. The inference extension hooks into the gateway's
request processing pipeline.

Apply it first — the namespace must exist before we can create pool and
objective resources:

```bash
kubectl apply -f manifests/gateway.yaml
```

### Step 3: Examine the InferencePool manifest

Open `manifests/inference-pool.yaml` and read the comments. The key fields are:

- **selector**: Which pods belong to this pool (label-based, like a Service)
- **targetPortNumber**: The port where the inference server listens
- **extensionRef**: Points to the endpoint-picker service that makes intelligent
  routing decisions

Apply the manifest to see the CRD in action (the resource will be created but
will not route traffic without real backends):

```bash
kubectl apply -f manifests/inference-pool.yaml
```

Inspect the resource:

```bash
kubectl get inferencepool -n inference-demo
kubectl describe inferencepool llm-pool -n inference-demo
```

### Step 4: Examine the InferenceObjective manifest

> **Important:** This CRD was renamed from `InferenceModel` to
> `InferenceObjective` at GA. If you see older tutorials or blog posts
> referencing `InferenceModel`, they are using the pre-GA name.

Open `manifests/inference-objective.yaml` and read the comments. The key fields
are:

- **modelName**: The user-facing model name that clients use in API requests
- **targetModels**: The actual backend model(s) that serve this objective
- **criticality**: Controls routing priority (Critical vs BestEffort)
- **poolRef**: Which InferencePool handles this objective

Apply the manifest:

```bash
kubectl apply -f manifests/inference-objective.yaml
```

Inspect the resource:

```bash
kubectl get inferenceobjective -n inference-demo
kubectl describe inferenceobjective coding-model -n inference-demo
```

### Step 5: Understand routing decisions

When a client sends a request like:

```json
{
  "model": "our-coding-model",
  "messages": [{"role": "user", "content": "Write a hello world in Python"}]
}
```

The routing flow is:

1. **Gateway receives the request** and the inference extension reads the `model`
   field from the JSON body.

2. **InferenceObjective lookup** — The extension finds the InferenceObjective
   named `coding-model` whose `modelName` matches `our-coding-model`.

3. **Pool selection** — The objective's `poolRef` points to `llm-pool`, so the
   request is scoped to pods in that pool.

4. **Intelligent pod selection** — The endpoint picker evaluates each pod in the
   pool based on:
   - **Model affinity**: Does this pod already have the target model loaded?
   - **Queue depth**: How many pending requests does this pod have?
   - **KV-cache utilization**: How full is the pod's KV-cache (for LLMs)?

5. **Request forwarded** to the best pod.

In a production setup with mixed models and criticality levels, this prevents
request starvation and reduces unnecessary model swaps.

**What this looks like on a real cluster:**

On a GPU-enabled cluster with vLLM pods running, you would see:
- Requests routed to pods that already have the model loaded (avoiding cold starts)
- Critical requests prioritized over best-effort requests
- Even distribution based on actual server load, not just connection count

See the optional cloud GPU labs for instructions on setting up a cluster where
you can test this end-to-end.

## Verify it worked

Even without real backends, you can verify the CRDs were created correctly:

```bash
# All three resource types should exist
kubectl get inferencepool -n inference-demo
kubectl get inferenceobjective -n inference-demo
kubectl get gateway -n inference-demo

# Check for any error conditions
kubectl get events -n inference-demo --sort-by='.lastTimestamp'
```

## What just happened?

You created the three resources that make up the Gateway API Inference Extension:

1. **Gateway** — The entry point for inference traffic, extended with
   model-aware routing logic.

2. **InferencePool** — A group of inference server pods with an intelligent
   endpoint picker that considers model affinity and server load.

3. **InferenceObjective** — A mapping from user-facing model names to backend
   models, with criticality-based prioritization.

Together, these resources enable routing decisions that are impossible with
standard Kubernetes networking. Instead of blindly load-balancing across pods,
the gateway understands what each pod is serving and routes accordingly.

This is particularly valuable for LLM serving where model loading takes minutes
and GPU memory is expensive — you want to avoid unnecessary model swaps and
ensure critical traffic always gets served.

## Clean up

```bash
kubectl delete -f manifests/gateway.yaml
kubectl delete -f manifests/inference-objective.yaml
kubectl delete -f manifests/inference-pool.yaml
kubectl delete namespace inference-demo
```

## Next step

Continue to [Lab 06: kagent and MCP](../06-kagent-mcp/).
