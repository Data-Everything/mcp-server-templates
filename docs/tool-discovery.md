# Tool Discovery System

**Automatic detection and normalization of MCP server capabilities with support for multiple discovery strategies and protocols.**

## Overview

The MCP Platform tool discovery system provides comprehensive, automated detection of tools (capabilities) from MCP servers using multiple discovery strategies. It supports both the official MCP JSON-RPC over stdio protocol and fallback HTTP endpoints for broader compatibility.

### Key Features

- ✅ **MCP Protocol Compliant**: Full support for MCP 2025-06-18 specification with JSON-RPC over stdio
- 🐳 **Docker Integration**: Direct discovery from Docker images with proper container lifecycle management
- 🔍 **Multi-Strategy Discovery**: Static, dynamic, template-based, and Docker probe strategies
- 📊 **Rich CLI Interface**: Beautiful, formatted output with comprehensive tool information
- ⚡ **Caching Support**: Optional caching for improved performance
- 🔄 **Fallback Support**: HTTP endpoint fallback for non-standard implementations

## Discovery Strategies

### 1. MCP Protocol Discovery (Primary)

Uses the official MCP JSON-RPC protocol over stdio transport:

- **Initialize**: Establishes MCP session with proper handshake
- **Tools/List**: Retrieves comprehensive tool definitions with schemas
- **Normalization**: Converts MCP tool definitions to unified format

### 2. Static Discovery

Reads tool definitions from `tools.json` files in template directories:

```json
{
  "tools": [
    {
      "name": "example_tool",
      "description": "Example tool description",
      "category": "general",
      "parameters": {
        "type": "object",
        "properties": {
          "input": {"type": "string"}
        }
      }
    }
  ]
}
```

### 3. Dynamic Discovery (Fallback)

Probes HTTP endpoints for tool information:
- `/tools`, `/api/tools`, `/v1/tools`, `/mcp/tools`
- Supports various response formats

### 4. Template Fallback

Extracts capabilities from existing `template.json` definitions for compatibility.

## CLI Usage

### List Tools for Templates

```bash
# Basic tool discovery for deployed template
mcpt> tools demo

# Force refresh cached results
mcpt> tools demo --refresh

# Ignore cache entirely
mcpt> tools demo --no-cache
```

### Template-Based Tool Discovery

The CLI now supports discovering tools directly from templates, with automatic Docker fallback for templates configured with `tool_discovery: "dynamic"`:

```bash
# Discover tools from a template directory
mcpt> tools my-template

# With configuration values for Docker fallback
mcpt> tools my-template --config "PORT=8080,HOST=localhost"

# Force refresh template tool discovery
mcpt> tools my-template --refresh --config "DEBUG=true"
```

When a template has `tool_discovery: "dynamic"` in its configuration and standard discovery methods fail, the system automatically:

1. **Checks for Docker image**: Looks for `docker_image` and `docker_tag` in template config
2. **Spins up container**: Creates temporary container with provided config values as environment variables
3. **Discovers tools**: Uses MCP protocol or HTTP endpoints to discover available tools
4. **Cleans up**: Automatically removes the temporary container

Example template configuration supporting dynamic discovery:
```json
{
  "name": "My MCP Server",
  "tool_discovery": "dynamic",
  "docker_image": "myregistry/mcp-server",
  "docker_tag": "latest",
  "config_schema": {
    "PORT": {"type": "integer", "default": 8080},
    "DEBUG": {"type": "boolean", "default": false}
  }
}
```

### Discover Tools from Docker Images

```bash
# Discover from MCP filesystem server
mcpt> tools --image mcp/filesystem /tmp

# Discover from custom server with arguments
mcpt> tools --image myregistry/mcp-server:latest config.json --port 8080

# Example output for filesystem server
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    🐳 Docker Tool Discovery            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
✅ Discovered 11 tools via docker_mcp_stdio

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name            ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ read_file            │ Read complete file contents...       │
│ write_file           │ Create or overwrite files...         │
│ list_directory       │ List directory contents...           │
│ create_directory     │ Create directories...                │
│ ...                  │ ...                                   │
└──────────────────────┴───────────────────────────────────────┘
```

## Template Configuration

Configure tool discovery behavior in `template.json`:

```json
{
  "name": "My MCP Server",
  "description": "An example MCP server template",
  "version": "1.0.0",
  "tool_discovery": {
    "method": "mcp_protocol",
    "fallback_methods": ["http", "static"],
    "cache_ttl": 300,
    "timeout": 30
  },
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"]
  },
  "mcp_protocol": {
    "version": "2025-06-18",
    "capabilities": {
      "tools": {}
    }
  }
}
```

#### Configuration Fields

- **`tool_discovery`**: Discovery method (`"static"`, `"dynamic"`, or `"none"`)
  - `"static"`: Uses pre-defined tools from `tools.json` file
  - `"dynamic"`: Probes running server endpoints, with Docker fallback for templates
  - `"none"`: Disables tool discovery
- **`tool_endpoint`**: Custom endpoint for dynamic discovery (default: `"/tools"`)
- **`has_image`**: Whether the template has a Docker image for probing
- **`docker_image`**: Docker image name for dynamic discovery fallback
- **`docker_tag`**: Docker image tag (default: `"latest"`)
- **`config_schema`**: Schema for configuration values passed to Docker containers
- **`origin`**: Template origin (`"internal"` or `"external"`)

### Static Tool Discovery

For static discovery, create a `tools.json` file in your template directory:

```json
{
  "tools": [
    {
      "name": "hello_world",
      "description": "Generate a greeting message",
      "category": "greeting",
      "parameters": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "Name to greet"
          }
        }
      }
    }
  ],
  "metadata": {
    "discovery_method": "static",
    "last_updated": "2024-07-29T00:00:00Z"
  }
}
```

### Dynamic Tool Discovery

For dynamic discovery, the system will probe these endpoints in order:

1. Custom endpoint (if specified in `tool_endpoint`)
2. `/tools`
3. `/get_tools`
4. `/capabilities`
5. `/metadata`
6. `/openapi.json`

The system expects responses in these formats:

#### Standard Tools Format
```json
{
  "tools": [
    {
      "name": "tool_name",
      "description": "Tool description",
      "parameters": {...}
    }
  ]
}
```

#### Capabilities Format
```json
{
  "capabilities": [
    {
      "name": "capability_name",
      "description": "Capability description"
    }
  ]
}
```

#### OpenAPI Format
```json
{
  "paths": {
    "/api/endpoint": {
      "get": {
        "summary": "Endpoint description",
        "parameters": [...]
      }
    }
  }
}
```

## Caching

Tool discovery results are automatically cached in `~/.mcp/cache/` for 6 hours by default.

### Cache Management

```python
from mcp_template.tools import CacheManager

cache = CacheManager()

# Get cache info
info = cache.get_cache_info()
print(f"Total files: {info['total_files']}")

# Clear expired entries
removed = cache.clear_expired()
print(f"Removed {removed} expired entries")

# Clear all cache
cache.clear_all()
```

## Programmatic Usage

### Tool Discovery

```python
from mcp_template.tools import ToolDiscovery
from pathlib import Path

discovery = ToolDiscovery()

# Discover tools for a template
result = discovery.discover_tools(
    template_name="my-template",
    template_dir=Path("templates/my-template"),
    template_config={
        "tool_discovery": "static",
        "tool_endpoint": "/api/tools"
    },
    use_cache=True,
    force_refresh=False
)

print(f"Found {len(result['tools'])} tools")
for tool in result['tools']:
    print(f"- {tool['name']}: {tool['description']}")
```

### Docker Probe

```python
from mcp_template.tools import DockerProbe

probe = DockerProbe()

# Discover tools from Docker image
result = probe.discover_tools_from_image("myregistry/mcp-server:latest")

if result:
    print(f"Discovered {len(result['tools'])} tools from image")
else:
    print("Failed to discover tools")
```

## Best Practices

### Template Authors

1. **Choose appropriate discovery method**:
   - Use `"static"` for stable, well-defined tools
   - Use `"dynamic"` for servers with runtime tool generation
   - Use `"none"` only if tools cannot be discovered

2. **Provide tools.json for static discovery**:
   - Include comprehensive tool descriptions
   - Use consistent parameter schemas
   - Keep metadata up to date

3. **Implement standard endpoints for dynamic discovery**:
   - Prefer `/tools` endpoint with standard format
   - Include proper error handling and timeouts
   - Support JSON content negotiation

### Platform Users

1. **Use caching effectively**:
   - Let cache work automatically for better performance
   - Use `--refresh` when you know tools have changed
   - Use `--no-cache` only for debugging

2. **Monitor discovery results**:
   - Check discovery method in tool listings
   - Verify tool counts and descriptions
   - Report issues with external templates

## Error Handling

The system gracefully handles various error conditions:

- **Missing tools.json**: Falls back to template.json or dynamic discovery
- **Network timeouts**: Logs debug messages and continues with fallback
- **Invalid JSON**: Logs warnings and skips malformed responses
- **Container failures**: Automatically cleans up failed Docker containers

## Extension Points

The system is designed for extensibility:

### Custom Discovery Methods

```python
class CustomToolDiscovery(ToolDiscovery):
    def _discover_custom_tools(self, template_name, config):
        # Implement custom discovery logic
        return {
            "tools": [...],
            "discovery_method": "custom",
            "timestamp": time.time()
        }
```

### Custom Tool Formats

```python
def normalize_custom_format(self, raw_data):
    # Convert custom format to standard tool format
    return [
        {
            "name": item["function_id"],
            "description": item["help_text"],
            "parameters": item["input_schema"]
        }
        for item in raw_data["functions"]
    ]
```

## Troubleshooting

### Common Issues

1. **No tools discovered**:
   - Check template configuration
   - Verify tools.json exists for static discovery
   - Test endpoints manually for dynamic discovery

2. **Cache not working**:
   - Check permissions on `~/.mcp/cache/`
   - Verify cache timestamps
   - Use `--no-cache` to bypass temporarily

3. **Docker probe failures**:
   - Ensure Docker is running
   - Check image exists and is accessible
   - Verify container exposes HTTP endpoints

4. **Timeout errors**:
   - Check network connectivity
   - Verify server is responding
   - Consider increasing timeout values

### Debug Mode

Enable debug logging to see detailed discovery process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
mcpt> tools my-template
```
