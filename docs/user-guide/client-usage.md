# Client Usage Guide

## Overview

The MCP Template platform provides an enhanced client library for programmatic interaction with Model Context Protocol (MCP) servers. This client provides a high-level Python API for managing templates, calling tools, and deploying servers.

## Installation

The client is included as part of the mcp-template package:

```python
from mcp_template.client_enhanced import MCPClient
```

## Quick Start

### Basic Client Usage

```python
from mcp_template.client_enhanced import MCPClient

# Initialize the client
client = MCPClient()

# List available templates
templates = client.list_templates()
print("Available templates:", list(templates.keys()))

# Get information about a specific template
demo_info = client.get_template_info("demo")
print("Demo template transport:", demo_info["transport"])

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

if result["success"]:
    print("Tool result:", result["result"])
else:
    print("Tool error:", result["error_message"])
```

### Server Management

```python
from mcp_template.client_enhanced import MCPClient

client = MCPClient()

# List running servers
servers = client.list_servers()
print("Running servers:", servers)

# Start a server
deployment_result = client.start_server(
    template_name="demo",
    config={"name": "my-demo-server"}
)

if deployment_result["success"]:
    server_name = deployment_result["deployment_name"]
    print(f"Server started: {server_name}")

    # Stop the server when done
    stop_result = client.stop_server(server_name)
    print("Server stopped:", stop_result["success"])
```

## API Reference

### MCPClient Class

#### Initialization

```python
MCPClient(backend_type: str = "docker", timeout: int = 30)
```

- `backend_type`: Backend for deployments ("docker", "kubernetes", "mock")
- `timeout`: Default timeout for operations

#### Template Methods

##### `list_templates() -> Dict[str, Dict[str, Any]]`

Returns a dictionary of all available templates with their configurations.

```python
templates = client.list_templates()
# Returns: {"demo": {...}, "filesystem": {...}, ...}
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
