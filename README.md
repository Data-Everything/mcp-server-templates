# MCP Server Templates

Production-ready Model Context Protocol (MCP) server templates with a **unified deployment architecture** and **comprehensive configuration support**. Easily deploy, manage, and extend AI server templates with flexible configuration options matching commercial platform capabilities.

## ⚡ Features

Get ready to supercharge your MCP journey! The MCP Platform is packed with electrifying features that make server deployment a thrill ride:

### 🚀 Current Features

- **🖱️ One-Click Docker Deployment**: Launch MCP servers instantly with pre-built templates—no hassle, just pure speed.
- **🔎 Smart Tool Discovery**: Automatically finds and showcases every tool your server can offer. No more guesswork!
- **💻 Slick CLI Management**: Command-line magic for easy, powerful control over all deployments.
- **🤝 Bring Your Own MCP Server**: Plug in your own MCP server and run it on our network—even with limited features!
- **🐳 Effortless Docker Image Integration**: Add any existing MCP Docker image to the templates library with minimal setup and unlock all the platform’s cool benefits.
- **⚡ Boilerplate Template Generator**: Instantly create new MCP server projects with a CLI-powered generator—kickstart your next big idea!
- **🛠️ Multiple Ways to Set Configuration**: Flex your setup with config via JSON, YAML, environment variables, CLI config, or CLI override options—total flexibility for every workflow!

### 🌈 Planned Features

- **🦸 MCP Sidekick (Coming Soon)**: Your friendly AI companion, making every MCP server compatible with any AI tool or framework.
- **🛸 Kubernetes Support**: Deploy to Kubernetes clusters with ease, scaling your MCP servers effortlessly.

**Release Timeline:** All this and more dropping mid-August 2025—don’t miss out!

Want the full scoop? [Check out the docs for more features & details!](docs/index.md)

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

- **CLI Tool**: `mcp-template` with comprehensive config support
- **DeploymentManager**: Unified interface for Docker, Kubernetes, or Mock backends
- **TemplateDiscovery**: Auto-discovers templates with config schema validation
- **ConfigMapping**: Generic mapping system supporting nested JSON/YAML configs
- **Multi-source Configuration**: File-based, CLI options, and environment variables

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
  "docker_image": "dataeverything/mcp-file-server",
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

### Basic Commands

| Command | Description |
|---------|-------------|
| `mcp-template list` | List all deployments |
| `mcp-template deploy <template>` | Deploy template with defaults (HTTP transport only) |
| `mcp-template deploy <template> --no-pull` | Deploy without pulling image (use local) |
| `mcp-template status <deployment>` | View deployment status |
| `mcp-template delete <deployment>` | Delete deployment |
| `mcp-template create <template-id>` | Create new template |
| `mcp-template run-tool <template> <tool_name>` | Run a tool from stdio MCP server |
| `mcp-template tools <template>` | List available tools in a template |

### Transport Types & Usage

MCP servers support two transport types with different deployment approaches:

#### HTTP Transport (Deployable)
HTTP transport servers run as persistent containers and can be deployed using the standard `deploy` command:

```bash
# Deploy HTTP transport server (runs persistently)
mcp-template deploy http-server --config port=8080

# Check server status
mcp-template status http-server-xyz

# Access via HTTP endpoint
curl http://localhost:8080/tools
```

#### Stdio Transport (Interactive)
Stdio transport servers run interactively and **cannot be deployed** as persistent containers. They use standard input/output for communication and are designed for direct tool execution:

```bash
# ❌ Cannot deploy stdio servers (will show error with helpful guidance)
mcp-template deploy stdio-server
# Error: Cannot deploy stdio transport MCP servers
# Stdio transport doesn't require deployment - use run-tool command instead

# ✅ List available tools in stdio server
mcp-template tools github
# Shows all available tools with descriptions

# ✅ Run specific tools from stdio server
mcp-template run-tool github search_repositories --args '{"query": "mcp server"}'
mcp-template run-tool github create_issue --args '{"owner": "user", "repo": "test", "title": "New issue"}'

# ✅ Run tools with configuration and environment variables
mcp-template run-tool github search_repositories \
  --args '{"query": "python"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token \
  --config timeout=30
```

### Configuration Options

**1. Check Template Configuration:**
```bash
# View template.json to see available config options
cat templates/file-server/template.json
```

**2. Deploy with Config File:**
```bash
# JSON config file
mcp-template deploy file-server --config-file ./config.json

# YAML config file
mcp-template deploy file-server --config-file ./config.yml
```

**3. Deploy with CLI Configuration Options:**

There are **two types** of CLI configuration:

- **`--config`**: For `config_schema` properties (becomes environment variables)
- **`--override`**: For template data modifications (modifies template structure directly)

```bash
# Configuration schema properties (recommended for server settings)
mcp-template deploy file-server \
  --config read_only_mode=true \
  --config max_file_size=50 \
  --config log_level=debug

# Template data overrides (for metadata, tools, custom fields)
mcp-template deploy file-server \
  --override "metadata__version=2.0.0" \
  --override "metadata__author=MyName" \
  --override "tools__0__enabled=false"

# Combined usage with custom name
mcp-template deploy file-server \
  --name my-file-server \
  --no-pull \
  --config read_only_mode=true \
  --override "metadata__description=Custom file server"
```

**4. Double Underscore Notation for Nested Configuration:**

Both `--config` and `--override` support double underscore notation for nested structures:

```bash
# Config schema properties (nested configuration)
mcp-template deploy file-server \
  --config security__read_only=true \
  --config security__max_file_size=50 \
  --config logging__level=debug

# Template data overrides (nested modifications)
mcp-template deploy file-server \
  --override "metadata__version=2.0.0" \
  --override "config__custom_setting=value" \
  --override "tools__0__description=Modified tool" \
  --override "servers__0__config__host=remote.example.com"
```

**5. Advanced Override Examples:**

```bash
# Array modifications with automatic type conversion
mcp-template deploy demo \
  --override "tools__0__enabled=false" \
  --override "tools__1__timeout=30.5" \
  --override "metadata__tags=[\"custom\",\"modified\"]"

# Complex nested structure creation
mcp-template deploy demo \
  --override "config__database__connection__host=localhost" \
  --override "config__database__connection__port=5432" \
  --override "config__security__enabled=true"

# JSON object overrides
mcp-template deploy demo \
  --override "metadata__custom={\"key\":\"value\",\"nested\":{\"prop\":true}}"
```

**6. Deploy with Environment Variables:**
```bash
mcp-template deploy file-server \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50 \
  --env MCP_LOG_LEVEL=debug
```

**7. Mixed Configuration (precedence: env > cli > file > defaults):**
```bash
mcp-template deploy file-server \
  --config-file ./base-config.json \
  --config log_level=warning \
  --override "metadata__version=1.5.0" \
  --env MCP_READ_ONLY=true
```

### Configuration vs Override Usage Guide

| Use Case | Recommended Method | Example |
|----------|-------------------|---------|
| Server settings (logging, security, performance) | `--config` | `--config log_level=debug` |
| Nested server configuration | `--config` with `__` | `--config security__read_only=true` |
| Template metadata changes | `--override` | `--override "metadata__version=2.0.0"` |
| Tool modifications | `--override` | `--override "tools__0__enabled=false"` |
| Custom fields addition | `--override` | `--override "custom_field=value"` |
| Complex nested structures | `--override` with `__` | `--override "config__db__host=localhost"` |

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
- `file-server-config.json`: Example file-server configuration
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
make test-template TEMPLATE=file-server

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

- **[Documentation Index](docs/index.md)**: Central hub for all documentation
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

# 2. List available deployments
mcp-template list

# 3. Deploy with defaults
mcp-template deploy file-server

# 4. Deploy with custom config and skip image pull
mcp-template deploy file-server --config-file ./my-config.json --no-pull

# 5. View deployment status
mcp-template status file-server-deployment

# 6. Delete when done
mcp-template delete file-server-deployment
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
- **Community Slack**: [Join mcp-platform workspace](https://join.slack.com/t/mcp-platform/shared_invite/zt-39z1p559j-8aWEML~IsSPwFFgr7anHRA)
- **Documentation**: [docs/index.md](docs/index.md)
