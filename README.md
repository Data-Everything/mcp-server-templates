# MCP Server Templates

Production-ready Model Context Protocol (MCP) server templates with a **unified deployment architecture** and **comprehensive configuration support**. Easily deploy, manage, and extend AI server templates with flexible configuration options matching commercial platform capabilities.

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

- **CLI Tool**: `python -m mcp_template` with comprehensive config support
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
| `python -m mcp_template list` | List all deployments |
| `python -m mcp_template deploy <template>` | Deploy template with defaults |
| `python -m mcp_template deploy <template> --no-pull` | Deploy without pulling image (use local) |
| `python -m mcp_template status <deployment>` | View deployment status |
| `python -m mcp_template delete <deployment>` | Delete deployment |
| `python -m mcp_template create <template-id>` | Create new template |

### Configuration Options

**1. Check Template Configuration:**
```bash
# View template.json to see available config options
cat templates/file-server/template.json
```

**2. Deploy with Config File:**
```bash
# JSON config file
python -m mcp_template deploy file-server --config-file ./config.json

# YAML config file
python -m mcp_template deploy file-server --config-file ./config.yml
```

**3. Deploy with CLI Configuration Options:**

There are **two types** of CLI configuration:

- **`--config`**: For `config_schema` properties (becomes environment variables)
- **`--override`**: For template data modifications (modifies template structure directly)

```bash
# Configuration schema properties (recommended for server settings)
python -m mcp_template deploy file-server \
  --config read_only_mode=true \
  --config max_file_size=50 \
  --config log_level=debug

# Template data overrides (for metadata, tools, custom fields)
python -m mcp_template deploy file-server \
  --override "metadata__version=2.0.0" \
  --override "metadata__author=MyName" \
  --override "tools__0__enabled=false"

# Combined usage with custom name
python -m mcp_template deploy file-server \
  --name my-file-server \
  --no-pull \
  --config read_only_mode=true \
  --override "metadata__description=Custom file server"
```

**4. Double Underscore Notation for Nested Configuration:**

Both `--config` and `--override` support double underscore notation for nested structures:

```bash
# Config schema properties (nested configuration)
python -m mcp_template deploy file-server \
  --config security__read_only=true \
  --config security__max_file_size=50 \
  --config logging__level=debug

# Template data overrides (nested modifications)
python -m mcp_template deploy file-server \
  --override "metadata__version=2.0.0" \
  --override "config__custom_setting=value" \
  --override "tools__0__description=Modified tool" \
  --override "servers__0__config__host=remote.example.com"
```

**5. Advanced Override Examples:**

```bash
# Array modifications with automatic type conversion
python -m mcp_template deploy demo \
  --override "tools__0__enabled=false" \
  --override "tools__1__timeout=30.5" \
  --override "metadata__tags=[\"custom\",\"modified\"]"

# Complex nested structure creation
python -m mcp_template deploy demo \
  --override "config__database__connection__host=localhost" \
  --override "config__database__connection__port=5432" \
  --override "config__security__enabled=true"

# JSON object overrides
python -m mcp_template deploy demo \
  --override "metadata__custom={\"key\":\"value\",\"nested\":{\"prop\":true}}"
```

**6. Deploy with Environment Variables:**
```bash
python -m mcp_template deploy file-server \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50 \
  --env MCP_LOG_LEVEL=debug
```

**7. Mixed Configuration (precedence: env > cli > file > defaults):**
```bash
python -m mcp_template deploy file-server \
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
4. Test with `python -m mcp_template {name} --show-config`

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
python -m mcp_template list
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
python -m mcp_template list

# 3. Deploy with defaults
python -m mcp_template deploy file-server

# 4. Deploy with custom config and skip image pull
python -m mcp_template deploy file-server --config-file ./my-config.json --no-pull

# 5. View deployment status
python -m mcp_template status file-server-deployment

# 6. Delete when done
python -m mcp_template delete file-server-deployment
```

### Template Discovery

```bash
# List all available templates
python -m mcp_template create --help

# Create new template interactively
python -m mcp_template create my-custom-template
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
