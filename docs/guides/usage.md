# Using MCP Server Templates

Comprehensive guide for integrating deployed MCP server templates with various clients and development environments.

## 🎯 Overview

Once you've deployed an MCP server template, you can integrate it with:
- **Claude Desktop**: For AI-powered workflows
- **VS Code**: For development environments
- **Python Applications**: For programmatic access
- **Other MCP-compatible clients**: Custom integrations

## 📋 Prerequisites

Before integrating, ensure you have:
1. **Deployed server**: `mcpt deploy <template-name>`
2. **Container name**: Note the container name from deployment output
3. **Configuration**: Know your server's configuration options

## 🔧 Integration Methods

### Method 1: Claude Desktop Integration

Perfect for AI-powered document processing, analysis, and automation.

#### 1. Find Your Container Name

```bash
# List running MCP containers
docker ps --filter "label=mcp.template-id" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Example output:
# mcp-filesystem-0725-123456-abcdef    dataeverything/mcp-filesystem:latest    Up 2 minutes
# mcp-demo-0725-789012-ghijkl           dataeverything/mcp-demo:latest           Up 1 minute
```

#### 2. Update Claude Desktop Configuration

**Location**:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration**:
```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

**Example for multiple templates**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-filesystem-0725-123456-abcdef", "python", "-m", "src.server"]
    },
    "demo-server": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-demo-0725-789012-ghijkl", "python", "-m", "src.server"]
    }
  }
}
```

#### 3. Restart Claude Desktop

After updating the configuration:
1. **Quit Claude Desktop** completely
2. **Restart the application**
3. **Verify connection**: Look for your server in the MCP section

#### 4. Usage in Claude Desktop

```
Example prompts:
• "List files in my Documents folder" (filesystem)
• "Say hello to Alice" (demo server)
• "Get server information" (any server)
• "Show me the configuration options"
```

### Method 2: VS Code Integration

Ideal for development workflows and code analysis.

#### 1. Install MCP Extension

```bash
# Install the MCP extension for VS Code
code --install-extension mcp-client
```

#### 2. Configure VS Code Settings

**File**: `.vscode/settings.json` in your workspace

```json
{
  "mcp.servers": {
    "filesystem": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"],
      "description": "File system access server"
    },
    "demo-server": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"],
      "description": "Demo greeting server"
    }
  }
}
```

#### 3. Use MCP Tools in VS Code

- **Command Palette**: `Ctrl+Shift+P` → "MCP: List Tools"
- **Tool Execution**: Select and run tools directly
- **Integration**: Use with GitHub Copilot Chat

### Method 3: Python Integration

For programmatic access and custom applications.

#### 1. Install MCP Client

```bash
pip install mcp
```

#### 2. Basic Python Client

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, container_name: str):
        self.server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", container_name, "python", "-m", "src.server"]
        )

    async def connect(self):
        """Establish connection to MCP server."""
        self.client = stdio_client(self.server_params)
        self.read, self.write = await self.client.__aenter__()
        self.session = ClientSession(self.read, self.write)
        await self.session.initialize()
        return self.session

    async def list_tools(self):
        """List available tools."""
        tools = await self.session.list_tools()
        return [(tool.name, tool.description) for tool in tools.tools]

    async def call_tool(self, name: str, args: dict = None):
        """Call a specific tool."""
        result = await self.session.call_tool(name, args or {})
        return result.content[0].text

    async def disconnect(self):
        """Close the connection."""
        await self.client.__aexit__(None, None, None)

# Usage example
async def main():
    client = MCPClient("mcp-demo-0725-789012-ghijkl")

    try:
        await client.connect()

        # List available tools
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Call a tool
        greeting = await client.call_tool("say_hello", {"name": "World"})
        print("Greeting:", greeting)

    finally:
        await client.disconnect()

# Run the client
asyncio.run(main())
```

#### 3. Advanced Python Usage

```python
import asyncio
from typing import Dict, Any, List

class AdvancedMCPClient(MCPClient):
    async def batch_operations(self, operations: List[Dict[str, Any]]):
        """Execute multiple operations in sequence."""
        results = []
        for op in operations:
            result = await self.call_tool(op['tool'], op.get('args', {}))
            results.append({
                'operation': op,
                'result': result
            })
        return results

    async def health_check(self):
        """Check server health and capabilities."""
        try:
            tools = await self.list_tools()
            return {
                'status': 'healthy',
                'tools_count': len(tools),
                'tools': tools
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Batch operations example
async def process_batch():
    client = AdvancedMCPClient("mcp-filesystem-0725-123456-abcdef")

    await client.connect()

    operations = [
        {'tool': 'list_directory', 'args': {'path': '/home/user/docs'}},
        {'tool': 'read_file', 'args': {'path': '/home/user/docs/readme.txt'}},
        {'tool': 'get_file_info', 'args': {'path': '/home/user/docs/readme.txt'}}
    ]

    results = await client.batch_operations(operations)

    for result in results:
        print(f"Tool {result['operation']['tool']}: {result['result']}")

    await client.disconnect()
```

### Method 4: Manual CLI Testing

For testing and debugging server functionality.

#### 1. Interactive Testing

```bash
# Connect directly to the server
docker exec -it CONTAINER_NAME python -m src.server

# Or use our test client
python test_demo_client.py
```

#### 2. Tool Testing

```bash
# Test specific functionality
docker exec CONTAINER_NAME python -c "
import asyncio
from src.server import DemoServer

async def test():
    server = DemoServer()
    # Test tool directly (bypassing MCP protocol)
    result = await server._register_tools.__wrapped__(server).say_hello('Test')
    print(result)

asyncio.run(test())
"
```

## 🛠️ Configuration Management

### Environment Variables

All templates support environment variable configuration:

```bash
# Deploy with custom configuration
mcpt deploy template-name \
  --config key1=value1 \
  --config key2=value2 \
  --env CUSTOM_VAR=custom_value
```

### Configuration Files

```bash
# Using configuration file
mcpt deploy template-name \
  --config-file my-config.json
```

**Example config file** (`my-config.json`):
```json
{
  "hello_from": "My Custom App",
  "log_level": "debug",
  "timeout": 60,
  "features": ["feature1", "feature2"]
}
```

### Dynamic Configuration

```bash
# Show available configuration options
mcpt deploy template-name --show-config

# Deploy with double underscore notation for nested config
mcpt deploy template-name \
  --config security__read_only=true \
  --config logging__level=debug
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Container Not Found
```bash
# Check running containers
docker ps --filter "label=mcp.template-id"

# If no containers, redeploy
mcpt deploy template-name
```

#### 2. Connection Refused
```bash
# Check container logs
docker logs CONTAINER_NAME

# Check container is running
docker exec CONTAINER_NAME ps aux
```

#### 3. Tool Not Working
```bash
# Test tool directly
docker exec -it CONTAINER_NAME python -c "
import sys
sys.path.append('/app')
from src.server import *
# Test server initialization
"
```

### Debug Mode

```bash
# Deploy with debug logging
mcpt deploy template-name \
  --config log_level=debug

# View debug logs
docker logs -f CONTAINER_NAME
```

## 📊 Monitoring and Management

### Container Management

```bash
# List all MCP containers
docker ps --filter "label=mcp.template-id" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# Stop specific template
mcpt stop template-name

# View logs
mcpt logs template-name

# Access shell
mcpt shell template-name
```

### Health Monitoring

```python
# Health check script
import asyncio
import docker

async def check_mcp_servers():
    client = docker.from_env()
    containers = client.containers.list(filters={
        "label": "mcp.template-id"
    })

    for container in containers:
        print(f"Container: {container.name}")
        print(f"Status: {container.status}")
        print(f"Health: {container.attrs.get('State', {}).get('Health', {}).get('Status', 'N/A')}")
        print("-" * 40)

asyncio.run(check_mcp_servers())
```

## 🔗 Next Steps

After successful integration:

1. **Template-Specific Usage**: Check `docs/server-templates/<template-name>/` for specific examples
2. **Advanced Configuration**: See `docs/guides/configuration.md`
3. **Development**: See `docs/development/template-development.md`
4. **Contributing**: See `docs/guides/contributing.md`

## 📚 Resources

- **Template Documentation**: `docs/server-templates/`
- **Configuration Guide**: `docs/guides/configuration.md`
- **MCP Protocol**: [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- **Support**: [tooling@dataeverything.ai](mailto:tooling@dataeverything.ai)
