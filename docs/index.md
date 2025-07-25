# MCP Server Templates

**Open-source deployment system for Model Context Protocol (MCP) server templates with zero-configuration deployment.**

MCP Server Templates is a self-hosted deployment system that lets you quickly deploy, manage, and extend MCP servers on your own infrastructure. It provides a unified CLI tool, flexible configuration system, and pre-built templates for common use cases.

## 🌟 MCP Platform - Commercial Hosted Solution

Looking for a one-click managed deployment? **[MCP Platform](https://mcp-platform.dataeverything.ai/)** offers:

- ✨ **One-click deployment** - Deploy any MCP server template instantly
- 🛡️ **Enterprise security** - SOC2, GDPR compliance and advanced security controls
- 📊 **Monitoring & analytics** - Real-time performance metrics and usage insights
- 🔧 **Custom templates** - We build proprietary MCP servers for your specific needs
- 💼 **Commercial support** - 24/7 enterprise support and SLA guarantees

**Ready for production?** [Get started with MCP Platform →](https://mcp-platform.dataeverything.ai/)

---

## Open Source Self-Hosted Deployment

This repository provides the open-source tools for self-managing MCP server deployments on your own infrastructure.

### Key Features

- **🚀 Zero Configuration Deployment** - Deploy templates with a single command
- **📦 Pre-built Templates** - Ready-to-use templates for common MCP use cases
- **🔧 Flexible Configuration** - Multi-source configuration with automatic type conversion
- **🐳 Docker Backend** - Container-based deployments with volume management
- **📋 Rich CLI Interface** - Beautiful command-line interface with progress indicators
- **🧪 Template Development** - Tools for creating and testing custom templates

### Quick Start

#### Installation

```bash
# Clone the repository
git clone https://github.com/Data-Everything/mcp-server-templates
cd mcp-server-templates

# Install dependencies
pip install -e .
```

#### Basic Usage

```bash
# List available templates
python -m mcp_template list

# Deploy a template
python -m mcp_template deploy file-server

# View logs
python -m mcp_template logs file-server

```

#### Show Configuration Options

```bash
# View configuration options for any template
python -m mcp_template deploy file-server --show-config

# Deploy with custom configuration
python -m mcp_template deploy file-server --config read_only_mode=true

# Deploy with config file
python -m mcp_template deploy file-server --config-file config.json
```

## Available Templates

Our templates are automatically discovered and validated using the `TemplateDiscovery` utility to ensure only working implementations are listed. This keeps the documentation up-to-date as new templates are added.

*Use `python -m mcp_template list` to see all currently available templates, or visit the [Templates](server-templates/index.md) section for detailed documentation.*

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
- **CLI Interface** - Rich command-line interface (`python -m mcp_template`)
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
python -m mcp_template deploy file-server \
  --config read_only_mode=true \
  --config max_file_size=50 \
  --config log_level=debug

# Using environment variables
python -m mcp_template deploy file-server \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50

# Using config file
python -m mcp_template deploy file-server --config-file production.json
```

## Template Development

Create custom MCP server templates:

```bash
# Interactive template creation
python -m mcp_template create my-custom-server

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
