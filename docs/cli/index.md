# CLI Reference

**Complete command-line interface documentation for the MCP Platform Templates system.**

The MCP Template CLI provides a comprehensive set of commands for deploying, managing, and working with Model Context Protocol (MCP) servers. It supports multiple deployment backends, rich configuration options, and advanced features like tool discovery and integration examples.

## Quick Start

```bash
# Install MCP Templates
pip install mcp-templates

# List available templates
python -m mcp_template list

# Deploy a template with defaults
python -m mcp_template deploy demo

# View template configuration options
python -m mcp_template config demo

# Discover tools from template
python -m mcp_template tools demo
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

### Tool Discovery & Interaction
- [discover-tools](discover-tools.md) - Discover available tools from MCP servers
- [tools](tools.md) - List and inspect tools in templates and deployments
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
python -m mcp_template create

# Create from existing image
python -m mcp_template create --from-image mcp/filesystem my-file-server

# Non-interactive creation
python -m mcp_template create --config-file template-config.json --non-interactive
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
python -m mcp_template deploy file-server --config read_only_mode=true

# Nested format (equivalent)
python -m mcp_template deploy file-server --config security__read_only=true

# Template-prefixed format
python -m mcp_template deploy file-server --config file-server__security__read_only=true
```

## Common Usage Patterns

### Development Workflow

```bash
# Create and test new template
python -m mcp_template create my-server
python -m mcp_template deploy my-server --config debug=true
python -m mcp_template logs my-server --follow

# Test tools
python -m mcp_template tools my-server
python -m mcp_template connect my-server --llm claude
```

### Production Deployment

```bash
# Deploy with production config
python -m mcp_template deploy file-server \
  --config-file production.json \
  --name prod-file-server \
  --no-pull

# Monitor deployment
python -m mcp_template status prod-file-server
python -m mcp_template logs prod-file-server --tail 100
```

### Tool Discovery

```bash
# Discover tools from external Docker image
python -m mcp_template discover-tools --image mcp/filesystem /tmp

# List tools from deployed template
python -m mcp_template tools demo --refresh

# Get integration examples
python -m mcp_template connect demo --llm vscode
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
