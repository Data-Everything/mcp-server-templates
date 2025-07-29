# Strategy Document: MCP Platform Refactor

**Version**: 1.1
**Date**: July 26, 2025
**Owner**: Data Everything Team
**Purpose**: To guide the refactoring of the MCP Platform, an open-core solution for deploying MCP servers, focusing on the demo template to validate the approach. The refactor leverages FastMCP, defaults to HTTP with Docker, enhances the CLI, and improves documentation for user-friendliness and scalability.

## 1. Project Overview
The **MCP Platform** enables users to deploy Model Context Protocol (MCP) servers as templates (e.g., demo, Zendesk) for AI agents (e.g., Claude) to interact with tools via standardized endpoints. The open-core model offers free templates and CLI, with premium features like managed hosting and a dashboard (Pro: $49/month, Enterprise: $500+/month). The refactor focuses on the **demo template** to validate the approach before scaling to other templates, aiming to:
- Maximize **FastMCP** usage for consistency and maturity.
- Default to **HTTP** for scalability, with stdio as a fallback.
- Use **Docker** for consistent local/remote deployments.
- Enhance CLI for config discoverability (including double-underscore notation) and tool listing.
- Ensure modular, testable, and well-documented code.
- Align with the vision: “From months to minutes” for AI-tool integration.

## 2. Strategic Principles
1. **Leverage FastMCP**: Reuse FastMCP functionality to reduce custom code and benefit from its maturity ([FastMCP Docs](https://gofastmcp.com/docs)).
2. **HTTP-First**: Prioritize HTTP for MCP server endpoints, supporting local and remote access. Support stdio only for niche local testing.
3. **Docker-Driven**: Use Docker for deployments, creating a unified network for management.
4. **User-Centric CLI**: Make the CLI intuitive, showing all config options (including double-underscore notation, e.g., `security__api_key`) and tools, with integration instructions for LLMs/frameworks.
5. **Demo Template Focus**: Refactor only the demo template to validate the approach before scaling.
6. **Consistency**: Use a base class and discovery service for template uniformity.
7. **Modularity and Testability**: Organize code logically, with comprehensive tests.
8. **Comprehensive Documentation**: Provide clear, auto-generated docs for configs, tools, and integrations.
9. **Open-Core Ecosystem**: Balance free features (CLI, templates) with premium features (managed API, marketplace).

## 3. Technical Strategy
### 3.1 FastMCP Integration
- **Objective**: Maximize FastMCP usage for the demo template.
- **Approach**:
  - Use FastMCP decorators for tools ([Decorating Methods](https://gofastmcp.com/patterns/decorating-methods)).
  - Adopt FastMCP CLI patterns ([CLI](https://gofastmcp.com/patterns/cli)).
  - Implement middleware for authentication/logging ([Middleware](https://gofastmcp.com/servers/middleware)).
  - Use FastMCP client for tool discovery ([Client](https://gofastmcp.com/clients/client)).
  - Follow deployment practices ([Running Server](https://gofastmcp.com/deployment/running-server)).
- **Example**: Rebuild `templates/demo/` with FastMCP’s `@tool` decorator, HTTP transport, and middleware.

### 3.2 HTTP as Default, Stdio as Fallback
- **Objective**: Simplify transport with HTTP, supporting stdio for edge cases.
- **Approach**:
  - Default to HTTP (`--http` flag, e.g., `mcp run demo --http`).
  - Support stdio via `--stdio` flag for local testing.
  - Ensure Docker deployments use HTTP (port 7071).
- **Rationale**: HTTP is scalable, Docker-friendly, and covers local/remote use cases. Stdio is niche and complex.

### 3.3 Docker Networking
- **Objective**: Simplify Docker management.
- **Approach**:
  - Create a Docker network (`mcp-platform`) for all deployments.
  - Use container names as path suffixes (e.g., `http://mcp.local:7071/demo`).
  - CLI command: `mcp deploy demo --docker --http` creates/joins network.
- **Example**: `docker network create mcp-platform; docker run --network mcp-platform --name demo -p 7071:7071 data-everything/demo-mcp-server`.

### 3.4 CLI Enhancements
- **Objective**: Make CLI discoverable and user-friendly.
- **Approach**:
  - Extend `mcp config demo` to show all options, including double-underscore notation (e.g., `--config security__api_key=abc`, `--env MCP_API_KEY=abc`, `security__api_key`).
  - Add `mcp tools demo` to list tools (e.g., `say_hello`, `get_server_info`) using `TemplateDiscovery` and FastMCP client.
  - Add `mcp connect demo --llm <llm>` to show integration code for Claude, OpenAI, VS Code, async functions.
  - Use FastMCP CLI patterns for consistency.
- **Example**:
  ```bash
  mcp config demo
  # Output: --config hello_from=value, --env MCP_HELLO_FROM=value, --config demo__hello_from=value
  mcp tools demo
  # Output: say_hello, get_server_info
 # Strategy Document: MCP Platform Refactor

 **Version**: 1.1
 **Date**: July 26, 2025
 **Owner**: Data Everything Team
 **Purpose**: To guide the refactoring of the MCP Platform, an open-core solution for deploying MCP servers, focusing on the demo template to validate the approach. The refactor leverages FastMCP, defaults to HTTP with Docker, enhances the CLI, and improves documentation for user-friendliness and scalability.

 ## 1. Project Overview
 The **MCP Platform** enables users to deploy Model Context Protocol (MCP) servers as templates (e.g., demo, Zendesk) for AI agents (e.g., Claude) to interact with tools via standardized endpoints. The open-core model offers free templates and CLI, with premium features like managed hosting and a dashboard (Pro: $49/month, Enterprise: $500+/month). The refactor focuses on the **demo template** to validate the approach before scaling to other templates, aiming to:
 - Maximize **FastMCP** usage for consistency and maturity.
 - Default to **HTTP** for scalability, with stdio as a fallback.
 - Use **Docker** for consistent local/remote deployments.
 - Enhance CLI for config discoverability (including double-underscore notation) and tool listing.
 - Ensure modular, testable, and well-documented code.
 - Align with the vision: “From months to minutes” for AI-tool integration.

 ## 2. Strategic Principles
 1. **Leverage FastMCP**: Reuse FastMCP functionality to reduce custom code and benefit from its maturity ([FastMCP Docs](https://gofastmcp.com/docs)).
 2. **HTTP-First**: Prioritize HTTP for MCP server endpoints, supporting local and remote access. Support stdio only for niche local testing.
 3. **Docker-Driven**: Use Docker for deployments, creating a unified network for management.
 4. **User-Centric CLI**: Make the CLI intuitive, showing all config options (including double-underscore notation, e.g., `security__api_key`) and tools, with integration instructions for LLMs/frameworks.
 5. **Demo Template Focus**: Refactor only the demo template to validate the approach before scaling.
 6. **Consistency**: Use a base class and discovery service for template uniformity.
 7. **Modularity and Testability**: Organize code logically, with comprehensive tests.
 8. **Comprehensive Documentation**: Provide clear, auto-generated docs for configs, tools, and integrations.
 9. **Open-Core Ecosystem**: Balance free features (CLI, templates) with premium features (managed API, marketplace).

 ## 3. Technical Strategy
 ### 3.1 FastMCP Integration
 - **Objective**: Maximize FastMCP usage for the demo template.
 - **Approach**:
   - Use FastMCP decorators for tools ([Decorating Methods](https://gofastmcp.com/patterns/decorating-methods)).
   - Adopt FastMCP CLI patterns ([CLI](https://gofastmcp.com/patterns/cli)).
   - Implement middleware for authentication/logging ([Middleware](https://gofastmcp.com/servers/middleware)).
   - Use FastMCP client for tool discovery ([Client](https://gofastmcp.com/clients/client)).
   - Follow deployment practices ([Running Server](https://gofastmcp.com/deployment/running-server)).
 - **Example**: Rebuild `templates/demo/` with FastMCP’s `@tool` decorator, HTTP transport, and middleware.

 ### 3.2 HTTP as Default, Stdio as Fallback
 - **Objective**: Simplify transport with HTTP, supporting stdio for edge cases.
 - **Approach**:
   - Default to HTTP (`--http` flag, e.g., `mcp run demo --http`).
   - Support stdio via `--stdio` flag for local testing.
   - Ensure Docker deployments use HTTP (port 7071).
 - **Rationale**: HTTP is scalable, Docker-friendly, and covers local/remote use cases. Stdio is niche and complex.

 ### 3.3 Docker Networking
 - **Objective**: Simplify Docker management.
 - **Approach**:
   - Create a Docker network (`mcp-platform`) for all deployments.
   - Use container names as path suffixes (e.g., `http://mcp.local:7071/demo`).
   - CLI command: `mcp deploy demo --docker --http` creates/joins network.
 - **Example**: `docker network create mcp-platform; docker run --network mcp-platform --name demo -p 7071:7071 data-everything/demo-mcp-server`.

 ### 3.4 CLI Enhancements
 - **Objective**: Make CLI discoverable and user-friendly.
 - **Approach**:
   - Extend `mcp config demo` to show all options, including double-underscore notation (e.g., `--config security__api_key=abc`, `--env MCP_API_KEY=abc`, `security__api_key`).
   - Add `mcp tools demo` to list tools (e.g., `say_hello`, `get_server_info`) using `TemplateDiscovery` and FastMCP client.
   - Add `mcp connect demo --llm <llm>` to show integration code for Claude, OpenAI, VS Code, async functions.
   - Use FastMCP CLI patterns for consistency.
 - **Example**:
   ```bash
   mcp config demo
   # Output: --config hello_from=value, --env MCP_HELLO_FROM=value, --config demo__hello_from=value
   mcp tools demo
   # Output: say_hello, get_server_info
 3.5 Demo Template Consistency
 Objective: Ensure the demo template is a model for future templates.
 Approach:
 Create BaseMCPServer in mcp_template/base.py for common functionality (e.g., config, middleware).
 Use TemplateDiscovery for template/tool discovery.
 Create a local FastMCP client for tool discovery (e.g., client.get_tools()).
 Update mcp create demo to generate consistent boilerplate.
 3.6 Code Organization
 Objective: Follow best practices for modularity and testability.
 Approach:
 Demo template: templates/demo/ with config.py, server.py, tools.py, tests/.
 Common code: mcp_template/ with cli.py, discovery.py, base.py.
 Tests: Template tests in templates/demo/tests/, common/integration tests in tests/.
 Example structure:
 mcp-server-templates/
 ├── mcp_template/
 │   ├── __init__.py
 │   ├── cli.py
 │   ├── discovery.py
 │   ├── base.py
 │   └── utils.py
 ├── templates/
 │   ├── demo/
 │   │   ├── __init__.py
 │   │   ├── config.py
 │   │   ├── server.py
 │   │   ├── tools.py
 │   │   └── tests/
 │   │       ├── test_server.py
 │   │       ├── test_tools.py
 ├── tests/
 │   ├── integration/
 │   │   └── test_demo.py
 │   ├── unit/
 │   │   └── test_discovery.py
 ├── Dockerfile
 ├── requirements.txt
 └── docs/
     ├── templates/
     │   ├── demo.md
     └── integration.md
 3.7 Testing
 Objective: Ensure robust tests for the demo template.
 Approach:
 Demo tests in templates/demo/tests/ (e.g., test_say_hello.py).
 Common/integration tests in tests/ (e.g., test_demo.py).
 Use FastMCP’s testing tools.
 Run tests in Docker.
 3.8 Documentation
 Objective: Provide clear, auto-generated docs.
 Approach:
 Extend doc generator to include config options (e.g., --config hello_from, --config demo__hello_from) and tools.
 Add integration guides for Claude, OpenAI, VS Code, async functions in docs/integration.md.
 Example: docs/templates/demo.md:
 ## Demo Template
 - Config: `--config hello_from=value`, `--env MCP_HELLO_FROM=value`, `--config demo__hello_from=value`
 - Tools: `say_hello`, `get_server_info`
 - Integration:
   ```python
   from fastmcp.client import FastMCPClient
   client = FastMCPClient(endpoint="http://localhost:7071/demo")
   greeting = client.call("say_hello", name="Alice")

 3.9 Strategy Updates
 Objective: Keep the strategy current.
 Approach:
 Update docs/strategy.md for changes (e.g., demo-only focus, new FastMCP features).
 Review before development cycles.
 4. Success Metrics
 User Experience: Deploy and connect demo template in <7 minutes.
 Scalability: Handle 1,000+ requests/day with <200ms latency (HTTP, Docker).
 Reliability: 100% test coverage for demo template.
 Accessibility: CLI supports technical users; future dashboard supports non-technical users.
 5. Risks and Mitigations
 Risk: FastMCP updates break compatibility.
 Mitigation: Pin fastmcp>=2.10.0, monitor releases.
 Risk: HTTP-only focus alienates stdio users.
 Mitigation: Support stdio via --stdio flag.
 Risk: Demo refactor doesn’t scale to other templates.
 Mitigation: Use BaseMCPServer and modular design.
 6. Next Steps
 Refactor demo template with FastMCP, HTTP default, Docker.
 Enhance CLI for config (double-underscore), tools, and integrations.
 Implement Docker networking.
 Organize demo code and tests.
 Update doc generator and integration guides.
 Validate demo template before scaling to others.
 Update docs/strategy.md post-refactor.
d d  9uu89uhhhbbbbbbbbbbbbbbbbbbhuuuuuuuuuuuuyu8y89u689ut89u0
