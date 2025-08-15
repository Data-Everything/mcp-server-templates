# Single entrypoint and routing
Task Context:
This is part of the same overall MCP platform development effort. You must complete all steps together in one workflow before finishing. Do not treat any part as separate or incomplete.

Overall Goal

Implement a unified MCP Gateway that:

Exposes a single HTTP(S) endpoint for all MCP servers:

Incoming requests follow https://<gateway-host>/<server-id>/<optional-path>

Dynamically routes requests to the correct MCP server:

Checks if server supports HTTP(S) JSON-RPC → forwards request

Otherwise, checks if server supports stdio → spawns or connects via stdio wrapper

Otherwise → returns error

Supports load balancing for multiple instances/pods of the same server:

Round-robin or other fair distribution for HTTP MCP servers

Pooling for stdio servers

Preserves JSON-RPC payloads transparently

Provides a configurable registry for MCP servers with connection metadata

Is extendable to Kubernetes services later

Uses Python (FastAPI or equivalent) and reuses existing MCP client/connection code wherever possible

Implementation Requirements

Plan First

Create a thorough Plan Document before coding. Include:

Evaluation of current MCP client & CLI capabilities and what can be reused

Protocol handling: HTTP vs stdio

Load balancing strategies and limitations

Registry format and dynamic discovery options

Implementation steps for routing, pooling, and proxying

Testing strategy: unit and integration

Rollback/cleanup plan

Keep this document as the source of truth and update it after every code change.

Gateway Implementation

HTTP Server

Use FastAPI or similar for the gateway

Accept incoming HTTP(S) requests and WebSocket connections

Parse <server-id> from URL

Route to the correct MCP server using registry

Server Connection Handling

Reuse existing logic to detect HTTP or stdio support

Wrap stdio MCP servers in async interface to forward JSON-RPC

Handle errors gracefully and return meaningful messages

Load Balancing

For HTTP MCP servers → round-robin between pods or backend URLs

For stdio servers → maintain a pool of connections / spawned processes

Registry

JSON or YAML file describing MCP servers and connection details

Example:

{
  "github-server": { "type": "http", "endpoint": "http://github-server:8080" },
  "filesystem-server": { "type": "stdio", "cmd": ["mcp-filesystem-server", "--dir", "/data"] }
}


Gateway reads registry on startup, supports dynamic reload if feasible

Testing

Unit Tests

Test connection detection (HTTP vs stdio)

Test routing logic

Test load balancing distribution

Integration Tests

Simulate multiple MCP servers (HTTP + stdio)

Send JSON-RPC requests via the gateway

Verify correct forwarding and response

Test error handling for unknown servers

Cleanup / Code Reuse

Reuse existing MCP client code for protocol handling

Remove duplicated logic if moving to gateway

Ensure CLI continues to work independently if necessary

Final Checklist

Plan Document created and continuously updated

Single gateway endpoint implemented with HTTP(S) and WebSocket support

MCP server routing works for HTTP and stdio servers

Load balancing implemented for multiple instances

Configurable server registry exists and can be dynamically loaded

Unit + integration tests exist for all new/modified functionality

All tests pass successfully

No unused/old code or duplicated logic remains

# Kubernetes backend
Task Context:
This is part of the same overall MCP platform development effort. You must complete all steps together in one workflow before finishing. Do not treat any part as separate or incomplete.

Overall Goal

Enhance the MCP platform to support dynamic Kubernetes deployment for MCP servers, while preserving the existing Docker-based workflow. Specifically:

Provide Helm chart(s) or equivalent manifests for deploying MCP servers as pods/services.

Allow the gateway / MCP client to dynamically spawn MCP server pods on Kubernetes:

Each HTTP server gets its own pod

Pods can be scaled horizontally (replicas)

Support dynamic routing and service discovery from the gateway to Kubernetes pods.

Preserve JSON-RPC and stdio functionality where feasible (for local or non-HTTP MCP servers).

Ensure configurable resource allocation (CPU, memory) per pod.

Integrate load balancing across pods using Kubernetes Services.

Make it easy to add new MCP servers without modifying the gateway code.

Implementation Requirements

Plan First

Create a Plan Document before coding. Include:

Comparison between current Docker deployment and desired Kubernetes deployment

Helm chart structure and templates for MCP servers

Pod lifecycle management (creation, scaling, deletion)

Routing and service discovery approach (DNS, environment variables, or gateway integration)

Load balancing strategy via Kubernetes Services

Implementation steps for spawning pods dynamically from registry/config

Testing strategy for unit, integration, and cluster-level tests

Rollback and cleanup plan

Keep this document as the source of truth and update it after every code change.

Kubernetes Backend Implementation

Helm Chart / Manifests

Define templates for MCP server deployment: Deployment + Service + ConfigMap/Secrets as needed

Support per-server customization: image, environment variables, ports, resource limits

Dynamic Pod Management

Extend the gateway/MCP client to optionally create pods via Kubernetes API

Check if a pod for a given server already exists; if not, create it

Support pod scaling (replicas) via configuration or API

Routing & Load Balancing

Use Kubernetes Service to abstract multiple pod endpoints

Ensure gateway can route requests to correct service

Optionally implement round-robin or least-connections if multiple replicas

Registry Integration

Update MCP server registry to include Kubernetes metadata

Example registry entry:

{
  "github-server": { "type": "k8s", "chart": "github-server", "replicas": 2, "namespace": "mcp" }
}


Support dynamic lookup of running pods for each server

Testing

Unit Tests

Test pod creation logic via Kubernetes Python client

Test registry handling and metadata parsing

Integration Tests

Deploy multiple MCP server pods in a test cluster (minikube/k3d)

Verify gateway routing to pods works correctly

Test scaling up/down and load balancing

Cleanup Tests

Ensure all dynamically created pods and services are cleaned up after tests

Cleanup / Code Reuse

Reuse existing Docker deployment code where possible (image references, build scripts)

Remove duplication and ensure Docker and Kubernetes workflows can coexist

Document differences and configuration options for users

Final Checklist

Plan Document created and continuously updated

Helm chart(s) or manifests implemented for MCP servers

Gateway/MCP client can dynamically create and route to Kubernetes pods

Load balancing across replicas implemented and tested

Unit + integration tests exist for all new/modified functionality

All tests pass successfully

Docker and Kubernetes deployments co-exist cleanly

Documentation updated (README, mkdocs, example commands)
