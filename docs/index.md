# MCP Server Templates

**Production-ready deployment system for Model Context Protocol (MCP) servers with zero-configuration deployment, comprehensive tool discovery, and enterprise-grade management capabilities.**

# MCP Server Templates Documentation

[![Version](https://img.shields.io/pypi/v/mcp-templates.svg)](https://pypi.o- **💬 Discord Community**: [Join our Discord server](https://discord.gg/55Cfxe9gnr)g/project/mcp-templates/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-templates.svg)](https://pypi.org/project/mcp-templates/)
[![License](https://img.shields.io/badge/License-Elastic%202.0-blue.svg)](/LICENSE)
[![Discord](https://img.shields.io/discord/XXXXX?color=7289da&logo=discord&logoColor=white)](https://discord.gg/55Cfxe9gnr)

> **Production-ready Model Context Protocol (MCP) server templates with zero-configuration deployment**

Deploy, manage, and scale MCP servers instantly with Docker containers, comprehensive CLI tools, and flexible configuration options.

## 🚀 Quick Navigation

<div class="grid cards" markdown>

-   :octicons-zap-16: **[Getting Started](getting-started/installation.md)**

    Install MCP Templates and deploy your first server in under 2 minutes

-   :octicons-terminal-16: **[CLI Reference](cli/index.md)**

    Complete command reference for the `mcp-template` CLI tool

-   :octicons-package-16: **[Server Templates](server-templates/index.md)**

    Browse available templates: GitHub, Zendesk, GitLab, Demo, and more

-   :octicons-book-16: **[User Guide](user-guide/)**

    In-depth guides for configuration, deployment, and management

</div>

## ⚡ What is MCP Templates?

MCP Server Templates is a **self-hosted deployment system** that enables rapid deployment, management, and scaling of Model Context Protocol servers on your own infrastructure. 

### Key Benefits

| Traditional MCP Setup | With MCP Templates |
|----------------------|-------------------|
| ❌ Complex server configuration | ✅ One-command deployment |
| ❌ Docker knowledge required | ✅ Zero configuration needed |
| ❌ Manual tool discovery | ✅ Automatic tool detection |
| ❌ Environment setup headaches | ✅ Pre-built, tested containers |
| ❌ No deployment management | ✅ Full lifecycle management |

### Core Features

- **🔧 Zero Configuration**: Deploy MCP servers with sensible defaults
- **🐳 Docker-Based**: Containerized deployments for consistency and security
- **🛠️ Tool Discovery**: Automatic detection of available tools and capabilities
- **📱 Interactive CLI**: Streamlined command-line interface for all operations
- **🔄 Lifecycle Management**: Deploy, configure, monitor, and cleanup with ease
- **🎯 Multiple Templates**: Pre-built servers for GitHub, Zendesk, GitLab, and more

## 📋 Available Templates

| Template | Description | Status |
|----------|-------------|--------|
| **demo** | Simple demonstration server | ✅ Available |
| **github** | GitHub repository management | ✅ Available |
| **gitlab** | GitLab integration server | ✅ Available |
| **zendesk** | Customer support integration | ✅ Available |

## � What’s Inside

Welcome to the MCP Platform—where server deployment meets pure excitement! Here’s what makes this project a must-have for every AI builder:

### ⚡ Features (Mid-August 2025 Release)

#### 🚀 Current Features

- **🖱️ One-Click Docker Deployment**: Launch MCP servers instantly with pre-built templates—no hassle, just pure speed.
- **🔎 Smart Tool Discovery**: Automatically finds and showcases every tool your server can offer. No more guesswork!
- **💻 Slick CLI Management**: Command-line magic for easy, powerful control over all deployments.
- **🤝 Bring Your Own MCP Server**: Plug in your own MCP server and run it on our network—even with limited features!
- **🐳 Effortless Docker Image Integration**: Add any existing MCP Docker image to the templates library with minimal setup and unlock all the platform’s cool benefits.
- **⚡ Boilerplate Template Generator**: Instantly create new MCP server projects with a CLI-powered generator—kickstart your next big idea!
- **🛠️ Multiple Ways to Set Configuration**: Flex your setup with config via JSON, YAML, environment variables, CLI config, or CLI override options—total flexibility for every workflow!

#### 🌈 Planned Features

- **🦸 MCP Sidekick (Coming Soon)**: Your friendly AI companion, making every MCP server compatible with any AI tool or framework.
- **🛸 Kubernetes Support**: Deploy to Kubernetes clusters with ease, scaling your MCP servers effortlessly.

**Release Timeline:** All this and more dropping mid-August 2025—don’t miss out!

Ready to dive in? [Get Started with the README!](../../README.md)

## �🌟 MCP Platform - Managed Cloud Solution

Looking for enterprise deployment without infrastructure management? **[MCP Platform](https://mcp-platform.dataeverything.ai/)** offers:

- ✨ **One-click deployment** - Deploy any MCP server template instantly
- 🛡️ **Enterprise security** - SOC2, GDPR compliance with advanced security controls
- 📊 **Real-time monitoring** - Performance metrics, usage analytics, and health dashboards
- 🔧 **Custom development** - We build proprietary MCP servers for your specific needs
- 💼 **Commercial support** - 24/7 enterprise support with SLA guarantees
- 🎯 **Auto-scaling** - Dynamic resource allocation based on demand
- 🔐 **Team management** - Multi-user access controls and audit logging

**Ready for production?** [Get started with MCP Platform →](https://mcp-platform.dataeverything.ai/)

---

## Open Source Self-Hosted Deployment

This repository provides comprehensive tools for self-managing MCP server deployments on your own infrastructure.

### 🚀 Key Features

- **🎯 Zero Configuration Deployment** - Deploy templates with a single command
- **🔍 Advanced Tool Discovery** - Automatic detection of MCP server capabilities using official MCP protocol
- **📦 Pre-built Templates** - Production-ready templates for file operations, databases, APIs, and more
- **🔧 Flexible Configuration** - Multi-source configuration with environment variables, CLI options, and files
- **🐳 Docker-First Architecture** - Container-based deployments with proper lifecycle management
- **📋 Rich CLI Interface** - Beautiful command-line interface with comprehensive help and examples
- **🧪 Template Development Tools** - Complete toolkit for creating and testing custom templates
- **📊 Monitoring & Management** - Real-time status monitoring, log streaming, and health checks
- **🔗 Integration Examples** - Ready-to-use code for Claude Desktop, VS Code, Python, and more

### 🎯 Quick Start

#### Installation

```bash
# Install from PyPI (recommended)
pip install mcp-templates

# Verify installation
mcp-template --version
```

#### Deploy Your First Template

```bash
# List available templates
mcp-template list

# Deploy demo server
mcp-template deploy demo

# Discover available tools
mcp-template tools demo

# Get integration examples
mcp-template connect demo --llm claude
```

#### Integration with Claude Desktop

```bash
# Get container name
mcp-template list

# Update Claude Desktop config
mcp-template connect demo --llm claude
```

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

### 📚 Documentation

#### 🚀 Getting Started
- **[Installation Guide](getting-started/installation.md)** - Setup and initial configuration
- **[Quick Start Tutorial](getting-started/quickstart.md)** - Deploy your first MCP server
- **[Basic Concepts](getting-started/concepts.md)** - Understanding templates, deployments, and tools

#### 📖 User Guide
- **[Template Usage](user-guide/templates.md)** - Working with pre-built templates
- **[Configuration Management](user-guide/configuration.md)** - Advanced configuration patterns
- **[Stdio Tool Execution](stdio-tool-execution.md)** - Interactive tool execution for stdio MCP servers
- **[Integration Patterns](user-guide/integration.md)** - Connect to LLMs and frameworks
- **[Monitoring & Management](user-guide/monitoring.md)** - Production deployment management

#### 🛠️ CLI Reference
- **[Command Overview](cli/index.md)** - Complete CLI documentation
- **[deploy](cli/deploy.md)** - Deploy HTTP transport templates with configuration options
- **[run-tool](stdio-tool-execution.md#basic-usage)** - Execute tools from stdio MCP servers
- **[tools](cli/tools.md)** - Discover and analyze MCP server capabilities
- **[tools](cli/tools.md)** - List tools from templates OR discover from Docker images
- ~~**[discover-tools](cli/discover-tools.md)**~~ - **DEPRECATED**: Use `tools --image` instead
- **[connect](cli/connect.md)** - Generate integration examples for LLMs
- **[config](cli/config.md)** - View template configuration options
- **[list](cli/list.md)** - List templates and deployments
- **[logs](cli/logs.md)** - Monitor deployment logs
- **[status](cli/status.md)** - Check deployment health

#### 🔧 Development
- **[Creating Templates](guides/creating-templates.md)** - Build custom MCP server templates
- **[Template Development Guide](guides/development.md)** - Advanced template development
- **[Template Discovery System](template-discovery.md)** - Understanding template discovery architecture
- **[Tool Discovery System](tool-discovery.md)** - Understanding tool discovery architecture
- **[Testing & Validation](guides/testing.md)** - Test templates and deployments
- **[Contributing](guides/contributing.md)** - Contribute to the project

#### 🏗️ System Architecture
- **[Architecture Overview](development/architecture.md)** - System design and components
- **[Backend Abstraction](development/backends.md)** - Docker, Kubernetes, and custom backends
- **[Template System](development/templates.md)** - Template structure and lifecycle
- **[API Reference](api/)** - Complete API documentation

### 🎯 Use Cases

#### File Operations
```bash
# Deploy secure file server
mcp-template deploy file-server \
  --config security__allowed_dirs='["/data", "/workspace"]' \
  --config security__read_only=false

# Connect to Claude Desktop for file operations
mcp-template connect file-server --llm claude
```

#### Database Integration
```bash
# Deploy PostgreSQL MCP server
mcp-template deploy postgres-server \
  --config database__host=localhost \
  --config database__name=mydb \
  --env POSTGRES_PASSWORD=secret

# Generate Python integration code
mcp-template connect postgres-server --llm python
```

#### API Integration
```bash
# Deploy REST API integration server
mcp-template deploy api-server \
  --config api__base_url=https://api.example.com \
  --config api__auth_token=$API_TOKEN

# Test with cURL
mcp-template connect api-server --llm curl
```

### 🔍 Tool Discovery

**Automatic MCP Protocol Discovery:**
```bash
# Discover tools from any MCP-compliant Docker image
mcp-template tools --image mcp/filesystem /tmp

# Rich formatted output shows all capabilities:
✅ Discovered 11 tools via docker_mcp_stdio
- read_file: Read complete file contents
- write_file: Create or overwrite files
- list_directory: List directory contents
- create_directory: Create directories
- ... and 7 more tools
```

**Integration Ready:**
```bash
# Get ready-to-use integration code
mcp-template tools demo --format json
mcp-template connect demo --llm vscode
```

### 📊 Available Templates

| Template | Description | Use Cases |
|----------|-------------|-----------|
| **demo** | Basic greeting and echo server | Learning, testing, examples |
| **file-server** | Secure filesystem operations | Document processing, file management |
| **postgres-server** | PostgreSQL database integration | Data analysis, query execution |
| **api-server** | REST API client with auth | External service integration |
| **mongodb-server** | MongoDB document operations | NoSQL data operations |
| **redis-server** | Redis cache and pub/sub | Caching, real-time messaging |

### 🛠️ System Requirements

- **Operating System**: Linux, macOS, Windows (with WSL2)
- **Docker**: Version 20.10+ (required for container deployments)
- **Python**: Version 3.9+ (for CLI and development)
- **Memory**: 512MB minimum, 2GB recommended
- **Storage**: 1GB minimum for templates and container images

### 🚦 Production Deployment

#### Security Considerations
```bash
# Deploy with security hardening
mcp-template deploy file-server \
  --config security__read_only=true \
  --config security__max_file_size=10 \
  --config logging__enable_audit=true \
  --env MCP_ALLOWED_DIRS='["/secure/data"]'
```

#### Monitoring Setup
```bash
# Health check monitoring
mcp-template list --format json | jq '.summary'

# Log monitoring
mcp-template logs file-server --follow --since 1h
```

#### Backup and Recovery
```bash
# Export deployment configuration
mcp-template status file-server --format json > backup.json

# Cleanup and redeploy
mcp-template cleanup file-server
mcp-template deploy file-server --config-file backup.json
```

### 🤝 Community & Support

- **📖 Documentation**: Comprehensive guides and API reference
- **🐛 Issue Tracker**: [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/Data-Everything/mcp-server-templates/discussions)
- **� Community Slack**: [Join mcp-platform workspace](https://join.slack.com/t/mcp-platform/shared_invite/zt-39z1p559j-8aWEML~IsSPwFFgr7anHRA)
- **�📧 Enterprise Support**: [Contact us](mailto:support@dataeverything.ai) for commercial support

### 🗺️ Roadmap

- **Kubernetes Backend**: Native Kubernetes deployment support
- **Template Marketplace**: Community-driven template sharing
- **GraphQL Integration**: GraphQL API server templates
- **Metrics & Alerting**: Prometheus/Grafana integration
- **Multi-tenant Support**: Isolated deployments for teams
- **Auto-scaling**: Dynamic resource allocation

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Get started today**: Choose between our [managed cloud platform](https://mcp-platform.dataeverything.ai/) for instant deployment or [self-hosted deployment](getting-started/installation.md) for full control.

# Install dependencies
pip install -e .
```

#### Basic Usage

```bash
# List available templates
mcp-template list

# Deploy a template
mcp-template deploy file-server

# View logs
mcp-template logs file-server

```

#### Show Configuration Options

```bash
# View configuration options for any template
mcp-template deploy file-server --show-config

# Deploy with custom configuration
mcp-template deploy file-server --config read_only_mode=true

# Deploy with config file
mcp-template deploy file-server --config-file config.json
```

## Available Templates

Our templates are automatically discovered and validated using the `TemplateDiscovery` utility to ensure only working implementations are listed. This keeps the documentation up-to-date as new templates are added.

*Use `mcp-template list` to see all currently available templates, or visit the [Templates](server-templates/index.md) section for detailed documentation.*

**Popular Templates:**
- **file-server** - Secure filesystem access for AI assistants
- **demo** - Demonstration server with greeting tools
- **github** - GitHub API integration for repository access
- **database** - Database connectivity for SQL operations

## Architecture

The system uses a simple architecture designed for self-hosted deployments:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   CLI Tool  │────│ Template         │────│ Docker Backend      │
│             │    │ Discovery        │    │                     │
│ • Commands  │    │ • Load metadata  │    │ • Container deploy  │
│ • Config    │    │ • Schema validation │  │ • Volume management │
│ • Display   │    │ • Config mapping  │    │ • Health monitoring │
└─────────────┘    └──────────────────┘    └─────────────────────┘
```

**Key Components:**
- **CLI Interface** - Rich command-line interface (`mcp-template`)
- **Template Discovery** - Automatic detection and validation of templates
- **Docker Backend** - Container-based deployment with volume management
- **Configuration System** - Multi-source configuration with type conversion

## Configuration System

Templates support flexible configuration from multiple sources:

**Configuration precedence (highest to lowest):**
1. Environment variables (`--env KEY=VALUE`)
2. CLI configuration (`--config KEY=VALUE`)
3. Configuration files (`--config-file config.json`)
4. Template defaults

**Example configuration:**
```bash
# Using CLI options
mcp-template deploy file-server \
  --config read_only_mode=true \
  --config max_file_size=50 \
  --config log_level=debug

# Using environment variables
mcp-template deploy file-server \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50

# Using config file
mcp-template deploy file-server --config-file production.json
```

## Template Development

Create custom MCP server templates:

```bash
# Interactive template creation
mcp-template create my-custom-server

# Follow prompts to configure:
# - Template metadata
# - Configuration schema
# - Docker setup
# - Documentation
```

Each template includes:
- `template.json` - Metadata and configuration schema
- `Dockerfile` - Container build instructions
- `README.md` - Template documentation
- `docs/index.md` - Documentation site content
- `src/` - Implementation code

## Documentation

- **[Templates](server-templates/index.md)** - Available templates and their configuration
- **[Getting Started](getting-started/quickstart.md)** - Installation and first deployment
- **[Guides](guides/creating-templates.md)** - Advanced usage and template development
- **[Development](development/architecture.md)** - Technical architecture and development

## Community

- **[GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/Data-Everything/mcp-server-templates/discussions)** - Community questions and sharing
- **Contributing** - See our [contribution guidelines](guides/contributing.md)

## Commercial Services

Need help with custom MCP servers or enterprise deployment?

**[MCP Platform](https://mcp-platform.dataeverything.ai/)** offers:
- Custom MCP server development
- Enterprise hosting and support
- Professional services and consulting

📧 **Contact us:** [tooling@dataeverything.ai](mailto:tooling@dataeverything.ai)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Data-Everything/mcp-server-templates/blob/main/LICENSE) file for details.

---

*MCP Server Templates - Deploy AI-connected services on your own infrastructure.*
