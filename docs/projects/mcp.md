# Model Context Protocol (MCP)

## What is it?
MCP is a standard protocol that defines how AI models connect to external tools, data sources, and services. Think of it like USB for AI — before USB, every peripheral needed its own cable and driver; MCP does the same thing for model-to-tool connections. Built on JSON-RPC 2.0, it gives any model a universal way to discover, authenticate with, and call any tool that implements the MCP server spec. Originally created by Anthropic and open-sourced on November 25, 2024, MCP was donated to the Agentic AI Foundation (AAIF) on December 9, 2025.

## What problem does it solve?
Before MCP, every AI integration was bespoke. If you wanted your model to query a database, call an API, or read a file system, you wrote custom integration code for that specific model and that specific tool. With N models and M tools, that meant N x M integrations. MCP collapses this to N + M: each model implements one client, each tool implements one server, and they all speak the same protocol. The ecosystem has responded — there are over 10,000 published MCP servers and 97 million monthly SDK downloads, with native integration in Claude, ChatGPT, Gemini, VS Code, Cursor, and GitHub Copilot.

## Where does it fit in the stack?
MCP is the protocol layer that kagent uses to connect agents to tools — it defines the wire format, while kagent provides the Kubernetes-native deployment and lifecycle management.

## Current status
- **CNCF status:** Not a CNCF project — governed by the Agentic AI Foundation (AAIF) under the Linux Foundation
- **Latest spec version:** 2026-07-28 (2025-11-25 is now a past revision)
- **Key CRDs:** N/A (MCP is a protocol specification, not a Kubernetes operator — see kagent's MCPServer CRD for K8s integration)

### What the 2026-07-28 revision changes

If you learned MCP against the 2025-11-25 spec, three things you were taught are
no longer true:

- **The protocol is stateless.** The `initialize` and
  `notifications/initialized` handshake is gone, and so is the `Mcp-Session-Id`
  header on the Streamable HTTP transport. Every request now carries its own
  protocol version and client capabilities in `_meta`, so capability negotiation
  happens per request rather than once per connection. A server that needs state
  across calls mints an explicit handle and the client passes it back as an
  ordinary tool argument.
- **Servers no longer call back into the client.** `sampling/createMessage`,
  `roots/list` and `elicitation/create` are replaced by Multi Round-Trip
  Requests: the server returns an `InputRequiredResult` and the client retries
  the original request carrying `inputResponses`. Every result now has a
  required `resultType`.
- **Sampling, Roots and Logging are deprecated**, along with OAuth Dynamic
  Client Registration. They still function, and the published policy is that
  removal comes no earlier than the first revision released on or after
  2027-07-28. `ping` and `logging/setLevel` were removed outright.

A new `server/discover` call advertises supported versions and capabilities up
front, and Tasks moved out of the core protocol into an official extension.

## Get started
- Official docs: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- GitHub: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
- Related lab: [labs/06-kagent-mcp](../../labs/06-kagent-mcp/)

## Last verified
September 2026. All facts checked against official sources.
