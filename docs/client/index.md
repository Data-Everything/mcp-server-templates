# MCPClient - Python API Reference

The MCPClient provides a comprehensive Python API for programmatic access to MCP servers and template management. It's designed to be the programmatic counterpart to the CLI interface, offering full automation capabilities for DevOps workflows, CI/CD pipelines, and custom integrations.

## Overview

MCPClient is a high-level Python interface that encapsulates all MCP template functionality in a clean, async-first API. It delegates to the same core modules used by the CLI, ensuring consistent behavior across interfaces.

### Key Features

- **Template Management**: List, inspect, and deploy MCP server templates
- **Server Lifecycle**: Start, stop, monitor, and manage server instances  
- **Tool Execution**: Discover and execute tools from running servers
- **Connection Management**: Direct STDIO connections for advanced scenarios
- **Resource Cleanup**: Automatic cleanup of connections and deployments
- **Backend Flexibility**: Support for Docker, Kubernetes, and mock backends

### Core Design Principles

- **Async-First**: All I/O operations are async for optimal performance
- **Context Manager Support**: Automatic resource cleanup using `async with`
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Type Safety**: Full type hints for excellent IDE support
- **Shared Core**: Uses same core modules as CLI for consistency

## Quick Start

```python
import asyncio
from mcp_template.client import MCPClient

async def main():
    # Use as async context manager for automatic cleanup
    async with MCPClient() as client:
        # List available templates
        templates = client.list_templates()
        print(f"Available templates: {list(templates.keys())}")
        
        # Start a server instance
        server = await client.start_server("demo", {
            "greeting": "Hello from API!"
        })
        
        if server["success"]:
            print(f"Server started: {server['deployment_id']}")
            
            # List available tools
            tools = await client.list_tools("demo")
            print(f"Tools: {[t['name'] for t in tools]}")
            
            # Execute a tool
            result = await client.call_tool("demo", "echo", {
                "message": "Hello World"
            })
            print(f"Tool result: {result}")
            
            # Stop the server
            await client.stop_server(server['deployment_id'])

# Run the example
asyncio.run(main())
```

## Architecture Integration

MCPClient integrates with the refactored core architecture:

```
MCPClient (client.py)
    ↓ delegates to
CoreMCPClient (core/core_client.py)
    ↓ uses
Core Business Logic Modules:
    • TemplateManager - Template discovery and metadata
    • DeploymentManager - Server lifecycle management  
    • ConfigManager - Configuration processing
    • ToolManager - Tool discovery and execution
    • OutputFormatter - Rich formatting utilities
    ↓ delegates to
Backend Services (docker, kubernetes, mock)
```

This architecture ensures that MCPClient and the CLI provide identical functionality through different interfaces.

## API Sections

- **[Template Operations](./templates.md)** - Template discovery, metadata, and listing
- **[Server Management](./servers.md)** - Server lifecycle, monitoring, and control
- **[Tool Execution](./tools.md)** - Tool discovery and execution workflows
- **[Connection Management](./connections.md)** - Direct STDIO connections and advanced scenarios
- **[Configuration](./configuration.md)** - Configuration management and validation
- **[Error Handling](./errors.md)** - Exception handling and error scenarios
- **[Examples](./examples.md)** - Complete usage examples and patterns

## Comparison with CLI

| Functionality | CLI Command | MCPClient Method | Notes |
|---------------|-------------|------------------|-------|
| List templates | `mcpt list` | `client.list_templates()` | Same underlying logic |
| Deploy server | `mcpt deploy demo` | `await client.start_server("demo")` | Async operation |
| List servers | `mcpt servers` | `client.list_servers()` | Same format |
| Execute tool | `mcpt run demo echo '{"msg":"hi"}'` | `await client.call_tool("demo", "echo", {"msg":"hi"})` | Async + structured args |
| Get logs | `mcpt logs demo-123` | `client.get_server_logs("demo-123")` | Same log output |
| Stop server | `mcpt stop demo-123` | `await client.stop_server("demo-123")` | Async operation |

## Version Compatibility

MCPClient is part of the unified refactoring and maintains compatibility with:

- **Core Modules**: Uses latest core module interfaces
- **Backend Services**: Supports all configured backends
- **Template System**: Compatible with all template formats
- **Configuration**: Uses same config processing as CLI

## Next Steps

- Explore the [Template Operations](./templates.md) guide for template management
- Check [Server Management](./servers.md) for deployment workflows  
- See [Examples](./examples.md) for complete integration patterns
