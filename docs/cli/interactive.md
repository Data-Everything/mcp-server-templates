# Interactive Command

The `interactive` command launches a comprehensive CLI session for deployment management and direct interaction with MCP servers.

## Usage

```bash
mcp-template interactive
```

## Description

The interactive mode provides a unified interface for managing MCP server deployments and executing tools directly from the command line. This is the primary way to:

- **Manage Deployments**: List, monitor, and control running MCP server deployments
- **Discover Tools**: Automatically discover available tools from deployed servers  
- **Execute Tools**: Run MCP server tools directly without writing integration code
- **Interactive Debugging**: Test and debug MCP server functionality in real-time

## Key Features

### Deployment Management
- List active deployments and their status
- Monitor deployment health and logs
- Start, stop, and manage server lifecycles
- View deployment configuration and metadata

### Tool Discovery & Execution
- Automatically discover tools available in deployed MCP servers
- Execute tools with real-time feedback and error handling
- Pass arguments and configuration dynamically
- Support for both simple and complex tool interactions

### Session Management
- Persistent session across multiple commands
- Command history and tab completion
- Context-aware help and suggestions
- Graceful error handling and recovery

## Example Session

```bash
# Start interactive session
mcp-template interactive

Welcome to MCP Template Interactive CLI
Type 'help' for available commands, 'exit' to quit

# List available deployments
mcp> deployments

# Discover tools from a deployment
mcp> discover github-server

# Execute a tool
mcp> call github-server search_repositories --query "mcp"

# View deployment logs
mcp> logs github-server

# Exit session
mcp> exit
```

## Benefits

- **Faster development**: No need to retype `mcp-template` for each command
- **Better testing**: Quickly iterate between deploy, test, and debug
- **Tool integration**: Direct access to template tools via `call` command
- **User-friendly**: More intuitive for extended usage sessions

## Related Commands

- [`call`](../interactive-cli/call.md) - Execute template tools (available in interactive mode)
- [`deploy`](deploy.md) - Deploy templates for tool calling
- [`list`](list.md) - List available templates
