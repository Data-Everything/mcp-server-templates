# MCP Server Templates

[![Version](https://img.shields.io/pypi/v/mcp-templates.svg)](https://pypi.org/project/mcp-templates/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-templates.svg)](https://pypi.org/project/mcp-templates/)
[![License](https://img.shields.io/badge/License-Elastic%202.0-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/discord/XXXXX?color=7289da&logo=discord&logoColor=white)](https://discord.gg/55Cfxe9gnr)

<div align="center">

**[📚 Documentation](https://data-everything.github.io/mcp-server-templates/)** • **[💬 Discord Community](https://discord.gg/55Cfxe9gnr)** • **[🚀 Quick Start](#-installation)**

</div>

> **Production-ready Model Context Protocol (MCP) server templates with zero-configuration deployment**

Deploy, manage, and scale MCP servers instantly with Docker containers, comprehensive CLI tools, and flexible configuration options. Built for developers who want to focus on AI integration, not infrastructure setup.

## 📢 Announcements
- **🚀 Version 0.3.0 Released!**: New features, bug fixes, and performance improvements.
- **🔧 CLI Shorthand Alias**: Introducing new `mcpt` alias for faster access to all CLI commands with full backward compatibility.

## 🌟 Why MCP Server Templates?

| Traditional MCP Setup | With MCP Templates |
|----------------------|-------------------|
| ❌ Complex server configuration | ✅ One-command deployment |
| ❌ Docker knowledge required | ✅ Zero configuration needed |
| ❌ Manual tool discovery | ✅ Automatic tool detection |
| ❌ Environment setup headaches | ✅ Pre-built, tested containers |
| ❌ No deployment management | ✅ Full lifecycle management |

**Perfect for:** AI developers, data scientists, DevOps teams, and anyone building with MCP who wants infrastructure that "just works".

## ⚡ Features

Get ready to supercharge your MCP journey! The MCP Platform is packed with electrifying features that make server deployment a thrill ride:

### 🚀 Current Features

- **🖱️ One-Click Docker Deployment**: Launch MCP servers instantly with pre-built templates—no hassle, just pure speed.
- **🔎 Smart Tool Discovery**: Automatically finds and showcases every tool your server can offer. No more guesswork!
- **💻 Slick CLI Management**: Command-line magic for easy, powerful control over all deployments.
- **🤝 Bring Your Own MCP Server**: Plug in your own MCP server and run it on our network — with limited features!
- **🐳 Effortless Docker Image Integration**: Add any existing MCP Docker image to the templates library with minimal setup and unlock all the platform’s cool benefits.
- **⚡ Boilerplate Template Generator**: Instantly create new MCP server projects with a CLI-powered generator—kickstart your next big idea!
- **🛠️ Multiple Ways to Set Configuration**: Flex your setup with config via JSON, YAML, environment variables, CLI config, or CLI override options—total flexibility for every workflow!
- **🔧 Comprehensive CLI Tools**: From deployment to tool execution, manage everything with a single command-line interface.
- **📦 Template Library**: Access a growing library of ready-to-use templates for common use cases.

### 🌈 Planned Features

- **🦸 MCP Sidekick (Coming Soon)**: Your friendly AI companion, making every MCP server compatible with any AI tool or framework.
- **🛸 Kubernetes Support**: Deploy to Kubernetes clusters with ease, scaling your MCP servers effortlessly.

**Release Timeline:** All this and more dropping mid-August 2025—don’t miss out!

Want the full scoop? [Check out the docs for more features & details!](https://data-everything.github.io/mcp-server-templates/)

---

## 🚀 How It Works

**Architecture Overview:**

```
┌────────────┐      ┌────────────────────┐      ┌────────────────────────────┐
│  CLI Tool  │──▶──▶│ DeploymentManager  │──▶──▶│ Backend (Docker/K8s/Mock)  │
└────────────┘      └────────────────────┘      └────────────────────────────┘
      │                    │                           │
      ▼                    ▼                           ▼
  TemplateDiscovery   Template Config           Container/Pod/Mock
      │                    │
      ▼                    ▼
  ConfigMapping      Environment Variables
```

**Configuration Flow:**
1. **Template Defaults** → 2. **Config File** → 3. **CLI Options** → 4. **Environment Variables**

- **CLI Tool**: `mcp-template` or `mcpt` with comprehensive config support
- **DeploymentManager**: Unified interface for Docker, Kubernetes, or Mock backends
- **TemplateDiscovery**: Auto-discovers templates with config schema validation
- **ConfigMapping**: Generic mapping system supporting nested JSON/YAML configs
- **Multi-source Configuration**: File-based, CLI options, and environment variables

---
## 📚 Installation
There are many ways to install the MCP Server Templates CLI tool:

### PyPI Package
Install the MCP Server Templates CLI tool via PyPI:

```bash
pip install mcp-templates
```

### Docker Image
Run the MCP Server Templates CLI tool using Docker:

```bash
docker run --privileged --rm -it dataeverything/mcp-server-templates:latest
# This requires --privileged to access as it runs podman as alaias to docker. Check https://hub.docker.com/r/mgoltzsche/podman for more details.
```

### Source Code
Clone the repository and install dependencies:

```bash
git clone https://github.com/DataEverything/mcp-server-templates.git
cd mcp-server-templates
pip install -r requirements.txt
```

---
## 📦 Template Structure

Each template must include:

- `template.json` — Metadata and config schema with environment mappings
- `Dockerfile` — Container build instructions
- `README.md` — Usage and description
- (Optional) `USAGE.md`, `requirements.txt`, `src/`, `tests/`, `config/`

**Example `template.json`:**
```json
{
  "name": "File Server MCP",
  "description": "Secure file system access for AI assistants...",
  "version": "1.0.0",
  "author": "Data Everything",
  "category": "File System",
  "tags": ["filesystem", "files", "security"],
  "docker_image": "dataeverything/mcp-demo",
  "docker_tag": "latest",
  "ports": {
    "8080": 8080
  },
  "command": ["python", "server.py"],
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"],
    "port": 8080
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "allowed_directories": {
        "type": "array",
        "env_mapping": "MCP_ALLOWED_DIRS",
        "env_separator": ":",
        "default": ["/data"],
        "description": "Allowed directories for file access"
      },
      "read_only_mode": {
        "type": "boolean",
        "env_mapping": "MCP_READ_ONLY",
        "default": false,
        "description": "Enable read-only mode"
      },
      "log_level": {
        "type": "string",
        "env_mapping": "MCP_LOG_LEVEL",
        "default": "info",
        "description": "Logging level (debug, info, warning, error)"
      }
    },
    "required": ["allowed_directories"]
  }
}
```

---
## 🛠️ CLI Usage

The MCP Template CLI provides two interfaces for managing MCP server templates:

### Command Overview

| Category | Command | Description |
|----------|---------|-------------|
| **General** | `mcp-template list` | List all available templates |
| | `mcp-template create <template-id>` | Create new template with generator |
| **Deployment** | `mcp-template deploy <template>` | Deploy template with Docker |
| | `mcp-template stop <deployment>` | Stop running deployment |
| | `mcp-template logs <deployment>` | View deployment logs |
| | `mcp-template shell <deployment>` | Open shell in deployment container |
| | `mcp-template cleanup [deployment]` | Clean up deployments |
| **Configuration** | `mcp-template config <template>` | Show template configuration options |
| **Integration** | `mcp-template connect <deployment>` | Show integration examples |
| | `mcp-template run` | Run template with transport options |
| **Interactive** | `mcp-template interactive` | Start interactive CLI mode |
| **Deprecated** | ~~`mcp-template tools`~~ | ❌ Use `interactive` mode instead |
| | ~~`mcp-template discover-tools`~~ | ❌ Use `interactive` mode instead |
| | ~~`mcp-template run-tool`~~ | ❌ Use `interactive` mode with `call` command instead |

### Getting Started with CLI

The MCP Template CLI provides comprehensive tools for deploying and managing MCP server templates:

#### Basic Workflow

```bash
# 1. List available templates
mcp-template list

# 2. Deploy a template
mcp-template deploy github

# 3. Check deployment logs
mcp-template logs github

# 4. Open interactive shell in deployment
mcp-template shell github

# 5. Use interactive mode for deployment management and tool execution
mcp-template interactive
# Interactive mode provides:
# - List and manage deployments
# - Discover available tools from MCP servers
# - Execute tools directly from command line
# - Real-time interaction with deployed servers

# 6. Clean up when done
mcp-template cleanup github
```

#### Configuration Management

```bash
# Show template configuration options
mcp-template config github

# Connect to deployed template (show integration examples)
mcp-template connect github

# Use interactive mode for tool discovery and execution
mcp-template interactive
# In interactive mode:
# - Discover available tools
# - Execute tools directly
# - Configure templates interactively
```

#### Advanced Usage

```bash
# Run template with specific transport
mcp-template run --transport http --port 8080

# Connect to deployed template
mcp-template connect github

# Deploy with cleanup of old instances
mcp-template deploy github --cleanup

# View comprehensive logs with follow
mcp-template logs github --follow
```

### Template Discovery and Management

**Available Templates:**
```bash
# List all available templates
mcp-template list
# Outputs: demo, github, gitlab, zendesk

# Create new template using generator
mcp-template create my-custom-server
```
- **Fallback strategies**: Docker → Static JSON → Template capabilities
- **Caching**: Caches discovery results for performance

### Configuration Options

**1. Check Template Configuration:**
```bash
# View template configuration options
mcp-template config demo

# Shows config schema properties, required fields, defaults
```

**2. Deploy with Config File:**
```bash
# JSON config file
mcp-template deploy demo --config-file ./config.json

# YAML config file  
mcp-template deploy demo --config-file ./config.yml
```

**3. Deploy with CLI Configuration Options:**

There are **two types** of CLI configuration:

- **`--config`**: For `config_schema` properties (becomes environment variables)
- **`--override`**: For template data modifications (modifies template structure directly)

```bash
# Configuration schema properties (recommended for server settings)
mcp-template deploy demo \
  --config read_only_mode=true \
  --config max_file_size=50 \
  --config log_level=debug

# Template overrides (modifies template structure)
mcp-template deploy demo \
  --override name="Custom File Server" \
  --override description="My custom file server"
```

### Interactive CLI Mode

The interactive CLI provides comprehensive deployment management and MCP server interaction:

```bash
# Start interactive CLI
mcp-template interactive
```

**Key Features:**
- **Deployment Management**: List, monitor, and manage running deployments
- **Tool Discovery**: Discover available tools from deployed MCP servers
- **Tool Execution**: Execute tools directly from the command line
- **Real-time Interaction**: Interactive session with deployed servers
- **Configuration Management**: Configure templates and servers dynamically

**Use Cases:**
- Manage multiple deployments from a single interface
- Discover what tools are available in your MCP servers
- Execute MCP server tools without writing integration code
- Debug and test MCP server functionality
- Interactive exploration of server capabilities

**Benefits:**
- **Streamlined workflow**: No need to retype `mcp-template` for each command
- **Server discovery**: Automatically find and interact with deployed servers
- **Tool execution**: Direct command-line access to MCP server tools
- **Session persistence**: Maintain context across multiple operations

### Advanced Usage & Examples

**1. Tool Discovery Workflows:**
```bash
# Discover tools without credentials (uses dummy credentials automatically)
mcp-template tools github

# Discover tools with custom Docker image
mcp-template discover-tools custom/mcp-server:latest --timeout 30

# Force server discovery (skip static fallback)
mcp-template tools github --force-server

# Show integration examples for discovered tools
mcp-template integration-examples github
```

**2. Complex Configuration Scenarios:**
```bash
# Deploy with multiple config sources (priority: CLI > file > defaults)
mcp-template deploy zendesk \
  --config-file ./zendesk-config.yaml \
  --config subdomain=mycompany \
  --config email=admin@company.com \
  --env ZENDESK_API_TOKEN=xyz123

# Use double underscore notation for nested config
mcp-template deploy demo \
  --config server__port=8080 \
  --config server__host=0.0.0.0 \
  --config limits__max_file_size=100MB
```

---
## 🔧 Development

### Building from Source

```bash
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Lint code
make lint

# Format code
make format
```

### Creating Templates

```bash
# Use the interactive template generator
mcp-template create my-custom-server

# Or manually create template structure:
mkdir templates/my-server
cd templates/my-server
# Create template.json, Dockerfile, README.md
```

---
## 📚 Documentation

### Core Documentation

### Stdio Tool Execution

For stdio transport MCP servers, use the `run-tool` command to execute individual tools:

**1. List Available Tools:**
```bash
# Show all tools available in a template
mcp-template tools github
mcp-template tools filesystem
mcp-template tools --image custom/mcp-server:latest

# List tools with configuration
mcp-template tools github --config github_token=your_token
```

**2. Run Individual Tools:**
```bash
# Basic tool execution
mcp-template run-tool github search_repositories \
  --args '{"query": "mcp server", "per_page": 5}'

# Tool execution with authentication
mcp-template run-tool github create_issue \
  --args '{"owner": "user", "repo": "test", "title": "Bug report", "body": "Description"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Tool execution with configuration
mcp-template run-tool filesystem read_file \
  --args '{"path": "/data/example.txt"}' \
  --config allowed_directories='["/data", "/workspace"]' \
  --config read_only=true
```

**3. Complex Tool Arguments:**
```bash
# JSON arguments for complex data structures
mcp-template run-tool github create_pull_request \
  --args '{
    "owner": "user",
    "repo": "project", 
    "title": "Feature: Add new functionality",
    "head": "feature-branch",
    "base": "main",
    "body": "This PR adds amazing new features:\n- Feature 1\n- Feature 2"
  }' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Multiple configuration options
mcp-template run-tool database query \
  --args '{"sql": "SELECT * FROM users LIMIT 10"}' \
  --config connection_string="postgresql://localhost:5432/mydb" \
  --config timeout=30 \
  --env DB_PASSWORD=secret
```

**4. Working with Different Templates:**
```bash
# GitHub API tools
mcp-template run-tool github search_users --args '{"q": "mcp"}'
mcp-template run-tool github get_file_contents --args '{"owner": "user", "repo": "project", "path": "README.md"}'

# Filesystem tools  
mcp-template run-tool filesystem list_directory --args '{"path": "/data"}'
mcp-template run-tool filesystem create_file --args '{"path": "/data/test.txt", "content": "Hello World"}'

# Custom MCP servers
mcp-template run-tool my-custom-server my_tool --args '{"param": "value"}'
```

### Configuration File Examples

**JSON Configuration (`config.json`):**
```json
{
  "security": {
    "allowedDirs": ["/data", "/workspace"],
    "readOnly": false,
    "maxFileSize": 100,
    "excludePatterns": ["**/.git/**", "**/node_modules/**"]
  },
  "logging": {
    "level": "info",
    "enableAudit": true
  },
  "performance": {
    "maxConcurrentOperations": 10,
    "timeoutMs": 30000
  }
}
```

**YAML Configuration (`config.yml`):**
```yaml
security:
  allowedDirs:
    - "/data"
    - "/workspace"
  readOnly: false
  maxFileSize: 100
  excludePatterns:
    - "**/.git/**"
    - "**/node_modules/**"

logging:
  level: info
  enableAudit: true

performance:
  maxConcurrentOperations: 10
  timeoutMs: 30000
```

---
## 🐳 Docker Images & Backends

### Supported Backends

- **Docker** (default): Uses local Docker daemon or nerdctl/containerd
- **Kubernetes**: Coming soon - will deploy to K8s clusters
- **Mock**: For testing and development

### Image Management

Templates automatically build and tag images as:
- Format: `dataeverything/mcp-{template-name}:latest`
- Custom images: Specify in `template.json` with `docker_image` field
- Auto-pull: Images are pulled automatically during deployment

---
## 🏗️ Architecture & Extensibility

### Core Components

- **Backend Abstraction**: Easily extend with Kubernetes, cloud providers
- **CLI + Library**: Use as command-line tool or import as Python library
- **Platform Integration Ready**: Same codebase powers MCP Platform commercial UI
- **Configuration System**: Generic mapping supporting any template structure
- **Type Conversion**: Automatic conversion based on JSON schema types

### Adding New Templates

1. Create `templates/{name}/` directory
2. Add `template.json` with config schema and environment mappings
3. Add `Dockerfile` for container build
4. Test with `mcp-template {name} --show-config`

### Adding New Backends

1. Inherit from base deployment service interface
2. Implement `deploy_template()`, `list_deployments()`, etc.
3. Register in `DeploymentManager._get_deployment_backend()`

---
## 🧪 Testing & Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test categories
pytest tests/test_configuration.py  # Configuration system tests
pytest tests/test_deployment_*.py   # Deployment tests
pytest tests/test_all_templates.py  # Template validation tests
```

### Test Configuration Files

Sample configuration files are available in `examples/config/`:
- `demo-config.json`: Example demo configuration
- Additional template configs as they're added

### Development Setup

```bash
# Clone and setup
git clone <repo-url>
cd mcp-server-templates
pip install -e .

# Run in development mode
mcp-template list
```

### Testing

```bash
# Run all tests
make test

# Run tests for all templates
make test-templates

# Run tests for a specific template
make test-template TEMPLATE=demo

# Run unit tests only
make test-unit

# Run integration tests
make test-integration
```

### Documentation

```bash
# Build documentation
make docs

# Serve documentation locally
make docs-serve

# Clean documentation build
make docs-clean
```

---
## 📚 Documentation Hub

### Core Documentation

- **[Documentation Index](https://data-everything.github.io/mcp-server-templates/)**: Central hub for all documentation
- **[Configuration Strategy](docs/CONFIGURATION_FINAL_RECOMMENDATIONS.md)**: Configuration design decisions
- **[Template Development Guide](docs/template-development-guide.md)**: Creating new templates
- **[Testing Guide](docs/TESTING.md)**: Testing strategies and tools

### Template-Specific Docs

Each template includes:
- `README.md`: Overview and basic usage
- `USAGE.md`: Detailed configuration and examples
- `tests/`: Template-specific test suites

---
## 🚀 Getting Started

### Quick Start

```bash
# 1. Install from PyPI
pip install mcp-templates

# 2. List available templates
mcp-template list

# 3. Deploy a template with defaults
mcp-template deploy github

# 4. View deployment logs
mcp-template logs github

# 5. Use interactive mode for tool execution
mcp-template interactive

# 6. Clean up when done
mcp-template cleanup github
```

### Template Discovery

```bash
# List all available templates
mcp-template create --help

# Create new template interactively
mcp-template create my-custom-template
```

---
## License

This project is licensed under the **Elastic License 2.0**.

You may use, deploy, and modify it freely in your organization or personal projects.
You **may not** resell, rehost, or offer it as a commercial SaaS product without a commercial license.

See [LICENSE](./LICENSE) and [ATTRIBUTION](./ATTRIBUTION.md) for details.

---
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

---
## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Data-Everything/mcp-server-templates/discussions)
- **Discord Community**: [Join our Discord server](https://discord.gg/55Cfxe9gnr)
- **Documentation**: [Read the Docs](https://data-everything.github.io/mcp-server-templates/)
