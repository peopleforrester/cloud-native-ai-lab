# Knative

## What is it?
Knative is a Kubernetes platform that adds serverless capabilities to your cluster. Its Serving component lets you deploy containers that automatically scale based on request traffic — including scaling all the way down to zero Pods when idle and spinning back up when a request arrives. In the context of AI workloads, Knative is the engine underneath KServe that makes scale-to-zero inference possible.

## What problem does it solve?
GPUs are expensive. An inference endpoint that sits idle overnight still burns GPU hours at full cost. Without Knative, you either accept that waste or build custom automation to scale down idle Deployments and intercept incoming requests to trigger scale-up. Knative solves this natively: it watches request queues, scales Pods to match demand, and drops to zero when traffic stops. When a new request arrives, its activator component intercepts it, triggers a scale-up, buffers the request, and forwards it once the Pod is ready. For inference workloads, this means you only pay for GPUs when models are actively serving predictions.

## Where does it fit in the stack?
Knative provides the serverless runtime layer beneath KServe, handling autoscaling and scale-to-zero for inference endpoints while KServe manages the model serving logic, traffic splitting, and API surface.

## Current status
- **CNCF status:** Graduated (October 8, 2025)
- **Latest version:** See [knative.dev/docs](https://knative.dev/docs) for current releases
- **Key CRDs:** Service, Route, Configuration, Revision (Knative Serving)

## Get started
- Official docs: [https://knative.dev](https://knative.dev)
- GitHub: [https://github.com/knative](https://github.com/knative)
- Related lab: [labs/04-kserve-inference](../../labs/04-kserve-inference) (Knative is used as KServe's backend)

## Last verified
March 2026 — all facts checked against official sources.
