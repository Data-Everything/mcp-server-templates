# Filesystem Usage Guide

## Overview

Local filesystem access with configurable allowed paths.

## Available Tools

### example

**Description**: A simple example tool

**Example Usage**: Say hello to the world

**Parameters**:
- No parameters required

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)


### Configuration File

You can also use a configuration file in JSON format:

```json
{
  "log_level": "INFO"

}
```

## Examples

### Basic Usage

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_server():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])

            # Use a tool
            result = await session.call_tool("example_tool", {})
            print("Result:", result)
```

### Docker Usage

```bash
# Build and run
docker build -t {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")} .
docker run {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")}
```

## Troubleshooting

### Common Issues

1. **Configuration not loaded**: Check environment variables are set correctly
2. **Tool not found**: Verify the tool name matches exactly
3. **Connection failed**: Ensure the server is running and accessible

### Debug Mode

Set `DEBUG=1` environment variable for verbose logging.
