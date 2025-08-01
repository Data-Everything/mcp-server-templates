# discover-tools

**[DEPRECATED] Use `tools --image` instead. This command will be removed in a future version.**

⚠️ **This command is deprecated**. The functionality has been merged into the unified `tools` command. 

**Migration**: Replace `discover-tools --image` with `tools --image`:

```bash
# Old (deprecated)
mcp-template discover-tools --image mcp/filesystem /tmp

# New (recommended) 
mcp-template tools --image mcp/filesystem /tmp
```

---

## Synopsis

```bash
mcp-template discover-tools --image IMAGE [SERVER_ARGS...]
```

## Description

The `discover-tools` command probes Docker images to discover MCP server capabilities using the official MCP JSON-RPC over stdio protocol. It automatically handles container lifecycle management, protocol negotiation, and presents results in a beautiful, formatted interface.

This command is particularly useful for:
- **Evaluating MCP servers** before deployment
- **Understanding available tools** and their capabilities
- **Debugging MCP server implementations**
- **Generating integration documentation**

## Options

| Option | Description | Required |
|--------|-------------|----------|
| `--image IMAGE` | Docker image name to probe | Yes |
| `SERVER_ARGS` | Arguments to pass to the MCP server | No |

## MCP Protocol Support

The tool discovery system uses the official MCP 2025-06-18 specification:

1. **Initialize**: Establishes MCP session with proper handshake
2. **Tools/List**: Retrieves comprehensive tool definitions
3. **Normalization**: Converts to unified format for display

### Fallback Strategy

If MCP stdio fails, the system automatically falls back to:
- HTTP endpoint probing (`/tools`, `/api/tools`, etc.)
- Static tool definition discovery
- Template metadata extraction

## Examples

### Basic Discovery

```bash
# Discover tools from filesystem server
mcp-template discover-tools --image mcp/filesystem /tmp

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
mcp-template discover-tools \
  --image myregistry/postgres-mcp:latest \
  --host localhost --port 5432 --database mydb

# API server with authentication
mcp-template discover-tools \
  --image company/api-mcp:v1.0 \
  --api-key $API_TOKEN --base-url https://api.example.com

# File server with multiple directories
mcp-template discover-tools \
  --image mcp/filesystem \
  /data /workspace /tmp
```

### Advanced Examples

```bash
# Custom image with complex configuration
mcp-template discover-tools \
  --image custom/research-mcp:latest \
  --config config.json \
  --model gpt-4 \
  --research-dir /research \
  --output-format json

# Development server with debug mode
mcp-template discover-tools \
  --image local/dev-mcp:latest \
  --debug \
  --log-level trace \
  --dev-mode
```

## Output Format

The command provides rich, structured output including:

### Tool Information
- **Name**: Tool identifier for calling
- **Description**: Human-readable explanation
- **Category**: Tool classification (mcp, general, etc.)
- **Parameters**: JSON schema for input validation

### Discovery Metadata
- **Discovery Method**: How tools were discovered (mcp_stdio, http, static)
- **Server Information**: MCP server name and version
- **Command Used**: Exact Docker command executed
- **Timestamp**: When discovery was performed

### Usage Examples
- **MCP Client Code**: Python code snippets for tool usage
- **Integration Examples**: Ready-to-use integration patterns
- **Error Handling**: Common error scenarios and solutions

## JSON Output

For programmatic usage, pipe to `jq` or similar tools:

```bash
# Get raw JSON data
mcp-template discover-tools --image mcp/filesystem /tmp | \
  grep -A 1000 "Raw result:" | tail -n +2

# Extract just tool names
mcp-template discover-tools --image mcp/filesystem /tmp 2>/dev/null | \
  jq -r '.tools[].name'

# Get tools with descriptions
mcp-template discover-tools --image mcp/filesystem /tmp 2>/dev/null | \
  jq -r '.tools[] | "\(.name): \(.description)"'
```

## Container Management

The discovery process automatically handles:
- **Container Creation**: Temporary containers with unique names
- **Lifecycle Management**: Automatic cleanup on success or failure
- **Resource Limits**: Appropriate CPU and memory constraints
- **Network Isolation**: Secure container networking
- **Timeout Handling**: Graceful termination after timeout

## Troubleshooting

### Common Issues

#### Image Not Found
```bash
❌ Docker image 'nonexistent/image' not found
```
**Solution**: Verify image exists and you have pull permissions.

#### MCP Protocol Errors
```bash
❌ MCP initialization failed: Expecting value: line 1 column 1 (char 0)
```
**Solutions**:
- Ensure image implements MCP protocol correctly
- Check if image requires specific arguments
- Try with different server arguments

#### Permission Errors
```bash
❌ Permission denied: Cannot access /restricted
```
**Solution**: Use accessible directories or configure image permissions.

#### Timeout Errors
```bash
❌ Timeout waiting for MCP response (30s)
```
**Solutions**:
- Server may be slow to start - this is normal for complex servers
- Check if server arguments are correct
- Verify image is functioning properly

### Debug Mode

For detailed troubleshooting information:

```bash
# Enable debug logging
MCP_DEBUG=1 mcp-template discover-tools --image mcp/filesystem /tmp

# Check container logs manually
docker run -it --rm mcp/filesystem /tmp
# Then manually send MCP commands via stdin
```

## Integration with Templates

Use discovered tools to inform template creation:

```bash
# Discover tools
mcp-template discover-tools --image custom/mcp-server:latest > tools.json

# Create template with discovered capabilities
mcp-template create my-template --from-discovery tools.json

# Deploy template
mcp-template deploy my-template
```

## Performance Considerations

- **Container Startup**: First run may be slower due to image pull
- **Caching**: Subsequent runs with same image are faster
- **Parallel Discovery**: Can run multiple discoveries simultaneously
- **Resource Usage**: Minimal overhead, containers are ephemeral

## Security Notes

- **Container Isolation**: Discovery runs in isolated containers
- **Network Access**: Limited network access during discovery
- **File System**: No persistent changes to host system
- **Cleanup**: Automatic cleanup prevents resource leaks

## See Also

- [tools](tools.md) - **NEW**: Unified command for listing tools from templates and Docker images
- [deploy](deploy.md) - Deploy templates after discovery
- [connect](connect.md) - Generate integration examples
- [Tool Discovery System](../tool-discovery.md) - Technical details

## Migration Guide

This command has been deprecated in favor of the unified `tools` command:

| Old Command | New Command |
|-------------|-------------|
| `discover-tools --image IMAGE` | `tools --image IMAGE` |
| `discover-tools --image IMAGE arg1 arg2` | `tools --image IMAGE arg1 arg2` |

All functionality, options, and behavior remain exactly the same.
