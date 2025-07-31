# tools

**List and analyze tools available from MCP server templates or discover tools from Docker images.**

## Synopsis

```bash
# For deployed templates
python -m mcp_template tools TEMPLATE [OPTIONS]

# For Docker images
python -m mcp_template tools --image IMAGE [SERVER_ARGS...] [OPTIONS]
```

## Description

The `tools` command discovers and displays tools (capabilities) available from MCP servers. It supports two modes:

1. **Template Mode**: Analyzes tools from deployed MCP server templates in your workspace
2. **Docker Discovery Mode**: Discovers tools directly from Docker images using the MCP protocol

The command uses multiple discovery strategies including MCP protocol communication, static analysis, and dynamic probing to provide comprehensive tool information.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE` | Name of the deployed template to analyze (template mode) |
| `SERVER_ARGS` | Arguments to pass to the MCP server (Docker mode) |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--image IMAGE` | Docker image name to discover tools from (enables Docker mode) | None |
| `--no-cache` | Ignore cached results and perform fresh discovery | Use cache |
| `--refresh` | Force refresh cached results | Use cache |

## Discovery Methods

The tools command uses a multi-strategy approach:

### Template Mode (Default)
1. **MCP Protocol**: Direct communication with running server
2. **Static Discovery**: Analysis of template configuration files
3. **Dynamic Probing**: HTTP endpoint discovery
4. **Template Metadata**: Fallback to template definitions

### Docker Mode (--image)
1. **MCP Protocol**: Direct communication via stdio transport
2. **HTTP Fallback**: Endpoint probing if stdio fails
3. **Container Management**: Automatic container lifecycle

## Examples

### Template Mode

```bash
# List tools from demo template
python -m mcp_template tools demo

# Example output:
╭─────────────────────────────────────────────────────────────╮
│                    📋 Template Tools: demo                  │
╰─────────────────────────────────────────────────────────────╯

✅ Discovered 3 tools via mcp_protocol

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name            ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ say_hello            │ Greet someone with a personalized... │
│ get_server_info      │ Get information about the server...  │
│ echo_message         │ Echo back the provided message...    │
└──────────────────────┴───────────────────────────────────────┘

💡 Usage Examples:
  # Deploy template: python -m mcp_template deploy demo
  # Connect to Claude: python -m mcp_template connect demo --llm claude
  # View logs: python -m mcp_template logs demo
```

### Docker Discovery Mode

```bash
# Discover tools from filesystem server
python -m mcp_template tools --image mcp/filesystem /tmp

# Example output:
╭──────────────────────────────────────────────────────────────╮
│                    🐳 Docker Tool Discovery                  │
╰──────────────────────────────────────────────────────────────╯

✅ Discovered 11 tools via docker_mcp_stdio

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name            ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ read_file            │ Read complete file contents...       │
│ write_file           │ Create or overwrite files...         │
│ list_directory       │ List directory contents...           │
│ create_directory     │ Create directories...                │
│ directory_tree       │ Get recursive tree view...           │
│ move_file            │ Move or rename files...              │
│ search_files         │ Search for files by pattern...       │
│ get_file_info        │ Get detailed file metadata...        │
│ edit_file            │ Make line-based edits...             │
│ read_multiple_files  │ Read multiple files efficiently...   │
│ list_allowed_directories │ List accessible directories...   │
└──────────────────────┴───────────────────────────────────────┘

💡 Usage Example:
  from mcp_template.tools.mcp_client_probe import MCPClientProbe
  client = MCPClientProbe()
  result = client.discover_tools_from_docker_sync('mcp/filesystem', ['/tmp'])
```

### Custom MCP Servers

```bash
# Database server with connection parameters
python -m mcp_template tools --image myregistry/postgres-mcp:latest \
  --host localhost --port 5432 --database mydb

# API server with authentication
python -m mcp_template tools --image company/api-mcp:v1.0 \
  --api-key $API_TOKEN --base-url https://api.example.com

# File server with multiple directories
python -m mcp_template tools --image mcp/filesystem \
  /data /workspace /tmp
```

### File Server Tools

```bash
# List file server tools
python -m mcp_template tools file-server

# Example output shows comprehensive file operations:
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name            ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ read_file            │ Read complete contents of a file...  │
│ write_file           │ Create or overwrite file content...  │
│ list_directory       │ Get detailed directory listing...    │
│ create_directory     │ Create directories recursively...    │
│ delete_file          │ Remove files and directories...      │
│ move_file            │ Move or rename files...              │
│ search_files         │ Search for files by pattern...       │
│ get_file_info        │ Get detailed file metadata...        │
│ watch_directory      │ Monitor directory changes...         │
└──────────────────────┴───────────────────────────────────────┘
```

### Cache Management

```bash
# Force refresh of cached tool information
python -m mcp_template tools demo --refresh

# Ignore cache and perform fresh discovery
python -m mcp_template tools demo --no-cache

# Use cached results (default behavior)
python -m mcp_template tools demo
```

## Detailed Tool Information

The tools command provides comprehensive information for each discovered tool:

### Tool Metadata
- **Name**: Unique identifier for the tool
- **Description**: Human-readable explanation of functionality
- **Category**: Classification (mcp, general, file, database, etc.)
- **Version**: Tool version if available

### Parameter Schema
- **Input Schema**: JSON Schema defining expected parameters
- **Required Parameters**: Which parameters are mandatory
- **Optional Parameters**: Additional configuration options
- **Parameter Types**: Data types and validation rules

### MCP Information
- **Input Schema**: Original MCP tool input schema
- **Output Schema**: Expected response format
- **Protocol Version**: MCP protocol version used

## Integration Examples

The command also provides ready-to-use integration examples:

### Python Integration
```python
# FastMCP client usage
from mcp_template.client import MCPClient

async def use_tools():
    client = MCPClient("demo-container-name")
    await client.connect()

    # Use discovered tools
    result = await client.call_tool("say_hello", {"name": "World"})
    info = await client.call_tool("get_server_info", {})

    await client.disconnect()
```

### Claude Desktop Integration
```json
{
  "mcpServers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

### VS Code Integration
```json
{
  "mcp.servers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "CONTAINER_NAME", "python", "-m", "src.server"]
    }
  }
}
```

## Tool Categories

Tools are automatically categorized for better organization:

### File Operations (`file`)
- File reading/writing operations
- Directory manipulation
- File system navigation

### Database Operations (`database`)
- Query execution
- Schema management
- Data manipulation

### API Operations (`api`)
- HTTP requests
- Authentication
- Data transformation

### MCP Protocol (`mcp`)
- Standard MCP server tools
- Protocol-specific functionality
- Server management

## Output Formats

### Table Format (Default)
Rich table with formatted columns showing tool names, descriptions, and metadata.

### JSON Format
For programmatic usage:
```bash
# Pipe to jq for JSON processing
python -m mcp_template tools demo 2>/dev/null | \
  grep -A 1000 "Tools data:" | tail -n +2 | jq '.'
```

### Compact Format
```bash
# Get just tool names
python -m mcp_template tools demo 2>/dev/null | \
  grep "│" | grep -E "^\│\s+\w+" | awk '{print $2}'
```

## Error Handling

### Template Not Found
```bash
❌ Template 'nonexistent' not found
Available templates: demo, file-server, postgres-server
```
**Solution**: Use `python -m mcp_template list` to see available templates.

### Template Not Deployed
```bash
❌ Template 'demo' is not currently deployed
```
**Solution**: Deploy the template first with `python -m mcp_template deploy demo`.

### Discovery Failed
```bash
⚠️  Could not discover tools via MCP protocol, falling back to static discovery
✅ Discovered 2 tools via static_discovery
```
**Note**: This is normal - the system automatically tries multiple discovery methods.

### No Tools Found
```bash
⚠️  No tools discovered for template 'custom-template'
This may indicate:
- Template has no tools defined
- Server is not responding
- Configuration issues
```
**Solutions**:
- Check template configuration
- Verify server is running: `python -m mcp_template status template-name`
- Check server logs: `python -m mcp_template logs template-name`

## Performance and Caching

### Caching Behavior
- **Default**: Results cached for 5 minutes
- **Cache Location**: `~/.mcp-template/cache/tools/`
- **Cache Key**: Based on template name and configuration hash

### Cache Commands
```bash
# View cache status
ls -la ~/.mcp-template/cache/tools/

# Clear cache for specific template
rm ~/.mcp-template/cache/tools/demo.json

# Clear all tool cache
rm -rf ~/.mcp-template/cache/tools/
```

## Advanced Usage

### Discovery Strategy Override
```bash
# Force specific discovery method (advanced)
MCP_DISCOVERY_METHOD=static python -m mcp_template tools demo

# Enable debug logging
MCP_DEBUG=1 python -m mcp_template tools demo --refresh
```

### Custom Tool Definitions
Add custom tool definitions to template directory:
```bash
# Add tools.json to template
echo '{"tools": [...]}' > templates/demo/tools.json

# Refresh to pick up changes
python -m mcp_template tools demo --refresh
```

## See Also

- ~~[discover-tools](discover-tools.md)~~ - **DEPRECATED**: Use `tools --image` instead
- [connect](connect.md) - Generate integration examples
- [deploy](deploy.md) - Deploy templates
- [config](config.md) - View template configuration

## Migration from discover-tools

The `discover-tools` command has been merged into the unified `tools` command. Update your scripts:

```bash
# Old (deprecated)
python -m mcp_template discover-tools --image mcp/filesystem /tmp

# New (recommended)
python -m mcp_template tools --image mcp/filesystem /tmp
```

The old command will continue to work but will show a deprecation warning.
