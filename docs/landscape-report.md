# Kubernetes is now the operating system for AI

**Kubernetes has become the default platform for running AI workloads at scale, and the last six months have been the most transformative period yet.** Between October 2025 and March 2026, DRA graduated to GA making GPU orchestration a first-class Kubernetes primitive, the Agentic AI Foundation launched under the Linux Foundation with backing from Anthropic, OpenAI, and Block, and CNCF introduced its first Kubernetes AI Conformance Program. The numbers tell the story: **66% of organizations already hosting generative AI models use Kubernetes for inference workloads**, 41% of AI developers are cloud native, and the CNCF ecosystem has grown to 15.6 million developers globally. KubeCon EU Amsterdam 2026 is the most AI-saturated KubeCon ever, with a dedicated AI+ML track, two AI-focused co-located events, and agentic AI content permeating nearly every session.

---

## The Kubernetes AI platform stack has crystallized

Kubernetes 1.35 "Timbernetes" (released December 17, 2025) marked a turning point. Three features landed that collectively position Kubernetes as a purpose-built AI orchestrator:

**Dynamic Resource Allocation (DRA) is now GA and locked.** After graduating in K8s 1.34 (August 2025), DRA's core feature gate was locked in 1.35, meaning it cannot be disabled. DRA replaces the rigid device plugin model with declarative, attribute-aware GPU allocation. Workloads can now express requirements like "2 GPUs with NVLink interconnect, minimum 40GB VRAM, driver version 550+" using CEL expressions. Sub-features continue evolving: Prioritized Resource Alternatives and Admin-Only Resource Claims reached beta in 1.34, while Device Taints & Tolerations, Consumable Capacity, and Device Binding Conditions remain in alpha. Cloud adoption is strong — AKS published DRA guides for NVIDIA vGPU and MIG in March 2026, GKE uses DRA as its primary GPU/TPU scheduling primitive, and EKS enables DRA by default on K8s 1.34+.

**In-Place Pod Resize reached GA**, enabling inference services to dynamically adjust CPU and memory without pod restarts. This is critical for model serving workloads that need to scale resources based on traffic patterns.

**Gang Scheduling and Workload-Aware Scheduling entered alpha**, bringing all-or-nothing pod placement directly into the Kubernetes scheduler for the first time. Previously available only through external schedulers like Kueue and Volcano, native gang scheduling ensures distributed training jobs either start all pods together or not at all, eliminating the partial-placement deadlocks that waste expensive GPU time.

The scheduling stack has also matured into a coherent layered architecture. **Kueue** (now CNCF Incubating, v0.16.4) handles admission control, fair sharing, and topology-aware scheduling. **JobSet** (v0.11.1) orchestrates distributed training job groups with coordinated failure handling. **LeaderWorkerSet** (v0.8.0, stable API) manages long-running multi-host inference workloads where LLMs are sharded across nodes. Together with DRA for device allocation, these four components form the canonical Kubernetes AI platform stack that cloud providers and enterprises are converging on.

---

## CNCF projects are reshaping the inference layer

The inference side of the stack saw the most dramatic changes. The **Gateway API Inference Extension** reached GA, introducing two new CRDs — **InferenceObjective** (previously named InferenceModel, renamed at GA) and **InferencePool** — that enable model-aware routing, KV-cache-aware load balancing, LoRA adapter traffic splitting, and request criticality prioritization. Built as an Envoy External Processing extension, it works with Envoy Gateway, kgateway, GKE Gateway, and Istio (which added support in v1.27). GKE's Inference Gateway claims **30% cost reduction and 60% lower tail latency** compared to traditional load balancing.

**KServe** was accepted as a CNCF Incubating project in September 2025 and released v0.17.0 on March 13, 2026. The latest release integrates with the Gateway API Inference Extension v1.2.0, adds a new `LLMInferenceService` CRD for disaggregated serving through llm-d, and includes KV cache offloading and model caching capabilities. KServe has evolved from a predictive-only inference platform to a unified generative+predictive serving layer, with **5,990 GitHub stars** and adoption by Bloomberg, Red Hat, NVIDIA, and SAP.

**llm-d** has emerged as the Kubernetes-native distributed LLM inference framework, launched by Red Hat with founding contributors CoreWeave, Google Cloud, IBM Research, and NVIDIA, and partners AMD, Cisco, Hugging Face, Intel, Lambda, and Mistral AI. Its v0.5 release (February 2026) delivers hierarchical KV offloading, cache-aware LoRA routing, and scale-to-zero autoscaling. Benchmarks show ~3,100 tokens/second per B200 decode GPU and up to 50,000 output tokens/second on a 16×16 B200 topology. The v0.4 release (December 2025) achieved a **40% reduction in per-output-token latency** for DeepSeek V3.1 on H200 GPUs.

**Knative graduated from CNCF** on October 8, 2025 — a milestone that directly benefits the AI ecosystem since Knative provides the scale-to-zero serverless backend for KServe inference workloads.

Other notable CNCF AI projects include **KAITO** (Kubernetes AI Toolchain Operator, Sandbox, v0.9.0 released February 2026), **HAMi** (heterogeneous GPU virtualization middleware, Sandbox), **Volcano** (batch scheduling, Incubating, v1.13 with native LeaderWorkerSet support and HyperNode topology discovery), and **Armada** (multi-cluster job meta-scheduler, Sandbox).

---

## The Agentic AI Foundation changes everything about AI agents

The single biggest ecosystem development was the **launch of the Agentic AI Foundation (AAIF)** on December 9, 2025, as a directed fund under the Linux Foundation. Co-founded by Anthropic, Block, and OpenAI, AAIF provides vendor-neutral governance for three foundational projects:

- **Model Context Protocol (MCP)** — donated by Anthropic, originally open-sourced November 2024. MCP standardizes how AI models connect to external tools and data sources using JSON-RPC 2.0. It has exploded in adoption: **97 million monthly SDK downloads**, over **10,000 published MCP servers**, and integration into Claude, ChatGPT, Gemini, VS Code, Cursor, and GitHub Copilot.
- **goose** — donated by Block, an open-source local-first AI agent framework combining LLMs with MCP-based tool integration.
- **AGENTS.md** — donated by OpenAI, a markdown convention for giving AI coding agents project-specific guidance, adopted by **60,000+ open-source projects**.

AAIF's membership exploded to **146 members** by February 2026. Platinum members include AWS, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft, and OpenAI. Gold members include Cisco, Datadog, Docker, IBM, JetBrains, Oracle, Salesforce, SAP, Shopify, and Snowflake.

The MCP specification (latest version 2025-11-25) now supports asynchronous long-running tasks, stateless server deployments, server identity via `.well-known` URLs, and OAuth 2.1 authorization. The protocol has effectively won the agent-to-tool communication race, while Google's **A2A (Agent-to-Agent) protocol** — donated to the Linux Foundation in June 2025 — addresses the complementary agent-to-agent communication space.

In the Kubernetes world, MCP deployment is maturing rapidly. **kagent** (contributed to CNCF by Solo.io) is the first Kubernetes-native agentic AI framework, with its **kmcp** subproject providing CRDs for deploying MCP servers. **ToolHive** (by Stacklok) offers enterprise-grade MCP server management with a Kubernetes operator, embedded authorization, and 60-85% token optimization. **agentgateway** (donated to the Linux Foundation by Solo.io) is a purpose-built Rust proxy for MCP and A2A protocols. And OpenTelemetry merged official **MCP semantic conventions in January 2026**, standardizing observability for agent-tool interactions.

---

## AI Gateways are evolving into Agent Gateways

The AI Gateway pattern has matured from a niche concern to a critical infrastructure component, and is now evolving beyond simple LLM proxying into full agent traffic management.

**Envoy AI Gateway** (envoyproxy/ai-gateway), initiated by Bloomberg and Tetrate in October 2024, was the first CNCF-backed AI gateway. It uses a two-tier architecture: a centralized tier for authentication and global rate limiting across external LLM providers, and a self-hosted tier for inference-aware routing to on-premises models. Key capabilities include token-based rate limiting with CEL expressions, provider failover, and credential management.

On **March 9, 2026**, a new **AI Gateway Working Group** was formally announced within the Kubernetes community, focused on standards for token-based rate limiting, payload processing, egress gateways for external AI services, and secure routing. This working group signals that AI traffic management is becoming a first-class concern in the Kubernetes ecosystem.

**kgateway** (CNCF Sandbox, formerly Gloo by Solo.io) became the first gateway to achieve conformance with both Gateway API v1.3.0 and the Inference Extension v1.0.0. Its November 2025 v2.1 release deprecated Envoy-based AI Gateway support in favor of integrating with **agentgateway** as its AI data plane — signaling the industry shift from "AI Gateway" (LLM proxy) to "Agent Gateway" (proxy for agentic systems supporting MCP and A2A protocols).

Commercial solutions have also matured. Kong offers 20+ LLM provider integrations with AI-specific plugins for prompt guarding and token rate limiting. Apache APISIX positions itself as "cloud-native to AI-native" with multi-LLM load balancing. Traefik Hub defines AIService CRDs. The common feature set across all solutions includes token-based rate limiting, multi-provider routing, prompt security and PII detection, semantic caching, and streaming-aware load balancing.


---

## What Linux Foundation initiatives should newbies know about

The Linux Foundation now hosts the most comprehensive open-source AI ecosystem in the world, organized across several umbrella foundations:

The **LF AI & Data Foundation** (lfaidata.foundation) hosts 50+ projects spanning the AI/ML lifecycle including ONNX, Milvus, Horovod, Flyte, and OPEA. Its **Generative AI Commons** working group (80+ organizations, 200+ active members) has produced two key specifications: the **Model Openness Framework (MOF)** — a three-tier classification for model openness, and the **Responsible Generative AI Framework (RGAF) v0.9** — mapping responsible AI dimensions to the EU AI Act, NIST AI Framework, and other regulatory frameworks.

The **PyTorch Foundation** has expanded significantly, with Ray joining in October 2025 alongside vLLM and DeepSpeed. Mark Collier was named GM of AI at the Linux Foundation and Executive Director of the PyTorch Foundation in February 2026. The "PARK stack" (PyTorch, AI, Ray, Kubernetes) is emerging as the canonical open-source AI compute stack.

The **CNCF Annual Survey** (published January 20, 2026) provided the definitive state-of-the-industry snapshot: **82% of container users run Kubernetes in production**, 66% of organizations already hosting generative AI models use it for inference, 52% of organizations don't train their own models (they're consumers of pretrained models), and cultural change remains the #1 challenge at 47%.

---

## KubeCon EU 2026 is the most AI-focused KubeCon yet

KubeCon + CloudNativeCon Europe 2026 runs March 23-26 at the RAI Amsterdam Convention Center with 12,000+ expected attendees. AI permeates the conference at every level:

**Co-located events on March 23** include two dedicated AI events: **Cloud Native AI + Kubeflow Day** (full-day, two parallel tracks covering LLMs, Graph RAGs, ethical AI, and the Kubeflow ecosystem) and the brand-new **Agentics Day: MCP + Agents** (half-day, 10+ talks on production MCP deployment, agent governance, and security). AI themes also appear in Platform Engineering Day, BackstageCon ("Agentic Backstage"), Observability Day, Cloud Native Telco Day, KeycloakCon ("MCP Authorization for Enterprise"), and KyvernoCon ("Policy for AI-era Kubernetes").

The main conference features a dedicated **AI + Machine Learning track** with sessions including "SIG Network: The State of Networking for AI on Kubernetes" (Red Hat, Google, NVIDIA, IBM), "GPUs on Kubernetes: What Actually Happens When You Request nvidia.com/gpu: 1" (LearnKube), "Sandbox Operator: Enabling Session-Aware MCP Tool Execution in Kubernetes" (Alibaba), and "Securing the AI/ML Lifecycle With MLSecOps" (Dell, Ericsson). European-specific content addresses sovereign cloud requirements and open-source AI reference stacks for EU compliance.

Key expected announcements include the **Kubernetes AI Conformance Program v2.0 roadmap** (expanding from the v1.0 launched at KubeCon NA 2025 in Atlanta), further MCP standardization updates, and project milestones for llm-d, KServe, and Kubeflow.

---

## The industry is converging on eight key trends

Stepping back from individual projects, eight macro trends define cloud-native AI in early 2026:

1. **Inference over training.** The CNCF survey found 52% of organizations don't train their own models. The ecosystem is responding — llm-d, the Gateway API Inference Extension, KServe's generative AI features, and the AI Gateway Working Group all optimize the inference path.

2. **DRA as the GPU abstraction layer.** With DRA GA and locked in K8s 1.35, the fragmented device plugin ecosystem is being replaced by a unified, declarative model. NVIDIA, AMD (GPU Operator v1.4.0 with experimental DRA driver), and cloud providers are all shipping DRA drivers.

3. **Topology awareness is table stakes.** Every major scheduler — Kueue, Volcano (with HyperNode CRD for NVLink/InfiniBand discovery), NVIDIA KAI Scheduler, and Run:ai — now offers topology-aware scheduling. NVIDIA's ComputeDomains enable multi-node NVLink on GB200 NVL72 systems through DRA.

4. **The rise of agentic infrastructure.** AAIF, MCP, A2A, kagent, agentgateway, and ToolHive collectively signal that AI agents are the next major workload class for Kubernetes, following the microservices era.

5. **AI Gateways becoming Agent Gateways.** The evolution from simple LLM proxying to MCP/A2A-native traffic management reflects the shift from API-style model calls to autonomous multi-step agent workflows.

6. **Multi-cluster GPU scheduling.** MultiKueue (beta), Volcano Global, and KubeStellar+Kueue integration enable distributing AI workloads across cluster boundaries — validated by CERN at KubeCon NA 2025.

7. **NVIDIA's Blackwell era on Kubernetes.** The GPU Operator v25.10.0 supports GB200 and GB300 NVL72 with ComputeDomains, CDI by default, and hardened container images. The KAI Scheduler (open-sourced from Run:ai) provides topology-aware scheduling for these new architectures.

8. **Standards and conformance maturing.** The Kubernetes AI Conformance Program, the Model Openness Framework, RGAF, OpenTelemetry MCP semantic conventions, and the AGENTS.md standard all reflect an ecosystem moving from experimentation to production standardization.

---

## Conclusion

The cloud-native AI landscape has undergone a fundamental phase transition in the last six months. Kubernetes is no longer just "a good option" for AI — it is the operating system for AI workloads, with **82% production adoption** and purpose-built primitives from DRA to gang scheduling to inference-aware routing. The most significant shift is organizational: AAIF's formation means that Anthropic, OpenAI, and the broader industry have chosen Linux Foundation governance for agentic AI standards, mirroring how CNCF established Kubernetes as the standard for cloud infrastructure a decade ago. For anyone entering this space, the core message is clear — the stack has converged around Kubernetes + DRA + Kueue + KServe/llm-d + Gateway API Inference Extension + MCP, and the next frontier is agentic AI as a first-class cloud-native workload. KubeCon EU Amsterdam 2026 arrives at exactly the right moment to crystallize this new reality.