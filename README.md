# MCP Server Templates

Production-ready Model Context Protocol (MCP) server templates with **unified deployment architecture** and **zero-configurat| **demo** | Simple demo server | 🚧 In Development |

## ⚙️ Configuration Strategy

This repository implements a **hybrid configuration approach** with intelligent backend selection:

- **Simple Configs**: Environment variables (`MCP_READ_ONLY=true`)
- **Complex Configs**: YAML configuration files (mounted volumes)  
- **Auto-Detection**: System automatically chooses the right approach
- **Backend Abstraction**: Easy to extend with new deployment targets

### Deployment Backends

| Backend | Status | Use Case |
|---------|--------|----------|
| **Docker CLI** | ✅ Active | Local development, self-hosting |
| **Kubernetes** | 🚧 Planned | Production clusters, auto-scaling |
| **Mock Service** | ✅ Active | Testing, development |

See [Configuration Strategy](docs/CONFIGURATION_FINAL_RECOMMENDATIONS.md) for implementation details.

## � Docker Images

All templates are automatically built and published to Docker Hub:

- **Registry**: `dataeverything/mcp-*`
- **Auto-builds**: On every commit to main branch  
- **Multi-platform**: Linux/AMD64 and Linux/ARM64
- **Public Access**: No authentication requireduick Start

### Zero-Configuration Deployment

```bash
# Clone and setup
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates
pip install -r requirements.txt

# Deploy any template instantly
python -m mcp_deploy file-server    # File system access
python -m mcp_deploy github         # GitHub integration  
python -m mcp_deploy database       # Database queries

# List available templates
python -m mcp_deploy list

# Manage deployments
python -m mcp_deploy logs file-server   # View logs
python -m mcp_deploy stop file-server   # Stop server
python -m mcp_deploy shell file-server  # Debug shell
```

**That's it!** Your MCP server is running in Docker with:
- ✅ **Unified deployment backend** - Same robust system used in MCP Platform
- ✅ **Rich CLI interface** - Beautiful tables and progress indicators
- ✅ **Automatic configuration** - MCP client config generated automatically
- ✅ **Persistent data volumes** - Your data survives container restarts
- ✅ **Enterprise-grade logging** - Structured logs with proper error handling
- ✅ **Zero Docker knowledge required** - Just run the command

### Alternative: Manual Docker Deployment

```bash
# Pull and run directly from Docker Hub
docker run -d --name mcp-file-server \
  -v ~/mcp-data:/data \
  -v ~/.mcp/logs:/logs \
  -e MCP_ALLOWED_DIRS=/data \
  -e MCP_READ_ONLY=false \
  dataeverything/mcp-file-server:latest
```

## 🏗️ Architecture

### Unified Deployment System

```
MCPDeployer (CLI) → DeploymentManager → DockerDeploymentService → Docker CLI
```

**Key Features:**
- **Backend Abstraction** - Easy to extend with Kubernetes, cloud providers
- **CLI + Library** - Use as command-line tool or import as Python library
- **Platform Integration Ready** - Same codebase powers MCP Platform
- **No Dependencies** - Only requires `rich>=13.0.0` for beautiful CLI output

### Platform Integration

The deployment system can be easily integrated into Django applications:

```python
from mcp_deploy import DeploymentManager

# Use in your Django views
deployment_manager = DeploymentManager(backend_type="docker")
result = deployment_manager.deploy_template(
    template_id="file-server",
    configuration=user_config,
    template_data=template_metadata
)
```

## 💡 Why MCP Templates?

**The Problem**: Official MCP servers require complex setup:
- Manual Docker configuration and networking
- Volume mounting and permission management
- Environment variable configuration
- MCP client configuration files
- No standardized deployment approach
- No unified management interface

**Our Solution**: Enterprise-grade deployment system with beautiful CLI interface.

### Comparison

| Task | Official MCP Servers | MCP Templates |
|------|---------------------|---------------|
| **Setup** | Clone repo, install deps, build Docker | `git clone && pip install -r requirements.txt` |
| **Deploy** | Manual Docker commands with complex flags | `python -m mcp_deploy file-server` |
| **Configure** | Write MCP config manually | Auto-generated and saved to `~/.mcp/` |
| **Manage** | Raw Docker commands | Rich CLI: `logs`, `stop`, `shell`, `list` |
| **Updates** | Manual rebuild and redeploy | `python -m mcp_deploy file-server` (pulls latest) |
| **Integration** | No programmatic API | Import `DeploymentManager` class |
| **Backends** | Docker only | Extensible (Docker, Kubernetes, cloud) |

## 📁 Repository Structure

```
mcp-server-templates/
├── mcp_deploy/          # 🎯 Unified deployment system
│   └── __init__.py      #    - DeploymentManager (backend abstraction)
│                        #    - DockerDeploymentService (CLI integration)
│                        #    - MCPDeployer (Rich CLI interface)
├── templates/           # 📦 Template definitions
│   ├── file-server/     #    - File system access (✅ Production Ready)
│   ├── database/        #    - Database integration (🚧 Development)
│   ├── github/          #    - GitHub API integration (🚧 Development)
│   └── basic/           #    - Base template structure
├── docs/                # 📚 Documentation and guides
├── tests/               # 🧪 Test utilities and deployment validation
├── examples/            # 💡 Docker Compose and Kubernetes examples
├── setup.py             # 📦 Python package configuration
├── requirements.txt     # 🔧 Dependencies (only: rich>=13.0.0)
└── .github/             # 🚀 GitHub Actions workflows
```

## 🏗️ Templates

### ✅ Production Ready Templates

| Template | Description | Docker Image | Status |
|----------|-------------|--------------|---------|
| **file-server** | Secure file system access with FastMCP Python server | `dataeverything/mcp-file-server:latest` | ✅ Ready |

### 🚧 Development Templates

| Template | Description | Docker Image | Status |
|----------|-------------|--------------|---------|
| **database** | Database integration template | `dataeverything/mcp-database:latest` | 🚧 In Development |
| **github** | GitHub API integration | `dataeverything/mcp-github:latest` | 🚧 In Development |
| **demo** | Simple demo server | `dataeverything/mcp-demo:latest` | 🚧 In Development |

| Template | Description | Docker Image | Status |
|----------|-------------|--------------|---------|
| **file-server** | Secure file system access with MCP filesystem server | `data-everything/mcp-file-server` | ✅ Ready |

### 🚧 Development Templates

| Template | Description | Status |
|----------|-------------|---------|
| **database** | Database integration template | 🚧 In Development |
| **github** | GitHub API integration | 🚧 In Development |
| **demo** | Simple demo server | 🚧 In Development |

## � Configuration Strategy

This repository implements a **hybrid configuration approach** that scales from simple to enterprise deployments:

- **Simple Configs**: Environment variables (`MCP_READ_ONLY=true`)
- **Complex Configs**: YAML configuration files (mounted volumes)
- **Auto-Detection**: System automatically chooses the right approach

See [Configuration Strategy](docs/CONFIGURATION_FINAL_RECOMMENDATIONS.md) for details.

## 🐳 Docker Images

All templates are automatically built and published to GitHub Container Registry:

- **Registry**: `data-everything/`
- **Auto-builds**: On every commit to main branch
- **Multi-platform**: Linux/AMD64 and Linux/ARM64

## 🛠️ Development

### Using as Python Library

```python
from mcp_deploy import DeploymentManager

# Initialize with backend
manager = DeploymentManager(backend_type="docker")

# Deploy a template
result = manager.deploy_template(
    template_id="file-server",
    configuration={"read_only": False, "max_file_size": 100},
    template_data=template_metadata
)

# List deployments
deployments = manager.list_deployments()

# Get status
status = manager.get_deployment_status(deployment_name)
```

### Building Templates Locally

```bash
# Build a specific template
cd templates/file-server
docker build -t local-mcp-file-server .

# Test with deployment system
python -c "
from mcp_deploy import DeploymentManager
manager = DeploymentManager()
# Override image for local testing
template_data = {'image': 'local-mcp-file-server', 'env_vars': {}}
manager.deploy_template('file-server', {}, template_data)
"
```

### Adding New Templates

1. Copy the `templates/base/` structure
2. Implement your MCP server logic
3. Update `template.json` with proper configuration schema
4. Add environment variable mappings (`env_mapping`)
5. Test locally and submit PR

### Configuration Guidelines

Each template should support:

- **Environment Variables**: For simple configuration options
- **Config File Mounting**: For complex nested configurations
- **Schema Validation**: Proper `template.json` with `config_schema`
- **Documentation**: Clear README with usage examples

## � Template Schema

Each template must include:

```json
{
  "name": "Template Name",
  "description": "What this template does",
  "docker_image": "data-everything/template-name",
  "config_schema": {
    "properties": {
      "setting_name": {
        "type": "string",
        "env_mapping": "MCP_SETTING_NAME",
        "description": "What this setting does"
      }
    }
  }
}
```

## � Deployment

### MCP Platform (Recommended)
Deploy directly through the MCP Platform web interface.

### Docker Compose
```yaml
version: '3.8'
services:
  file-server:
    image: data-everything/mcp-file-server:latest
    environment:
      - MCP_ALLOWED_DIRS=/data:/workspace
      - MCP_READ_ONLY=false
    volumes:
      - ./data:/data
      - ./workspace:/workspace
    ports:
      - "8000:8000"
```

### Kubernetes
See `examples/kubernetes/` for deployment manifests.

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/new-template`)
3. Commit your changes (`git commit -am 'Add new template'`)
4. Push to the branch (`git push origin feature/new-template`)
5. Create a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- [MCP Platform](https://mcp-platform.ai)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Docker Images](https://github.com/orgs/Data-Everything/packages)

- [MCP Platform Core](https://github.com/Data-Everything/mcp-platform-core) - Managed hosting platform
- [MCP Deployment Tools](https://github.com/Data-Everything/mcp-deployment-tools) - Self-hosting utilities
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/) - Official MCP documentation

## 💡 Why Open Source Templates?

These MCP server implementations are open source because we believe in:

- **🔍 Transparency**: Inspect, modify, and understand exactly how your AI integrations work
- **🤝 Community**: Everyone can contribute new templates and improvements  
- **🔒 Trust**: No vendor lock-in - you own the code and can self-host anytime
- **⚡ Innovation**: Faster development through community contributions

## 🏢 Platform vs Self-Hosting

| Feature | Open Source (Self-Host) | MCP Platform (Managed) |
|---------|------------------------|------------------------|
| **MCP Server Code** | ✅ Full source code | ✅ Same implementations |
| **Deployment** | 🔧 Manual setup | ⚡ One-click deployment |
| **Hosting** | 🏠 Your infrastructure | ☁️ Managed hosting |
| **Monitoring** | 📊 DIY setup | 📈 Built-in dashboards |
| **Team Features** | ❌ Not included | 👥 Team management |
| **Support** | 📚 Community docs | 🎧 Enterprise support |
| **Cost** | 💰 Infrastructure only | 💳 Platform subscription |

Our [MCP Platform](https://mcp-platform.dataeverything.ai) adds enterprise features like team management, monitoring, and managed hosting on top of these open source templates.
