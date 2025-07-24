# MCP Server Templates

A collection of production-ready Model Context Protocol (MCP) server templates for various use cases.

## 🚀 Quick Start

1. **Browse Templates**: Explore the `/templates` directory for available templates
2. **Deploy**: Use the MCP Platform or deploy locally with Docker
3. **Customize**: Fork and modify templates for your specific needs

## 📁 Repository Structure

```
mcp-server-templates/
├── templates/           # Template definitions
│   ├── file-server/    # File system access server (✅ Production Ready)
│   ├── database/       # Database integration server
│   ├── github/         # GitHub API integration server
│   └── ...
├── docs/               # Documentation and guides
├── scripts/            # Build and deployment scripts
├── tests/              # Test utilities and scripts
└── .github/            # GitHub Actions workflows
```

## 🏗️ Templates

### ✅ Production Ready Templates

| Template | Description | Docker Image | Status |
|----------|-------------|--------------|---------|
| **file-server** | Secure file system access with MCP filesystem server | `ghcr.io/data-everything/mcp-file-server` | ✅ Ready |

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

- **Registry**: `ghcr.io/data-everything/`
- **Auto-builds**: On every commit to main branch
- **Multi-platform**: Linux/AMD64 and Linux/ARM64

## 🛠️ Development

### Building Templates Locally

```bash
# Build a specific template
./scripts/build-template.sh file-server

# Test locally
docker run --rm -p 8000:8000 \
  --env=MCP_ALLOWED_DIRS=/data \
  --env=MCP_LOG_LEVEL=debug \
  ghcr.io/data-everything/mcp-file-server:latest
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
  "docker_image": "ghcr.io/data-everything/template-name",
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
    image: ghcr.io/data-everything/mcp-file-server:latest
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
