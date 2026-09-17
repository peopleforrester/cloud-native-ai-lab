# Gateway API Inference Extension

## What is it?
The Gateway API Inference Extension adds model-aware routing to the Kubernetes Gateway API. If you already know how HTTPRoute directs HTTP traffic to backend Services, think of InferencePool as a BackendRef that understands which AI model a request targets and can make smarter load-balancing decisions based on GPU-level signals like KV cache utilization and LoRA adapter locality. The project reached GA status. This is production-ready.

## What problem does it solve?
Standard Kubernetes load balancing (round-robin, least-connections) is blind to what matters for inference: which GPU already has the model weights loaded, which node has a warm KV cache for a follow-up request, and which LoRA adapter a request needs. Without this awareness, requests bounce to cold GPUs, wasting time reloading weights. The Inference Extension solves this by routing at the model level, not just the endpoint level. GKE reports a 30% cost reduction and 60% lower tail latency when using model-aware routing compared to naive balancing.

## Where does it fit in the stack?
It sits at the ingress layer, in front of inference backends like KServe and llm-d, making routing decisions before requests reach the serving infrastructure.

## Current status
- **CNCF status:** Not a standalone CNCF project, developed under the Kubernetes Gateway API SIG
- **Latest version:** v1.6.1 (InferencePool API is v1, GA)
- **Key CRDs:** InferencePool (`inference.networking.k8s.io/v1`, GA) and InferencePoolImport (`inference.networking.x-k8s.io/v1alpha1`, new in v1.6.0).
- **Moved out:** `InferenceObjective` replaced `InferenceModel` in v1.0.0 but was never promoted to the GA group. v1.6.0 removed it, along with `InferenceModelRewrite` and `EndpointPickerConfig`, and it now ships from llm-d-router as `llm-d.ai/v1alpha2`.

## Get started
- Official docs: [gateway-api-inference-extension.sigs.k8s.io](https://gateway-api-inference-extension.sigs.k8s.io)
- GitHub: [github.com/kubernetes-sigs/gateway-api-inference-extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
- Compatible with: Envoy Gateway, kgateway, GKE Gateway, Istio
- Related lab: [labs/05-gateway-routing](../../labs/05-gateway-routing/)

## Last verified
July 2026. All facts checked against official sources.
