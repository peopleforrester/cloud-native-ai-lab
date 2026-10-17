# Lab 06: kagent and MCP

## What you'll learn

- What AI agents are and why they belong on Kubernetes
- The Model Context Protocol (MCP) and how it standardizes tool access for LLMs
- How to deploy a kagent Agent definition and the ModelConfig it uses
- How to configure an MCP server as a tool source for an agent
- Where agentgateway and ToolHive fit for production deployments

## Prerequisites

- Lab 00 completed (kind cluster running with kubectl configured)
- `helm` installed and available on your PATH

## Background

An AI agent is an LLM that can take actions, not just generate text. Instead of
responding with "you should run kubectl get pods," an agent actually runs the
command, reads the output, and decides what to do next. Agents need tools: shell
access, API calls, database queries, file operations. The problem is that every
agent framework invented its own way to define and connect tools, creating a
fragmented ecosystem.

The **Model Context Protocol (MCP)** solves this fragmentation. Created by
Anthropic and now an open standard, MCP defines a universal interface between AI
applications (clients) and tool providers (servers). Think of it as USB for AI:
before USB, every peripheral had its own connector. MCP gives every tool the same
plug. An MCP server exposes tools (functions the agent can call), resources (data
the agent can read), and prompts (templates for common tasks). The client
discovers available tools at runtime through a standard handshake.

The ecosystem has grown rapidly. There are over 10,000 MCP servers available
today, covering everything from GitHub and Slack to databases and cloud
providers. For Kubernetes operators, this means you can give an agent access to
your cluster, your monitoring stack, and your incident management system through
standardized, discoverable interfaces.

**kagent** brings agents to Kubernetes as native resources. This lab uses three
of its CRDs, all in the `kagent.dev` API group: Agent (the instructions and the
tools an agent may call), ModelConfig (which LLM provider and model to use, and
where the API key is stored), and MCPServer (an MCP server that kagent runs in
the cluster as a tool source). MCPServer comes from kmcp, a kagent subproject
whose CRD the kagent CRD chart installs alongside the core ones. kagent also
has RemoteMCPServer, for MCP servers already running somewhere else. This lab
pins kagent 0.10.3. The kagent 1.0 releases, still in alpha as of October 2026,
move to a different API group and drop MCPServer, so these manifests do not
apply to them. For production deployments, two
additional projects are worth knowing: **agentgateway** provides authentication,
rate limiting, and observability for MCP traffic (like an API gateway for tool
access), and **ToolHive** manages the lifecycle of MCP servers as containers with
security sandboxing. This lab covers the introductory concepts. Production setup
is a separate concern.

## Exercise

### Step 1: Install kagent CRDs

kagent publishes its custom resource definitions as a Helm chart called
`kagent-crds`. Install it at a pinned version:

```bash
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --version 0.10.3 \
  --namespace kagent \
  --create-namespace
```

This installs only the CRDs. The kagent controller, which turns these resources
into running agents, is a separate chart (`kagent`) that this lab does not
install.

Verify the CRDs are installed:

```bash
kubectl get crds | grep kagent.dev
```

You should see `agents.kagent.dev`, `modelconfigs.kagent.dev` and
`mcpservers.kagent.dev`, along with the other kagent CRDs:
`agentharnesses`, `memories`, `modelproviderconfigs`, `remotemcpservers`,
`sandboxagents` and `toolservers`.

### Step 2: Create a namespace and deploy an Agent definition

Create a namespace for agent workloads:

```bash
kubectl apply -f manifests/namespace.yaml
```

Apply the ModelConfig, then the Agent that uses it:

```bash
kubectl apply -f manifests/model-config.yaml
kubectl apply -f manifests/agent.yaml
```

Inspect the resources:

```bash
kubectl get modelconfigs,agents -n agents
kubectl describe agent k8s-helper -n agents
```

The ModelConfig resource defines:
- Which LLM provider and model to use
- Which Kubernetes Secret holds the API key

The Agent resource defines:
- Its type: `Declarative` (kagent runs it from this definition) or `BYO` (you
  bring your own agent image)
- Which ModelConfig to use
- System instructions (what the agent knows and how it should behave)
- Which tool sources (MCP servers) the agent can access, and which of their
  tools it may call

### Step 3: Deploy an MCP server configuration

Apply the MCP server manifest:

```bash
kubectl apply -f manifests/mcp-server.yaml
```

Inspect the MCP server resource:

```bash
kubectl get mcpservers -n agents
kubectl describe mcpserver kubernetes-tools -n agents
```

The MCPServer resource defines:
- The container that runs the MCP server (image, command and arguments)
- How the server speaks MCP: `stdio` (over stdin/stdout, which kmcp puts on the
  network for it) or `http`
- The port its Service listens on

The server here runs kagent's Kubernetes tools in read-only mode. The agent's
`toolNames` list narrows that further to four tools: list resources, describe
a resource, read events and read pod logs.

### Step 4: Verify the resources

Check that both resources are created and linked:

```bash
# List all agent-related resources
kubectl get agents,modelconfigs,mcpservers -n agents

# Check for any error events
kubectl get events -n agents --sort-by='.lastTimestamp'
```

> **Honest limitation:** On a kind cluster without the full kagent controller
> running, these resources will be created as CRD objects but the agent will
> not actually execute. The controllers that reconcile Agent and MCPServer
> resources into running pods need the `kagent` Helm chart, an LLM endpoint,
> and the API key Secret the ModelConfig names. The MCP server's service
> account would also need RBAC permission to read the cluster. This lab
> focuses on understanding the resource model: the CRDs and their
> relationships.

### Step 5: Understand production considerations

In a production deployment, several additional components are needed:

**agentgateway**: Sits between agents and MCP servers. It provides:
- Authentication and authorization for tool access
- Rate limiting to prevent runaway agents from overwhelming tools
- Observability (metrics, tracing, logging) for every tool call
- Policy enforcement (which agents can use which tools)

**ToolHive**: Manages MCP server lifecycles:
- Runs MCP servers as sandboxed containers
- Handles secrets injection (API keys, tokens) securely
- Provides health checking and automatic restart
- Supports both local and remote MCP servers

**Architecture in production:**

```
┌─────────────────┐
│   Agent Pod     │  ← kagent Agent resource
│   (LLM + loop)  │
└────────┬────────┘
         │ MCP protocol
         ▼
┌─────────────────┐
│  agentgateway   │  ← auth, rate limiting, observability
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│MCP Srv │ │MCP Srv │  ← managed by ToolHive
│(K8s)   │ │(GitHub) │
└────────┘ └────────┘
```

For a hands-on production setup, see the kagent documentation at
https://github.com/kagent-dev/kagent.

## Verify it worked

```bash
# CRDs should be installed
kubectl get crds | grep kagent.dev

# Agent, ModelConfig and MCPServer resources should exist
kubectl get agents -n agents
kubectl get modelconfigs -n agents
kubectl get mcpservers -n agents

# Resources should have the expected names
kubectl get agent k8s-helper -n agents -o yaml
kubectl get modelconfig k8s-helper-model -n agents -o yaml
kubectl get mcpserver kubernetes-tools -n agents -o yaml
```

## What just happened?

You defined three Kubernetes-native resources that represent an AI agent system:

1. **Agent**: A CRD that declares an AI agent's identity: which ModelConfig it
   uses, what instructions it follows, and which tool sources it can access.
   This is the Kubernetes-native way to manage agent configurations: versioned,
   auditable, and deployable through standard GitOps workflows.

2. **ModelConfig**: A CRD that declares which LLM provider and model to use and
   where the API key lives. Keeping it separate means many agents can share one
   model configuration, and you can switch models without editing each agent.

3. **MCPServer**: A CRD that declares a tool source using the Model Context
   Protocol. Instead of hardcoding tool integrations into agent code, MCP servers
   expose tools through a standardized discovery and invocation protocol.

The key insight is that agents and their tools become Kubernetes resources,
managed with kubectl, deployed with Helm or Kustomize, governed by RBAC, and
observable through standard Kubernetes tooling. This is the same operational
model you use for every other workload.

## Clean up

```bash
kubectl delete -f manifests/mcp-server.yaml
kubectl delete -f manifests/agent.yaml
kubectl delete -f manifests/model-config.yaml
kubectl delete namespace agents

# Remove CRDs (optional: only if you want to fully clean up).
# Uninstalling the chart deletes the kagent CRDs and any resources of those kinds.
helm uninstall kagent-crds --namespace kagent
kubectl delete namespace kagent
```

## Next step

You have completed all core labs. Return to the
[checklist](../../checklist.md) for further exploration topics, including the
optional cloud GPU labs for running these workloads with real GPU hardware.
