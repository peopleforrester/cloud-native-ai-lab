# kagent

## What is it?
kagent is a Kubernetes-native framework for deploying and managing AI agents and MCP (Model Context Protocol) servers. Contributed to the CNCF by Solo.io, it lets you define agents, the models they use, and their available tools as Kubernetes custom resources, the same way you define Deployments and Services today. Its kmcp subproject adds CRDs specifically for managing MCP servers, so you can treat tool integrations as declarative Kubernetes objects rather than hand-wired configurations.

## What problem does it solve?
Without kagent, running AI agents on Kubernetes means writing custom glue code: spinning up containers, wiring tool access, managing credentials, and coordinating multi-agent workflows, all imperatively. kagent brings the Kubernetes operating model (declare what you want, let controllers reconcile it) to the agent world. You define an Agent CR with its model, tools, and instructions; kagent handles the rest, including lifecycle management and scaling. Think of it as the Deployment controller, but for AI agents instead of pods.

## Where does it fit in the stack?
kagent operates at the application layer above the inference stack. It consumes models served by KServe/llm-d and connects them to external tools via MCP servers.

## Current status
- **CNCF status:** Sandbox
- **Latest version:** v0.10.3 (2026-10-02) is the newest non-alpha release and the version lab 06 pins. The v1.0.0 alpha releases move the CRDs to the `api.kagent.dev` group and drop MCPServer.
- **Key CRDs (v0.10.3, `kagent.dev` group):** Agent, ModelConfig, ModelProviderConfig, RemoteMCPServer, ToolServer, Memory, AgentHarness, SandboxAgent (kagent core); MCPServer (kmcp subproject, installed by the same `kagent-crds` chart)

## Get started
- Official docs: [kagent.dev](https://kagent.dev)
- GitHub: [github.com/kagent-dev/kagent](https://github.com/kagent-dev/kagent)
- Related lab: [labs/06-kagent-mcp](../../labs/06-kagent-mcp/)

## Last verified
July 2026. All facts checked against official sources. Latest version and CRDs re-checked against kagent's v0.10.3 release on 2026-10-17.
