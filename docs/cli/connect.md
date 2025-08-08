# connect

**Generate integration examples and code snippets for connecting MCP servers to various LLM clients and frameworks.**

## Synopsis

```bash
mcpt connect TEMPLATE [OPTIONS]
```

## Description

The `connect` command generates ready-to-use integration examples for connecting deployed MCP servers to popular LLM clients, IDEs, and frameworks. It provides language-specific code snippets, configuration files, and step-by-step setup instructions.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE` | Name of the deployed template to generate integration for |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--llm {fastmcp,claude,vscode,curl,python}` | Generate specific integration example | Show all |

## Supported Integrations

### LLM Clients
- **fastmcp**: FastMCP Python client integration
- **claude**: Claude Desktop application setup
- **vscode**: VS Code extension configuration
- **cursor**: Cursor IDE integration
- **continue**: Continue.dev extension setup

### Development Tools
- **python**: Direct Python client usage
- **curl**: HTTP API testing with curl
- **postman**: Postman collection generation
- **nodejs**: Node.js client implementation

### Frameworks
- **langchain**: LangChain integration patterns
- **llamaindex**: LlamaIndex tool integration
- **autogen**: AutoGen agent configuration

## Examples

### Show All Integration Options

```bash
# Display all available integrations for demo template
mcpt connect demo

# Example output:
╭─────────────────────────────────────────────────────────────╮
│           🔗 Integration Examples for demo                  │
╰─────────────────────────────────────────────────────────────╯

📋 Template Information:
- Name: demo
- Container: mcp-demo-20240115-103045-abc123
- Transport: stdio (recommended)
- Status: ✅ Active

🔧 Available Integrations:
- Claude Desktop
- VS Code MCP Extension
- FastMCP Python Client
- Direct Python Client
- cURL Testing
- Node.js Client

💡 Use --llm option to see specific integration:
  mcpt connect demo --llm claude
  mcpt connect demo --llm vscode
  mcpt connect demo --llm python
```

### Claude Desktop Integration

```bash
# Generate Claude Desktop configuration
mcpt connect demo --llm claude

# Example output:
╭─────────────────────────────────────────────────────────────╮
│              🤖 Claude Desktop Integration                  │
╰─────────────────────────────────────────────────────────────╯

📁 Configuration File Location:
  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  Windows: %APPDATA%\Claude\claude_desktop_config.json

📝 Configuration to Add:
```json
{
  "mcpServers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-demo-20240115-103045-abc123", "python", "-m", "src.server"],
      "env": {
        "MCP_DEBUG": "false"
      }
    }
  }
}
```

🔄 Setup Steps:
1. Stop Claude Desktop completely
2. Edit the configuration file above
3. Add the JSON configuration to the "mcpServers" section
4. Restart Claude Desktop
5. Look for "demo" in the MCP section

✨ Usage Examples:
"Say hello to Alice"
"Get server information"
"Echo back this message: Hello World"

🐛 Troubleshooting:
- If connection fails, verify container is running:
  mcpt status demo
- Check container logs:
  mcpt logs demo
```

### VS Code Integration

```bash
# Generate VS Code configuration
mcpt connect demo --llm vscode

# Example output:
╭─────────────────────────────────────────────────────────────╮
│                📝 VS Code Integration                       │
╰─────────────────────────────────────────────────────────────╯

🔧 Required Extensions:
- MCP Tools for VS Code (Install from Marketplace)

📁 Workspace Settings (.vscode/settings.json):
```json
{
  "mcp.servers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-demo-20240115-103045-abc123", "python", "-m", "src.server"],
      "description": "Demo MCP server with greeting tools"
    }
  }
}
```

🚀 Usage:
1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Type "MCP: List Tools" to see available tools
3. Use "MCP: Call Tool" to execute server functions
4. Integration with GitHub Copilot Chat available

💡 Pro Tips:
- Use in GitHub Copilot Chat: "@mcp demo, say hello to the user"
- Access via command palette for direct tool execution
- Check Output panel (MCP Tools) for debug information
```

### Python Client Integration

```bash
# Generate Python client code
mcpt connect demo --llm python

# Example output:
╭─────────────────────────────────────────────────────────────╮
│              🐍 Python Client Integration                   │
╰─────────────────────────────────────────────────────────────╯

📦 Installation:
```bash
pip install mcp-client asyncio
```

🔧 Basic Usage:
```python
import asyncio
import json
from mcp_client import MCPClient

async def demo_client():
    # Connect to the MCP server
    client = MCPClient()
    await client.connect([
        "docker", "exec", "-i",
        "mcp-demo-20240115-103045-abc123",
        "python", "-m", "src.server"
    ])

    try:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [tool['name'] for tool in tools])

        # Call specific tools
        greeting = await client.call_tool("say_hello", {"name": "World"})
        print("Greeting:", greeting)

        server_info = await client.call_tool("get_server_info", {})
        print("Server info:", server_info)

        echo = await client.call_tool("echo_message", {"message": "Hello MCP!"})
        print("Echo:", echo)

    finally:
        await client.disconnect()

# Run the client
asyncio.run(demo_client())
```

🚀 Advanced Usage:
```python
# Error handling and retry logic
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def mcp_client():
    client = MCPClient()
    try:
        await client.connect([
            "docker", "exec", "-i",
            "mcp-demo-20240115-103045-abc123",
            "python", "-m", "src.server"
        ])
        yield client
    except Exception as e:
        print(f"Connection failed: {e}")
        raise
    finally:
        await client.disconnect()

async def robust_demo():
    async with mcp_client() as client:
        # Your MCP operations here
        result = await client.call_tool("say_hello", {"name": "Alice"})
        return result
```
```

### FastMCP Integration

```bash
# Generate FastMCP integration
mcpt connect demo --llm fastmcp

# Shows FastMCP-specific patterns and best practices
```

### cURL Testing

```bash
# Generate cURL examples for HTTP transport
mcpt connect demo --llm curl

# Example output includes HTTP endpoint testing:
curl -X POST http://localhost:8080/tools/say_hello \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Transport-Specific Examples

### stdio Transport (Recommended)
Most integrations use stdio transport for direct process communication:
```bash
docker exec -i CONTAINER_NAME python -m src.server
```

### HTTP Transport
For web-based integrations:
```bash
# HTTP endpoint available at:
http://localhost:PORT/tools/TOOL_NAME
```

## Integration Patterns

### Synchronous Usage
```python
import subprocess
import json

def call_mcp_tool(container_name, tool_name, params):
    cmd = ["docker", "exec", "-i", container_name, "python", "-m", "src.server"]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params}
    }

    stdout, _ = process.communicate(json.dumps(request).encode())
    return json.loads(stdout.decode())
```

### Asynchronous Usage
```python
import asyncio
import json

async def async_mcp_call(container_name, tool_name, params):
    process = await asyncio.create_subprocess_exec(
        "docker", "exec", "-i", container_name, "python", "-m", "src.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params}
    }

    stdout, _ = await process.communicate(json.dumps(request).encode())
    return json.loads(stdout.decode())
```

## Template-Specific Integration

Different templates provide specialized integration examples:

### File Server Template
```bash
mcpt connect filesystem --llm claude
# Shows examples for file operations, directory listing, etc.
```

### Database Templates
```bash
mcpt connect postgres-server --llm python
# Shows SQL query examples, connection pooling, etc.
```

### API Templates
```bash
mcpt connect api-server --llm curl
# Shows REST API integration patterns
```

## Troubleshooting Integration

The connect command includes troubleshooting sections:

### Common Issues
- **Container not found**: Verify deployment with `status` command
- **Permission denied**: Check Docker permissions
- **Connection timeout**: Verify server is responding
- **Protocol errors**: Check MCP protocol version compatibility

### Debug Commands
```bash
# Test container accessibility
docker exec -i CONTAINER_NAME echo "test"

# Check server response
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | \
  docker exec -i CONTAINER_NAME python -m src.server

# View server logs
mcpt logs TEMPLATE_NAME
```

## Configuration Management

### Environment-Specific Configs
```bash
# Development
mcpt connect demo --llm claude --env dev

# Production
mcpt connect demo --llm claude --env prod
```

### Custom Integration
```bash
# Generate custom integration template
mcpt connect demo --llm custom > integration_template.py
```

## See Also

- [deploy](deploy.md) - Deploy templates before connecting
- [interactive](interactive.md) - Use interactive mode for tool discovery
- [logs](logs.md) - Monitor server activity during integration
