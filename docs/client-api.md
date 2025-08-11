# MCP Client - Programmatic Access

The MCP Client provides a clean, programmatic interface for managing MCP server templates without requiring CLI usage. This allows you to integrate MCP functionality directly into your Python applications.

## Quick Start

```python
from mcp_template import MCPClient

# Initialize the client
client = MCPClient()

# List available templates
templates = client.list_templates()
print(f"Available templates: {list(templates.keys())}")

# Deploy a template
deployment = client.deploy("demo", config={
    "greeting": "Hello World!",
    "log_level": "INFO"
})

# List active deployments
deployments = client.list_deployments()

# Discover tools from a deployed template
tools = client.discover_tools("demo")

# Call a specific tool
result = client.call_tool("demo", "greet", {"name": "Alice"})

# Stop the deployment
client.stop("demo")
```

## Key Features

- **Template Management**: List, deploy, and manage templates programmatically
- **Tool Discovery**: Discover available tools from deployed MCP servers
- **Tool Execution**: Execute tools with arguments and get results
- **Error Handling**: Comprehensive error handling with meaningful messages
- **Backend Support**: Works with Docker, Kubernetes, and Mock backends
- **No CLI Dependency**: Pure Python interface

## API Reference

### MCPClient

The main client class for programmatic MCP access.

#### Constructor

```python
MCPClient(backend_type="docker", config_dir=None)
```

- `backend_type`: Deployment backend ("docker", "kubernetes", "mock")
- `config_dir`: Custom configuration directory (defaults to ~/.mcp)

#### Methods

##### `list_templates(as_dict=True)`

List all available MCP server templates.

```python
# As dictionary
templates = client.list_templates()

# As list with status info
template_list = client.list_templates(as_dict=False)
```

##### `get_template_config(template_name)`

Get configuration schema for a specific template.

```python
config_schema = client.get_template_config("demo")
```

##### `deploy(template_name, config=None, name=None, **kwargs)`

Deploy an MCP server template.

```python
deployment = client.deploy("github", config={
    "github_token": "your_token"
})
```

##### `list_deployments()`

List all active deployments.

```python
deployments = client.list_deployments()
```

##### `get_deployment_status(deployment_name)`

Get status of a specific deployment.

```python
status = client.get_deployment_status("demo")
```

##### `stop(template_name, deployment_name=None)`

Stop a running deployment.

```python
client.stop("demo")
```

##### `discover_tools(template_name, endpoint=None)`

Discover tools available in a deployed template.

```python
tools = client.discover_tools("demo")
```

##### `call_tool(template_name, tool_name, arguments, endpoint=None)`

Call a specific tool on a deployed template.

```python
result = client.call_tool("demo", "greet", {"name": "World"})
```

##### `cleanup(template_name=None, all_deployments=False)`

Clean up stopped or failed deployments.

```python
client.cleanup(all_deployments=True)
```

## Examples

### Basic Template Management

```python
from mcp_template import MCPClient

client = MCPClient()

# List available templates
templates = client.list_templates()
for name, template in templates.items():
    print(f"{name}: {template['description']}")

# Get configuration options for a template
config = client.get_template_config("github")
print("Configuration options:")
for prop, details in config.get("properties", {}).items():
    print(f"  {prop}: {details.get('description', 'No description')}")
```

### Deploy and Manage Templates

```python
from mcp_template import MCPClient

client = MCPClient()

# Deploy with configuration
deployment = client.deploy("github", config={
    "github_token": "your_personal_access_token",
    "log_level": "DEBUG"
})

# Check deployment status
status = client.get_deployment_status("github")
print(f"Status: {status}")

# List all deployments
deployments = client.list_deployments()
for deployment in deployments:
    print(f"Deployment: {deployment['name']} - {deployment['status']}")

# Stop when done
client.stop("github")
```

### Tool Discovery and Execution

```python
from mcp_template import MCPClient

client = MCPClient()

# Deploy a template
client.deploy("demo", config={"greeting": "Hello from API!"})

# Discover available tools
tools = client.discover_tools("demo")
print("Available tools:")
for tool in tools:
    print(f"  {tool['name']}: {tool.get('description', 'No description')}")

# Call a tool
result = client.call_tool("demo", "greet", {"name": "API User"})
print(f"Tool result: {result}")

# Cleanup
client.stop("demo")
```

## Error Handling

The client provides comprehensive error handling:

```python
from mcp_template import MCPClient

client = MCPClient()

try:
    # This will raise ValueError for non-existent template
    client.deploy("nonexistent_template")
except ValueError as e:
    print(f"Template error: {e}")

try:
    # This will raise RuntimeError for deployment issues
    client.discover_tools("not_running")
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

## Integration with Existing CLI

The MCP Client works alongside the existing CLI tools:

```python
# Use programmatically
client = MCPClient()
client.deploy("demo")

# CLI still works
# $ mcpt list
# $ mcpt logs demo
# $ mcpt stop demo
```

## Backend Options

Choose your deployment backend:

```python
# Docker (default)
client = MCPClient(backend_type="docker")

# Mock (for testing)
client = MCPClient(backend_type="mock")

# Kubernetes (when available)
client = MCPClient(backend_type="kubernetes")
```