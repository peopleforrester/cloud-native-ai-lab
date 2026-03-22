# Gateway API Inference Extension

## What is it?
The Gateway API Inference Extension adds model-aware routing to the Kubernetes Gateway API. If you already know how HTTPRoute directs HTTP traffic to backend Services, think of InferenceObjective as an HTTPRoute that understands which AI model a request targets and can make smarter load-balancing decisions based on GPU-level signals like KV cache utilization and LoRA adapter locality. The project reached GA status — this is production-ready.

## What problem does it solve?
Standard Kubernetes load balancing (round-robin, least-connections) is blind to what matters for inference: which GPU already has the model weights loaded, which node has a warm KV cache for a follow-up request, and which LoRA adapter a request needs. Without this awareness, requests bounce to cold GPUs, wasting time reloading weights. The Inference Extension solves this by routing at the model level, not just the endpoint level. GKE reports a 30% cost reduction and 60% lower tail latency when using model-aware routing compared to naive balancing.

## Where does it fit in the stack?
It sits at the ingress layer, in front of inference backends like KServe and llm-d, making routing decisions before requests reach the serving infrastructure.

## Current status
- **CNCF status:** Not a standalone CNCF project — developed under the Kubernetes Gateway API SIG
- **Latest version:** GA (v1)
- **Key CRDs:** InferenceObjective (renamed from InferenceModel at GA), InferencePool

## Get started
- Official docs: [gateway-api-inference-extension.sigs.k8s.io](https://gateway-api-inference-extension.sigs.k8s.io)
- GitHub: [github.com/kubernetes-sigs/gateway-api-inference-extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
- Compatible with: Envoy Gateway, kgateway, GKE Gateway, Istio
- Related lab: [labs/05-gateway-routing](../../labs/05-gateway-routing/)

## Last verified
March 2026 — all facts checked against official sources.
