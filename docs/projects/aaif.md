# Agentic AI Foundation (AAIF)

## What is it?
The Agentic AI Foundation is a directed fund under the Linux Foundation that governs open standards for AI agent interoperability. Launched on December 9, 2025, and co-founded by Anthropic, Block, and OpenAI, it provides vendor-neutral stewardship for the protocols and conventions that let AI agents work with tools and with each other. It is not a software project — it is the governance body that ensures projects like MCP remain open and community-driven, similar to how the CNCF governs Kubernetes-ecosystem projects.

## What problem does it solve?
As AI agents proliferate, the industry faces a fragmentation risk: every vendor defining its own way for agents to discover tools, communicate, and describe themselves. AAIF prevents this by providing a neutral home for foundational standards. Without it, MCP could have remained an Anthropic-controlled project, goose could have stayed a Block-internal tool, and there would be no shared convention for agent self-description. AAIF gives these projects a governance model that encourages broad adoption — 146 member organizations had joined by February 2026.

## Where does it fit in the stack?
AAIF operates above the stack — it governs the standards (MCP, goose, AGENTS.md) that tools like kagent implement at the Kubernetes level.

## Current status
- **CNCF status:** Not a CNCF project — directed fund under the Linux Foundation
- **Latest version:** N/A (foundation, not software)
- **Key CRDs:** N/A

## Governed projects
- **MCP (Model Context Protocol):** The universal protocol for model-to-tool communication
- **goose:** An open-source AI agent framework (originally from Block)
- **AGENTS.md:** A convention for describing agent capabilities in a repository, analogous to SECURITY.md or CONTRIBUTING.md

## Membership highlights
- **Platinum members:** AWS, Bloomberg, Cloudflare, Google, Microsoft, and others
- **Total members:** 146 as of February 2026

## Get started
- Official site: [aaif.io](https://aaif.io)
- Related lab: [labs/06-kagent-mcp](../../labs/06-kagent-mcp/) (context — the lab uses MCP, which AAIF governs)

## Last verified
March 2026 — all facts checked against official sources.
