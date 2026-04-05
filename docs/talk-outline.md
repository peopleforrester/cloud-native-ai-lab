# AI + Kubernetes: What Beginners Need to Know in 2026

## A 15-Minute Talk for Cloud Native University @ KubeCon + CloudNativeCon Europe 2026 — Amsterdam

**Speaker:** Michael Forrester — KodeKloud
**Program:** Cloud Native University
**Date:** Tuesday, March 24, 2026 — 13:20 | RAI Amsterdam Convention Center

---

## The Hook (0:00–1:30)

Open with a question to the audience:

> "Raise your hand if your job title has the word 'AI' in it."
>
> *Pause.*
>
> "Now raise your hand if you've deployed, managed, or been asked to support an AI workload in the last six months."
>
> *Watch the second group dwarf the first.*
>
> "That gap — between what you're called and what you're doing — is the entire story of cloud-native AI in 2026. And if you're sitting in a Cloud Native University session right now wondering whether you're behind, you're not. You're exactly where you need to be."

**The thesis:** The CNCF survey published in January told us that 82% of container users run Kubernetes in production and 66% are using it for generative AI. But here's the number that matters most: 52% of organizations aren't even training their own models. They download one and serve it. That means most of the "AI work" happening right now is infrastructure work. It's scheduling, networking, and observability. It's stuff you already know. This talk fills in the gaps.

---

## PART 1 — "What's new in Kubernetes for AI?" (1:30–5:00)

### The single biggest thing: GPUs are now first-class citizens

For years, requesting a GPU in Kubernetes was clunky. You'd use a device plugin, ask for `nvidia.com/gpu: 1`, and hope for the best. You couldn't say "I need a GPU with at least 40GB of VRAM" or "give me two GPUs connected by NVLink." It was like ordering food by saying "one food, please."

**DRA (Dynamic Resource Allocation)** fixes this. It graduated to GA in Kubernetes 1.34 (August 2025) and was permanently locked on in Kubernetes 1.35 (December 2025). "Locked" means you can't disable it — it's a permanent part of the platform now.

With DRA, you can say things like:
- "I need 2 GPUs with NVLink interconnect"
- "Minimum 40GB VRAM"
- "Driver version 550 or higher"

All three major clouds support it: EKS, GKE, and AKS all ship DRA. AKS just published guides for DRA with NVIDIA vGPU and MIG this month.

**Why this matters for beginners:** If you're learning Kubernetes for AI workloads, DRA is the #1 concept to understand. It's how every AI workload will request hardware going forward. Learn it like you learned resource requests and limits for CPU and memory.

### Two other Kubernetes 1.35 features worth knowing

**In-Place Pod Resize reached GA.** This lets a running pod change its CPU and memory without restarting. For AI inference services that need to scale up during traffic spikes and scale down when it's quiet, this is huge — no more killing a pod that's mid-request.

**Gang Scheduling entered alpha.** This is all-or-nothing pod placement. If your distributed training job needs 8 GPUs across 4 nodes, gang scheduling ensures either all 8 pods get placed or none of them do. Without this, you get deadlocks where half your pods are placed and waiting forever for the other half.

---

## PART 2 — "What's the AI stack on Kubernetes?" (5:00–9:00)

### The four projects that form the foundation

This is the part that looks complicated until you realize it's just four things doing four jobs:

**1. DRA** — handles device allocation. "Give me GPUs with these specific attributes." You just learned this one.

**2. Kueue** — handles queuing and admission control. Think of it as a traffic controller for GPU jobs. It decides who gets to run, when, and with what share of the cluster. It knows about topology too — it can place your workload near the right GPU interconnects. CNCF Incubating project, version 0.17.0.

**3. JobSet** — handles distributed training. If you're training a model across multiple nodes, JobSet coordinates all the pieces and handles failures. If one pod dies, it knows what to do with the rest. Version 0.11.1.

**4. LeaderWorkerSet** — handles long-running inference. When a large language model is too big for one GPU, you shard it across multiple nodes. LeaderWorkerSet manages that leader-worker topology and keeps it healthy. Version 0.8.0 with a stable API.

That's the scheduling foundation. DRA for devices, Kueue for admission, JobSet for training, LeaderWorkerSet for inference.

### The serving layer: how models actually get to users

**KServe** is the model serving platform. CNCF Incubating (accepted September 2025), version 0.17.0 released March 13, 2026. You give it a model, it serves it behind an API. It handles autoscaling, canary rollouts, and now has a dedicated CRD for LLM inference called `LLMInferenceService`. Bloomberg, Red Hat, NVIDIA, and SAP use it in production.

**Knative** provides the scale-to-zero capability underneath KServe. It graduated from CNCF in October 2025. Scale-to-zero means when nobody is sending requests, your inference pods scale down to zero and stop costing you GPU money. When a request comes in, they spin back up.

**llm-d** is the new project to know about for LLM inference specifically. Launched by Red Hat with contributions from Google Cloud, IBM Research, NVIDIA, CoreWeave, AMD, Cisco, and Hugging Face — that contributor list alone tells you the industry is serious about this. It's a Kubernetes-native framework for distributed LLM inference. It handles things like KV cache offloading (keeping frequently used context in fast memory), cache-aware LoRA routing (sending requests to the server that already has the right adapter loaded), and scale-to-zero. KServe v0.17.0 integrates directly with llm-d. You don't need to use llm-d on day one, but it's where high-performance LLM serving is headed on Kubernetes.

**The Gateway API Inference Extension** (now GA) makes routing smart. Instead of dumb round-robin load balancing, it can route requests based on which model you're calling, how full each server's KV cache is, which LoRA adapter you need, and how critical the request is. GKE's implementation reports 30% cost savings and 60% lower tail latency.

### The beginner mental model

Think of it in layers:
- **Bottom:** DRA gives you GPUs
- **Middle:** Kueue decides who gets them and when
- **Top:** KServe serves models to users, Gateway API routes traffic smartly

Everything else builds on top of these.

---

## PART 3 — "What about AI agents? What's MCP?" (9:00–11:00)

### The next wave: AI agents on Kubernetes

You've probably heard about AI agents — AI systems that don't just answer questions but take actions. They browse the web, write code, call APIs, query databases. The big question is: how do they connect to all those tools in a standard way?

**MCP (Model Context Protocol)** is the answer the industry settled on. Originally created by Anthropic and open-sourced in November 2024, MCP standardizes how AI models talk to external tools and data sources. Think of it like USB for AI — a universal plug that lets any model connect to any tool.

The numbers are wild: 97 million monthly SDK downloads, over 10,000 registered MCP servers, and it's integrated into Claude, ChatGPT, Gemini, VS Code, Cursor, and GitHub Copilot.

In December 2025, Anthropic donated MCP to the brand-new **Agentic AI Foundation (AAIF)** under the Linux Foundation. OpenAI donated **AGENTS.md** (a standard for giving AI coding agents project-specific guidance, adopted by 60,000+ projects). Block donated **goose** (an open-source AI agent framework). Three competitors collaborating on shared standards under neutral governance — that's a big deal.

### Why Kubernetes people should care

Agents need to run somewhere, and that somewhere is increasingly Kubernetes. Three projects are emerging:

- **kagent** (CNCF, by Solo.io) — gives you Kubernetes CRDs for deploying and managing AI agents and MCP servers
- **ToolHive** (by Stacklok) — enterprise MCP server management with a Kubernetes operator
- **agentgateway** (Linux Foundation, by Solo.io) — a proxy specifically built for MCP and agent-to-agent traffic

You don't need to master these today. But know they exist, because six months from now, "deploy an MCP server on Kubernetes" is going to be as common a task as "deploy a microservice."

---

## PART 4 — "Where do I go from here?" (11:00–15:00)

### This week at KubeCon

You're at the right conference. Here's how to make the most of the next two days:

**Attend sessions from the AI + Machine Learning track.** Two to prioritize: "GPUs on Kubernetes: What Actually Happens When You Request nvidia.com/gpu: 1" (great beginner session from LearnKube) and "Securing the AI/ML Lifecycle With MLSecOps" (Dell, Ericsson).

**If you were here yesterday (Monday),** hopefully you caught Cloud Native AI + Kubeflow Day or Agentics Day — but if you missed them, the recordings will be available.

**Talk to people in the expo hall** who are working on DRA, Kueue, KServe, and llm-d. The maintainers are here. They love beginners who ask questions. Seriously — walk up to the CNCF project pavilion and say "I'm new to AI on Kubernetes, what should I learn first?" You'll get a better answer than any blog post.

### After KubeCon — your 30-day learning path

**Week 1: Read.** Start with the CNCF Annual Survey (January 2026) — it's the single best document for understanding where the industry actually is vs. where the hype says it is. Then read the Kubernetes 1.35 release blog, specifically the DRA and gang scheduling sections.

**Week 2: Schedule.** Install Kueue on a test cluster. Submit a job. Set up fair sharing between two queues. This is where you build intuition for how AI workloads get scheduled differently from web services. If you have access to a GPU node, create a DRA ResourceClaim and watch how it gets allocated.

**Week 3: Serve.** Deploy a model with KServe. Pick something small — Mistral 7B or Llama 3.1 8B. Get it serving inference behind an API. Send it traffic. Watch it autoscale. Break it on purpose. Fix it. This is the week where it stops being abstract.

**Week 4: Explore.** Go deeper on the piece that grabbed you. If it's GPU scheduling, dig into DRA's CEL expressions and topology awareness. If it's model serving, try llm-d behind KServe. If it's agents, deploy an MCP server with kagent and connect it to a model. Pick your lane.

**Week 5+: Contribute.** Every project I mentioned today is open source and actively looking for contributors. The AI Gateway Working Group was announced two weeks ago — it's brand new, and your voice matters. File an issue. Review a PR. Write the blog post about what you learned. The best way to learn this stuff is to participate.

### The honest truth about "10x AI engineers"

Here's the secret nobody tells you: **the 10x AI engineer everyone's hiring for is a platform engineer who understands AI workload patterns.**

The data scientists aren't going to learn DRA. The ML researchers aren't going to configure Kueue fair-sharing policies. The prompt engineers aren't going to set up MCP server authorization. But someone has to.

If you already know Kubernetes — if you already understand scheduling, networking, storage, and observability — you're 80% of the way there. The other 20% is understanding three workload patterns:

- **Training** is batch, parallel, and GPU-bound → JobSet + Kueue
- **Inference** is latency-sensitive, bursty, and memory-bound → KServe + LeaderWorkerSet
- **Agents** are long-running, tool-calling, and security-critical → kagent + MCP

You don't need to become a machine learning expert. You need to become the person who makes machine learning experts productive.

> "The best infrastructure is invisible. The best AI engineer is the one who makes GPUs as boring as CPU cores."

Welcome to KubeCon. You're not behind. Go make AI boring.

---

## Appendix: Key Links & Resources

| Resource | URL |
|---|---|
| CNCF Annual Survey 2026 | cncf.io/announcements/2026/01/20 |
| Kubernetes 1.35 Release Notes | kubernetes.io/blog/2025/12/17 |
| DRA Documentation | kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation |
| KServe v0.17.0 | kserve.github.io/kserve |
| llm-d | github.com/llm-d/llm-d |
| Gateway API Inference Extension | gateway-api-inference-extension.sigs.k8s.io |
| Agentic AI Foundation | aaif.io |
| MCP Specification | modelcontextprotocol.io/specification/2025-11-25 |
| kagent | kagent.dev |
| ToolHive | docs.stacklok.com/toolhive |
| agentgateway | github.com/agentgateway/agentgateway |
| Kueue | kueue.sigs.k8s.io |
| KubeCon EU 2026 Schedule | kccnceu2026.sched.com |

---

## Speaker Notes: Timing Guide

| Section | Time | Duration | Audience Level |
|---|---|---|---|
| The Hook | 0:00–1:30 | 90 sec | Everyone |
| Part 1 — What changed in K8s for AI | 1:30–5:00 | 3.5 min | Beginner |
| Part 2 — The AI stack on K8s | 5:00–9:00 | 4 min | Beginner |
| Part 3 — Agents & MCP | 9:00–11:00 | 2 min | Beginner |
| Part 4 — Where to go + the close | 11:00–15:00 | 4 min | Beginner |
| **Total** | | **15 min** | |

**Pacing note:** Parts 1–2 are pure beginner and take 7.5 minutes — half the talk — covering what changed in Kubernetes and what the AI stack looks like. Part 3 introduces agents at a high level without assuming prior knowledge. Part 4 is the longest section after the core content because giving people a concrete plan is more valuable than more information. The "make AI boring" line is the closer — don't rush it.
