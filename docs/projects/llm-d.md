# llm-d

## What is it?
llm-d is a Kubernetes-native framework for running large language model (LLM) inference at scale across distributed GPU clusters. Launched by Red Hat, with founding contributions from CoreWeave, Google Cloud, IBM Research, and NVIDIA, it treats LLM serving the way Kubernetes treats container orchestration — as a scheduling and routing problem that benefits from declarative, infrastructure-aware automation. Partners including AMD, Cisco, Hugging Face, Intel, Lambda, and Mistral AI contribute to the broader ecosystem.

## What problem does it solve?
Before llm-d, serving LLMs on Kubernetes meant either over-provisioning expensive GPUs to handle peak load or accepting high latency during traffic spikes. There was no standard way to reuse the KV cache (the per-request memory that stores what the model has already "read") across requests, so every new prompt started cold. llm-d fixes this with KV cache offloading, cache-aware LoRA routing (sending requests for the same fine-tuned adapter to GPUs that already have it loaded), and scale-to-zero so idle models release GPU resources entirely. Benchmarks show roughly 3,100 tokens per second per NVIDIA B200 decode GPU.

## Where does it fit in the stack?
llm-d sits behind KServe (v0.17.0 integrates directly with it) as the inference engine, while the Gateway API Inference Extension handles model-aware traffic routing in front.

## Current status
- **CNCF status:** Not a CNCF project
- **Latest version:** v0.5 (February 2026)
- **Key CRDs:** None — llm-d plugs into existing KServe CRDs (InferenceService, ServingRuntime)

## Get started
- Official docs: See the project README and architecture guide in the GitHub repo
- GitHub: [github.com/llm-d/llm-d](https://github.com/llm-d/llm-d)
- Related lab: [labs/04-kserve-inference](../../labs/04-kserve-inference/) — covers KServe integration with llm-d

## Last verified
March 2026 — all facts checked against official sources.
