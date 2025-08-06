# CLI Reference

**Complete command-line interface documentation for the MCP Platform Templates system.**

The MCP Template CLI provides a comprehensive set of commands for deploying, managing, and working with Model Context Protocol (MCP) servers. It supports multiple deployment backends, rich configuration options, and advanced features like tool discovery and integration examples.

## Quick Start

```bash
# Install MCP Templates
pip install mcp-templates

# List available templates
mcp-template list

# Deploy a template with defaults
mcp-template deploy demo

# View template configuration options
mcp-template config demo

# Discover tools from template
mcp-template tools demo
```

## Global Options

| Option | Description |
|--------|-------------|
| `--help, -h` | Show help message and exit |
| `--version` | Show version information |
| `--verbose, -v` | Enable verbose output with detailed logging |
| `--quiet, -q` | Suppress output except errors |

## Command Reference

### Template Management
- [create](create.md) - Create new MCP server templates with interactive guidance
- [deploy](deploy.md) - Deploy MCP server templates to infrastructure
- [list](list.md) - List available templates and deployments
- [stop](stop.md) - Stop deployed templates or specific deployments

### Tool Discovery & Interaction
- [connect](connect.md) - Connect to deployed MCP servers with LLM clients

### Configuration & Monitoring
- [config](config.md) - View and validate configuration settings
- [status](status.md) - Check deployment health and detailed status information
- [logs](logs.md) - Access deployment logs and monitoring

## Configuration System

The CLI supports comprehensive template creation alongside deployment and configuration management:

### Template Creation & Development

```bash
# Interactive template creation
mcp-template create

# Create from existing image
mcp-template create --from-image mcp/filesystem my-file-server

# Non-interactive creation
mcp-template create --config-file template-config.json --non-interactive
```

### Configuration Precedence

The CLI supports multiple configuration methods with clear precedence:

```
Environment Variables > CLI Options > Config File > Template Defaults
```

### Configuration Sources

1. **Environment Variables**: `MCP_*` prefixed variables
2. **CLI Options**: `--config key=value` and `--env KEY=VALUE`
3. **Configuration Files**: JSON/YAML files via `--config-file`
4. **Template Defaults**: Built-in template configurations

### Double-Underscore Notation

Use double underscores for nested configuration:

```bash
# Standard format
mcp-template deploy file-server --config read_only_mode=true

# Nested format (equivalent)
mcp-template deploy file-server --config security__read_only=true

# Template-prefixed format
mcp-template deploy file-server --config file-server__security__read_only=true
```

## Common Usage Patterns

### Development Workflow

```bash
# Create and test new template
mcp-template create my-server
mcp-template deploy my-server --config debug=true
mcp-template logs my-server --follow

# Test tools
mcp-template tools my-server
mcp-template connect my-server --llm claude
```

### Production Deployment

```bash
# Deploy with production config
mcp-template deploy file-server \
  --config-file production.json \
  --name prod-file-server \
  --no-pull

# Monitor deployment
mcp-template status prod-file-server
mcp-template logs prod-file-server --tail 100
```

### Tool Discovery

```bash
# Unified tool discovery command
mcp-template tools demo                              # From templates
mcp-template tools --image mcp/filesystem /tmp       # From Docker images

# Get integration examples
mcp-template connect demo --llm vscode
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TEMPLATE_DEFAULT_BACKEND` | Default deployment backend | `docker` |
| `MCP_TEMPLATE_CONFIG_PATH` | Default configuration directory | `~/.mcp-template` |
| `MCP_DEBUG` | Enable debug logging | `false` |
| `DOCKER_HOST` | Docker daemon host (for Docker backend) | `unix:///var/run/docker.sock` |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid argument or configuration |
| `3` | Template not found |
| `4` | Deployment error |
| `5` | Backend not available |

## Error Handling

The CLI provides comprehensive error handling with helpful messages:

```bash
# Template not found
❌ Template 'nonexistent' not found
Available templates: demo, file-server, postgres-server

# Configuration error
❌ Invalid configuration: security.max_file_size must be a number
   Given: "unlimited"
   Expected: integer

# Backend error
❌ Docker daemon not available
   Please ensure Docker is installed and running
```

## Integration Examples

### Claude Desktop

```json
{
  "mcpServers": {
    "my-server": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "my-server": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

### Python

```python
import asyncio
from mcp_template.client import MCPClient

async def main():
    client = MCPClient("container-name")
    await client.connect()

    tools = await client.list_tools()
    result = await client.call_tool("example_tool", {"param": "value"})

    await client.disconnect()

asyncio.run(main())
```

## Support & Troubleshooting

For common issues and troubleshooting:
- Check [Troubleshooting Guide](../guides/troubleshooting.md)
- Review [FAQ](../faq.md)
- Visit [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)

## Next Steps

- Explore individual [command documentation](list.md)
- Learn about [template creation](create.md)
- Set up [integration workflows](connect.md)
- Configure [advanced deployments](deploy.md)
