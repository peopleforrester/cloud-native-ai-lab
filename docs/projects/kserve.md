# KServe

## What is it?
KServe is a model serving platform for Kubernetes. You give it a trained model and a container runtime, and it serves that model behind a prediction API with autoscaling, canary rollouts, and optional scale-to-zero. It handles the operational complexity of running inference in production — versioning, traffic splitting, GPU allocation, and request batching — so you can focus on the model itself. Its new LLMInferenceService CRD adds first-class support for disaggregated LLM serving through the llm-d project, separating prefill and decode phases for better GPU utilization.

## What problem does it solve?
Deploying a model to production on Kubernetes without KServe means stitching together Deployments, Services, HPAs, Ingress rules, and custom health checks — then doing it all again for canary rollouts and A/B testing. KServe wraps all of that into a single InferenceService resource. You declare the model location and the framework, and KServe handles the rest: pulling the model, configuring the serving runtime, wiring up the API endpoint, and autoscaling based on request load. It is to model serving what Ingress is to HTTP routing — a standard interface that multiple backends can implement.

## Where does it fit in the stack?
KServe sits at the top of the inference stack. It uses Knative for scale-to-zero and serverless capabilities, DRA for GPU allocation, and can work alongside LeaderWorkerSet for multi-host model sharding.

## Current status
- **CNCF status:** Incubating (accepted September 29, 2025)
- **Latest version:** v0.17.0 (released March 13, 2026)
- **Key CRDs:** InferenceService, LLMInferenceService
- **Adoption:** 5,990 GitHub stars; used by Bloomberg, Red Hat, NVIDIA, SAP

## Get started
- Official docs: [https://kserve.github.io/kserve](https://kserve.github.io/kserve)
- GitHub: [https://github.com/kserve/kserve](https://github.com/kserve/kserve)
- Related lab: [labs/04-kserve-inference](../../labs/04-kserve-inference)

## Last verified
March 2026 — all facts checked against official sources.
