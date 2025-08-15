# Client Usage Guide

## Overview

The MCP Template platform provides a comprehensive client library for programmatic interaction with Model Context Protocol (MCP) servers. This client provides a high-level Python API for managing templates, calling tools, and deploying servers.

## Installation

The client is included as part of the mcp-template package:

```bash
pip install mcp-template
```

```python
from mcp_template.client import MCPClient
```

## Quick Start

### Basic Client Usage

```python
from mcp_template.client import MCPClient

# Initialize the client
client = MCPClient()

# List available templates
templates = client.list_templates()
print("Available templates:", list(templates.keys()))

# Get information about a specific template
demo_info = client.get_template_info("demo")
if demo_info:
    print("Demo template name:", demo_info["name"])

# List tools for a template
tools = client.list_tools("demo")
for tool in tools:
    print(f"Tool: {tool['name']} - {tool.get('description', 'No description')}")

# Call a tool
result = client.call_tool(
    template_name="demo",
    tool_name="say_hello",
    arguments={"name": "World"}
)

if result.get("success"):
    print("Tool result:", result["result"])
else:
    print("Tool error:", result.get("error_message"))
```

### Server Management

```python
from mcp_template.client import MCPClient

client = MCPClient()

# List running servers
servers = client.list_servers()
print("Running servers:", len(servers))

# Start a server
deployment_result = client.start_server(
    template_name="demo",
    config={"greeting": "Hello from API!"}
)

if deployment_result.get("success"):
    deployment_id = deployment_result["deployment_id"]
    print(f"Server started: {deployment_id}")

    # Stop the server when done
    stop_result = client.stop_server(deployment_id)
    print("Server stopped:", stop_result.get("success"))
```

## API Reference

### MCPClient Class

#### Initialization

```python
MCPClient(backend_type: str = "docker", timeout: int = 30)
```

**Parameters:**
- `backend_type`: Backend for deployments ("docker", "kubernetes", "mock")
- `timeout`: Default timeout for operations in seconds

#### Template Methods

##### `list_templates(include_deployed_status: bool = False) -> Dict[str, Dict[str, Any]]`

Returns a dictionary of all available templates with their configurations.

```python
templates = client.list_templates()
# Returns: {"demo": {...}, "filesystem": {...}, ...}

# Include deployment status
templates_with_status = client.list_templates(include_deployed_status=True)
```

##### `get_template_info(template_id: str) -> Optional[Dict[str, Any]]`

Get detailed information about a specific template.

```python
template_info = client.get_template_info("demo")
if template_info:
    print(f"Template: {template_info['name']} v{template_info['version']}")
```

##### `validate_template(template_id: str) -> bool`

Validate if a template exists and is properly configured.

```python
is_valid = client.validate_template("demo")
if not is_valid:
    print("Template is invalid or missing")
```

##### `search_templates(query: str) -> Dict[str, Dict[str, Any]]`

Search templates by name, description, or tags.

```python
results = client.search_templates("file")
# Returns templates matching "file" in name, description, or tags
```

#### Server Management Methods

##### `list_servers(template_name: Optional[str] = None) -> List[Dict[str, Any]]`

List running MCP servers, optionally filtered by template.

```python
# List all servers
all_servers = client.list_servers()

# List servers for specific template
demo_servers = client.list_servers("demo")
```

##### `list_servers_by_template(template: str) -> List[Dict[str, Any]]`

List all servers running a specific template.

```python
servers = client.list_servers_by_template("filesystem")
```

##### `start_server(template_name: str, config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]`

Start a new MCP server instance.

```python
result = client.start_server(
    template_name="demo",
    config={
        "greeting": "Hello World",
        "port": 8080
    },
    transport="http",
    no_pull=False
)

if result["success"]:
    print(f"Server started with ID: {result['deployment_id']}")
```

##### `stop_server(deployment_id: str, timeout: int = 30) -> Dict[str, Any]`

Stop a running server by deployment ID.

```python
result = client.stop_server("demo-12345")
if result["success"]:
    print("Server stopped successfully")
```

##### `stop_all_servers(template: str = None) -> bool`

Stop all servers, optionally filtered by template.

```python
# Stop all servers
client.stop_all_servers()

# Stop all demo servers
client.stop_all_servers("demo")
```

##### `get_server_info(deployment_id: str) -> Optional[Dict[str, Any]]`

Get detailed information about a running server.

```python
info = client.get_server_info("demo-12345")
if info:
    print(f"Server status: {info['status']}")
    print(f"Uptime: {info.get('uptime', 'Unknown')}")
```

##### `get_server_logs(deployment_id: str, lines: int = 100, follow: bool = False) -> Dict[str, Any]`

Get logs from a running server.

```python
logs = client.get_server_logs("demo-12345", lines=50)
if logs["success"]:
    for line in logs["logs"]:
        print(line)
```

#### Tool Management Methods

##### `list_tools(template_or_id: str, discovery_method: str = "auto", force_refresh: bool = False) -> List[Dict[str, Any]]`

List available tools from a template or running server.

```python
# List tools from template
tools = client.list_tools("demo")

# List tools from running server
tools = client.list_tools("demo-12345")

# Force refresh cache
tools = client.list_tools("demo", force_refresh=True)

# Use specific discovery method
tools = client.list_tools("demo", discovery_method="static")
```

##### `call_tool(template_name: str, tool_name: str, arguments: Dict[str, Any], **kwargs) -> Dict[str, Any]`

Call a tool on a template or server.

```python
result = client.call_tool(
    template_name="demo",
    tool_name="say_hello",
    arguments={"name": "Alice"}
)

if result["success"]:
    print("Result:", result["result"])
else:
    print("Error:", result["error_message"])
```

#### Async Connection Methods

For advanced use cases requiring direct MCP protocol communication:

##### `async connect_stdio(template_name: str, config: Optional[Dict[str, Any]] = None) -> str`

Create a direct stdio connection to an MCP server.

```python
import asyncio

async def main():
    client = MCPClient()
    connection_id = await client.connect_stdio("demo")
    # Use connection for direct MCP protocol communication
    await client.disconnect(connection_id)

asyncio.run(main())
```

##### `async list_tools_from_connection(connection_id: str) -> List[Dict[str, Any]]`

List tools through a direct connection.

##### `async call_tool_from_connection(connection_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]`

Call a tool through a direct connection.

##### `async disconnect(connection_id: str) -> bool`

Close a direct connection.

#### Async Server Methods

##### `async start_server_async(template_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

Asynchronously start a server.

##### `async list_tools_async(template_or_id: str, discovery_method: str = "auto") -> List[Dict[str, Any]]`

Asynchronously list tools.

## Configuration

### Client Configuration

```python
# Use different backend
client = MCPClient(backend_type="kubernetes")

# Set custom timeout
client = MCPClient(timeout=60)

# Use mock backend for testing
client = MCPClient(backend_type="mock")
```

### Server Configuration

When starting servers, you can provide configuration in multiple ways:

```python
# Direct config dictionary
config = {
    "allowed_dirs": ["/tmp", "/home/user/data"],
    "read_only": False,
    "max_file_size": "100MB"
}

client.start_server("filesystem", config=config)

# With transport options
client.start_server(
    "demo",
    config={"greeting": "Hello"},
    transport="http",
    no_pull=True
)
```

## Error Handling

All methods return dictionaries with success indicators:

```python
result = client.start_server("demo")
if result["success"]:
    print("Server started:", result["deployment_id"])
else:
    print("Error:", result.get("error", "Unknown error"))
    if "details" in result:
        print("Details:", result["details"])
```

For async methods, exceptions may be raised:

```python
try:
    connection_id = await client.connect_stdio("demo")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Best Practices

### Resource Management

Always clean up resources when done:

```python
# Start server
result = client.start_server("demo")
deployment_id = result["deployment_id"]

try:
    # Use the server
    tools = client.list_tools(deployment_id)
    # ... work with tools ...
finally:
    # Clean up
    client.stop_server(deployment_id)
```

### Connection Pooling

For high-throughput applications, reuse client instances:

```python
# Create once, reuse many times
client = MCPClient()

for task in tasks:
    result = client.call_tool("demo", "process", task)
    # Process result
```

### Error Resilience

Handle network and server errors gracefully:

```python
def safe_call_tool(client, template, tool, args, retries=3):
    for attempt in range(retries):
        try:
            result = client.call_tool(template, tool, args)
            if result["success"]:
                return result
            print(f"Attempt {attempt + 1} failed: {result.get('error')}")
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")

        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    return {"success": False, "error": "All retries failed"}
```

## Examples

### Basic File Operations

```python
client = MCPClient()

# Start filesystem server
server = client.start_server("filesystem", {
    "allowed_dirs": ["/tmp"],
    "read_only": False
})

deployment_id = server["deployment_id"]

# List available tools
tools = client.list_tools(deployment_id)
print("Available file operations:", [t["name"] for t in tools])

# Read a file
content = client.call_tool(deployment_id, "read_file", {
    "path": "/tmp/test.txt"
})

if content["success"]:
    print("File content:", content["result"])

# Clean up
client.stop_server(deployment_id)
```

### GitHub Integration

```python
client = MCPClient()

# Start GitHub server with API token
server = client.start_server("github", {
    "token": "ghp_your_token_here",
    "default_repo": "owner/repo"
})

deployment_id = server["deployment_id"]

# List repository issues
issues = client.call_tool(deployment_id, "list_issues", {
    "state": "open",
    "labels": ["bug"]
})

if issues["success"]:
    for issue in issues["result"]:
        print(f"#{issue['number']}: {issue['title']}")

client.stop_server(deployment_id)
```

### Batch Processing

```python
import asyncio

async def batch_process():
    client = MCPClient()

    # Start multiple servers
    servers = []
    for i in range(3):
        result = await client.start_server_async("demo", {
            "instance_id": i
        })
        servers.append(result["deployment_id"])

    # Process in parallel
    tasks = []
    for i, server_id in enumerate(servers):
        task = client.call_tool(server_id, "process_batch", {
            "batch_id": i,
            "data": f"batch_{i}_data"
        })
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Clean up
    for server_id in servers:
        await client.stop_server(server_id)

    return results

results = asyncio.run(batch_process())
```

##### `get_template_info(template_name: str) -> Optional[Dict[str, Any]]`

Get detailed information about a specific template.

```python
info = client.get_template_info("demo")
# Returns: {"transport": {...}, "description": "...", ...}
```

#### Tool Methods

##### `list_tools(template_name: str) -> List[Dict[str, Any]]`

List all available tools for a template.

```python
tools = client.list_tools("demo")
# Returns: [{"name": "say_hello", "description": "..."}, ...]
```

##### `call_tool(template_name: str, tool_name: str, arguments: Dict[str, Any] = None, config_values: Dict[str, Any] = None) -> Dict[str, Any]`

Call a specific tool with given arguments.

**Parameters:**
- `template_name`: Name of the template containing the tool
- `tool_name`: Name of the tool to call
- `arguments`: Arguments to pass to the tool (optional)
- `config_values`: Configuration values for the template (optional)

**Returns:**
A dictionary with the following structure:
```python
{
    "success": bool,          # Whether the call succeeded
    "result": dict,           # Tool result (if successful)
    "content": list,          # Structured content (if available)
    "is_error": bool,         # Whether this represents an error
    "error_message": str,     # Error message (if failed)
    "raw_output": str         # Raw output from the tool
}
```

**Example:**
```python
result = client.call_tool(
    template_name="demo",
    tool_name="say_hello",
    arguments={"name": "Alice"},
    config_values={"greeting": "Hello"}
)

if result["success"]:
    # Access the result
    content = result["result"]["content"]
    for item in content:
        if item["type"] == "text":
            print(item["text"])
```

#### Server Management Methods

##### `list_servers() -> List[Dict[str, Any]]`

List all running server deployments.

```python
servers = client.list_servers()
# Returns: [{"name": "mcp-demo-...", "status": "running", ...}, ...]
```

##### `start_server(template_name: str, config: Dict[str, Any] = None, custom_name: str = None) -> Dict[str, Any]`

Start a new server deployment.

**Parameters:**
- `template_name`: Name of the template to deploy
- `config`: Configuration for the deployment (optional)
- `custom_name`: Custom name for the deployment (optional)

**Returns:**
```python
{
    "success": bool,
    "deployment_name": str,    # Name of the created deployment
    "error_message": str       # Error message (if failed)
}
```

##### `stop_server(deployment_name: str) -> Dict[str, Any]`

Stop a running server deployment.

**Returns:**
```python
{
    "success": bool,
    "error_message": str       # Error message (if failed)
}
```

## Advanced Usage

### Error Handling

The client provides structured error handling. All methods return dictionaries with success indicators:

```python
result = client.call_tool("demo", "nonexistent_tool")

if not result["success"]:
    if result["is_error"]:
        print(f"Tool execution error: {result['error_message']}")
    else:
        print(f"Client error: {result['error_message']}")
```

### Working with Different Transports

Templates may support different transport methods (stdio, HTTP). The client automatically detects and uses the appropriate transport:

```python
# The client will use stdio transport if supported
result = client.call_tool("demo", "say_hello", {"name": "World"})

# For HTTP-only templates, the client will use HTTP transport
result = client.call_tool("http_template", "some_tool", {"param": "value"})
```

### Configuration and Environment Variables

You can pass configuration values to templates:

```python
result = client.call_tool(
    template_name="demo",
    tool_name="say_hello",
    arguments={"name": "Alice"},
    config_values={
        "greeting_style": "formal",
        "language": "en"
    }
)
```

### Custom Backend Configuration

```python
# Use mock backend for testing
client = MCPClient(backend_type="mock")

# Use longer timeout for slow operations
client = MCPClient(timeout=120)
```

## Integration Examples

### Building a Chatbot Interface

```python
from mcp_template.client_enhanced import MCPClient

class MCPChatbot:
    def __init__(self):
        self.client = MCPClient()
        self.available_tools = {}
        self._load_tools()

    def _load_tools(self):
        """Load all available tools from all templates."""
        templates = self.client.list_templates()
        for template_name in templates:
            tools = self.client.list_tools(template_name)
            for tool in tools:
                self.available_tools[tool["name"]] = {
                    "template": template_name,
                    "description": tool.get("description", "")
                }

    def execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool by name."""
        if tool_name not in self.available_tools:
            return {"error": f"Tool {tool_name} not found"}

        tool_info = self.available_tools[tool_name]
        result = self.client.call_tool(
            template_name=tool_info["template"],
            tool_name=tool_name,
            arguments=kwargs
        )

        return result

    def list_capabilities(self):
        """List all available capabilities."""
        return list(self.available_tools.keys())

# Usage
bot = MCPChatbot()
print("Available tools:", bot.list_capabilities())

result = bot.execute_tool("say_hello", name="User")
if result["success"]:
    print(result["result"]["content"][0]["text"])
```

### Automated Testing Framework

```python
from mcp_template.client_enhanced import MCPClient
import json

class MCPTestRunner:
    def __init__(self):
        self.client = MCPClient(backend_type="mock")  # Use mock for testing

    def run_test_suite(self, test_cases: list):
        """Run a suite of test cases."""
        results = []

        for test_case in test_cases:
            result = self.client.call_tool(
                template_name=test_case["template"],
                tool_name=test_case["tool"],
                arguments=test_case["arguments"]
            )

            results.append({
                "test_name": test_case["name"],
                "success": result["success"],
                "expected": test_case.get("expected"),
                "actual": result.get("result"),
                "error": result.get("error_message")
            })

        return results

    def generate_report(self, results: list):
        """Generate a test report."""
        passed = sum(1 for r in results if r["success"])
        total = len(results)

        print(f"Test Results: {passed}/{total} passed")

        for result in results:
            status = "✓" if result["success"] else "✗"
            print(f"{status} {result['test_name']}")
            if not result["success"]:
                print(f"   Error: {result['error']}")

# Usage
runner = MCPTestRunner()
test_cases = [
    {
        "name": "Basic greeting",
        "template": "demo",
        "tool": "say_hello",
        "arguments": {"name": "Test"}
    }
]

results = runner.run_test_suite(test_cases)
runner.generate_report(results)
```

## Troubleshooting

### Common Issues

1. **Docker not available**: Ensure Docker is installed and running for the default backend.

2. **Template not found**: Check available templates with `client.list_templates()`.

3. **Tool call timeouts**: Increase the timeout parameter when initializing the client.

4. **Permission errors**: Ensure your user has access to Docker (or run with sudo).

### Debugging

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = MCPClient()
# Debug information will now be printed
```

### Using Mock Backend for Development

During development, use the mock backend to avoid Docker dependencies:

```python
client = MCPClient(backend_type="mock")
# All operations will be simulated
```
