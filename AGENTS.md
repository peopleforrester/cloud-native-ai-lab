# AGENTS.md

## Project overview

This is `cloud-native-ai-lab` — a hands-on learning resource for Kubernetes engineers who are new to AI workloads. It was created as a companion to a Cloud Native University talk at KubeCon EU 2026 but is designed as a long-lived community resource.

**Author:** Michael Forrester — KodeKloud
**License:** Apache 2.0

## Audience

Kubernetes practitioners who know pods, deployments, services, and namespaces but have never touched AI/ML workloads. Do NOT assume ML knowledge.

## Repository structure

```
cloud-native-ai-lab/
├── README.md              # Main entry point, learning path, prerequisites
├── AGENTS.md              # This file — AI assistant context
├── LICENSE                # Apache 2.0
├── checklist.md           # Step-by-step learning path checklist
├── docs/
│   ├── landscape-report.md    # Full cloud-native AI landscape report (March 2026)
│   ├── talk-outline.md        # KubeCon EU 2026 talk outline
│   └── projects/              # One-pager per project (11 total)
├── labs/
│   ├── 00-setup/              # Kind cluster setup
│   ├── 01-kueue-basics/       # GPU scheduling fundamentals
│   ├── 02-dra-resource-claims/ # Device allocation
│   ├── 03-jobset-training/    # Distributed training simulation
│   ├── 04-kserve-inference/   # Model serving
│   ├── 05-gateway-routing/    # Inference-aware routing
│   ├── 06-kagent-mcp/         # AI agents and MCP
│   └── optional/              # Cloud GPU cluster setups (EKS/GKE/AKS)
└── .github/
    └── CONTRIBUTING.md
```

## Key conventions

### Lab READMEs

Every lab README follows this structure: What you'll learn → Prerequisites → Background → Exercise (numbered steps) → Verify it worked → What just happened? → Clean up → Next step.

### Project one-pagers

Every project one-pager follows this template: What is it? → What problem does it solve? → Where does it fit in the stack? → Current status (CNCF status, version, CRDs) → Get started (docs, GitHub, related lab) → Last verified.

### Manifest organization

Each lab has a `manifests/` subdirectory containing all Kubernetes YAML files for that lab. Manifests are self-contained — they should not depend on files from other labs.

### Code files

All code files (Python, shell scripts) start with a 2-line ABOUTME comment describing the file's purpose.

## Mandatory fact-check corrections

These corrections have been verified against official sources. They MUST be applied whenever these topics are mentioned:

1. **JobSet version is v0.11.1** — NOT v0.10.1 as stated in some source materials.
2. **MCP server count is 10,000+** — NOT 6,400. The official figure from Anthropic and the Linux Foundation is "over 10,000 published MCP servers."
3. **InferenceModel CRD was renamed to InferenceObjective** — The Gateway API Inference Extension GA/v1 release renamed this CRD. Always use InferenceObjective when referring to the v1/GA API.
4. **The 66% gen AI statistic** — This applies to "organizations already hosting generative AI models," not all surveyed organizations. Always include this qualifier.
5. **llm-d was launched by Red Hat** — Founding contributors are CoreWeave, Google Cloud, IBM Research, and NVIDIA. Partners include AMD, Cisco, Hugging Face, Intel, Lambda, and Mistral AI. Do NOT present all companies as equal "co-creators."

## Content guidelines

- All claims must be verifiable against official sources — no hallucinated version numbers or dates.
- Do not guess version numbers from training data. Use the landscape report and fact-check document as the source of truth.
- Be honest when a lab step cannot work on kind without GPU hardware. Provide annotated manifests with conceptual walkthroughs instead of broken instructions.
- No marketing language. No "revolutionary" or "game-changing." Clear, factual, helpful.
- This is a community resource, not a KodeKloud branded product. Do not promote KodeKloud beyond the speaker attribution on the talk outline.
