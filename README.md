# 🚀 This Project Has Moved!

> ## ⚠️ **IMPORTANT: This repository has been renamed and moved to [MCP Platform](https://github.com/Data-Everything/MCP-Platform)**
>
> **What changed:**
> - **New Repository**: [`Data-Everything/MCP-Platform`](https://github.com/Data-Everything/MCP-Platform)
> - **New Package**: `pip install mcp-platform` (replaces `mcp-templates`)
> - **New CLI**: `mcpp` command (replaces `mcpt`)
> - **Enhanced Features**: Improved architecture and expanded capabilities
>
> **Migration is easy:**
> ```bash
> # Uninstall old package
> pip uninstall mcp-templates
>
> # Install new package
> pip install mcp-platform
>
> # Use new command (all your configs work the same!)
> mcpp deploy demo  # instead of mcpt deploy demo
> ```
>
> **📚 [Complete Migration Guide](https://github.com/Data-Everything/MCP-Platform#migration-from-mcp-templates)** | **🆕 [New Documentation](https://data-everything.github.io/MCP-Platform/)**

---

# MCP Server Templates (Legacy)

> **⚠️ This version is in maintenance mode. Please migrate to [MCP Platform](https://github.com/Data-Everything/MCP-Platform) for latest features and updates.**

[![Version](https://img.shields.io/pypi/v/mcp-templates.svg)](https://pypi.org/project/mcp-templates/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-templates.svg)](https://pypi.org/project/mcp-templates/)
[![License](https://img.shields.io/badge/License-Elastic%202.0-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/discord/XXXXX?color=7289da&logo=discord&logoColor=white)](https://discord.gg/55Cfxe9gnr)

<div align="center">

**� [Migrate to MCP Platform](https://github.com/Data-Everything/MCP-Platform)** • **[💬 Discord Community](https://discord.gg/55Cfxe9gnr)** • **[� Legacy Docs](#-quick-start)**

</div>

> **Deploy Model Context Protocol (MCP) servers in seconds, not hours.**

Zero-configuration deployment of production-ready MCP servers with Docker containers, comprehensive CLI tools, and intelligent caching. Focus on AI integration, not infrastructure setup.

---

## 🚀 Quick Start

```bash
# Install MCP Templates
pip install mcp-templates

# List available templates
mcpt list

# Deploy instantly
mcpt deploy demo

# View deployment
mcpt logs demo
```

**That's it!** Your MCP server is running at `http://localhost:8080`

---

## ⚡ Why MCP Templates?

| Traditional MCP Setup | With MCP Templates |
|----------------------|-------------------|
| ❌ Complex configuration | ✅ One-command deployment |
| ❌ Docker expertise required | ✅ Zero configuration needed |
| ❌ Manual tool discovery | ✅ Automatic detection |
| ❌ Environment setup headaches | ✅ Pre-built containers |

**Perfect for:** AI developers, data scientists, DevOps teams building with MCP.

---

## 🌟 Key Features

### 🖱️ **One-Click Deployment**
Deploy MCP servers instantly with pre-built templates—no Docker knowledge required.

### 🔍 **Smart Tool Discovery**
Automatically finds and showcases every tool your server offers.

### 🧠 **Intelligent Caching**
6-hour template caching with automatic invalidation for lightning-fast operations.

### 💻 **Powerful CLI**
Comprehensive command-line interface for deployment, management, and tool execution.

### 🛠️ **Flexible Configuration**
Configure via JSON, YAML, environment variables, CLI options, or override parameters.

### 📦 **Growing Template Library**
Ready-to-use templates for common use cases: filesystem, databases, APIs, and more.

---

## 📚 Installation

### PyPI (Recommended)
```bash
pip install mcp-templates
```

### Docker
```bash
docker run --privileged -it dataeverything/mcp-server-templates:latest deploy demo
```

### From Source
```bash
git clone https://github.com/DataEverything/mcp-server-templates.git
cd mcp-server-templates
pip install -r requirements.txt
```

---

## 🎯 Common Use Cases

### Deploy with Custom Configuration
```bash
# Basic deployment
mcpt deploy filesystem --config allowed_dirs="/path/to/data"

# Advanced overrides
mcpt deploy demo --override metadata__version=2.0 --transport http
```

### Manage Deployments
```bash
# List all deployments
mcpt list --deployed

# Stop a deployment
mcpt stop demo

# View logs
mcpt logs demo --follow
```

### Template Development
```bash
# Create new template
mcpt create my-template

# Test locally
mcpt deploy my-template --backend mock
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│  CLI Tool   │───▶│ DeploymentManager │───▶│ Backend (Docker)    │
│  (mcpt)     │    │                   │    │                     │
└─────────────┘    └───────────────────┘    └─────────────────────┘
       │                      │                        │
       ▼                      ▼                        ▼
┌─────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│ Template    │    │ CacheManager      │    │ Container Instance  │
│ Discovery   │    │ (6hr TTL)         │    │                     │
└─────────────┘    └───────────────────┘    └─────────────────────┘
```

**Configuration Flow:** Template Defaults → Config File → CLI Options → Environment Variables

---

## 📦 Available Templates

| Template | Description | Transport | Use Case |
|----------|-------------|-----------|----------|
| **demo** | Hello world MCP server | HTTP, stdio | Testing & learning |
| **filesystem** | Secure file operations | stdio | File management |
| **gitlab** | GitLab API integration | stdio | CI/CD workflows |
| **github** | GitHub API integration | stdio | Development workflows |
| **zendesk** | Customer support tools | HTTP, stdio | Support automation |

[View all templates →](https://data-everything.github.io/mcp-server-templates/server-templates/)

---

## 🛠️ Configuration Examples

### Basic Configuration
```bash
mcpt deploy filesystem --config allowed_dirs="/home/user/data"
```

### Advanced Configuration
```bash
mcpt deploy gitlab \
  --config gitlab_token="$GITLAB_TOKEN" \
  --config read_only_mode=true \
  --override metadata__version=1.2.0 \
  --transport stdio
```

### Configuration File
```json
{
  "allowed_dirs": "/home/user/projects",
  "log_level": "DEBUG",
  "security": {
    "read_only": false,
    "max_file_size": "100MB"
  }
}
```

```bash
mcpt deploy filesystem --config-file myconfig.json
```

---

## 🔧 Template Development

### Creating Templates

1. **Use the generator**:
   ```bash
   mcpt create my-template
   ```

2. **Define template.json**:
   ```json
   {
     "name": "My Template",
     "description": "Custom MCP server",
     "docker_image": "my-org/my-mcp-server",
     "transport": {
       "default": "stdio",
       "supported": ["stdio", "http"]
     },
     "config_schema": {
       "type": "object",
       "properties": {
         "api_key": {
           "type": "string",
           "env_mapping": "API_KEY",
           "sensitive": true
         }
       }
     }
   }
   ```

3. **Test and deploy**:
   ```bash
   mcpt deploy my-template --backend mock
   ```

[Full template development guide →](https://data-everything.github.io/mcp-server-templates/templates/creating/)

---

## � Migration to MCP Platform

**This repository has evolved into MCP Platform with enhanced features and better architecture.**

### Why We Moved

1. **Better Naming**: "MCP Platform" better reflects the comprehensive nature of the project
2. **Enhanced Architecture**: Improved codebase structure and performance
3. **Expanded Features**: More deployment options, better tooling, enhanced templates
4. **Future Growth**: Better positioned for upcoming MCP ecosystem developments

### What Stays the Same

- ✅ All your existing configurations work unchanged
- ✅ Same Docker images and templates
- ✅ Same deployment workflows
- ✅ Full backward compatibility during transition

### Migration Steps

1. **Install new package:**
   ```bash
   pip uninstall mcp-templates
   pip install mcp-platform
   ```

2. **Update commands:**
   ```bash
   # Old command
   mcpt deploy demo

   # New command (everything else identical)
   mcpp deploy demo
   ```

3. **Update documentation bookmarks:**
   - New docs: https://data-everything.github.io/MCP-Platform/
   - New repository: https://github.com/Data-Everything/MCP-Platform

### Support Timeline

- **Current (Legacy) Package**: Security updates only through 2025
- **New Platform**: Active development, new features, full support
- **Migration Support**: Available through Discord and GitHub issues

**🚀 [Start your migration now →](https://github.com/Data-Everything/MCP-Platform)**

---

## �📖 Documentation (Legacy)

- **[Getting Started](https://data-everything.github.io/mcp-server-templates/getting-started/)** - Installation and first deployment
- **[CLI Reference](https://data-everything.github.io/mcp-server-templates/cli/)** - Complete command documentation
- **[Template Guide](https://data-everything.github.io/mcp-server-templates/templates/)** - Creating and configuring templates
- **[User Guide](https://data-everything.github.io/mcp-server-templates/user-guide/)** - Advanced usage and best practices

---

## 🤝 Community

- **[Discord Server](https://discord.gg/55Cfxe9gnr)** - Get help and discuss features
- **[GitHub Issues](https://github.com/DataEverything/mcp-server-templates/issues)** - Report bugs and request features
- **[Discussions](https://github.com/DataEverything/mcp-server-templates/discussions)** - Share templates and use cases

---

## 📝 License

This project is licensed under the [Elastic License 2.0](LICENSE).

---

## 🙏 Acknowledgments

Built with ❤️ for the MCP community. Thanks to all contributors and template creators!
