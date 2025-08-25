# Interactive Command

The `interactive` command launches a comprehensive CLI session for deployment management and direct interaction with MCP servers.

## Usage

```bash
mcpt interactive
```

## Description

The interactive mode provides a unified interface for managing MCP server deployments and executing tools directly from the command line. This modern CLI includes command history, tab completion, and template session management for an enhanced user experience.

This is the primary way to:

- **Manage Deployments**: List, monitor, and control running MCP server deployments
- **Discover Tools**: Automatically discover available tools from deployed servers
- **Execute Tools**: Run MCP server tools directly without writing integration code
- **Interactive Debugging**: Test and debug MCP server functionality in real-time
- **Template Selection**: Select a template once and use all commands without repeating the template name

## Key Features

### Enhanced User Experience
- **Command History**: Use up/down arrow keys to navigate through previous commands
- **Tab Completion**: Auto-complete commands, template names, and configuration keys
- **Dynamic Prompts**: Visual indication of currently selected template
- **Rich Formatting**: Beautiful tables and colored output for better readability

### Template Session Management
- **Template Selection**: Use `select <template>` to set a default template for the session
- **Session Persistence**: Selected template persists across commands until changed
- **Smart Arguments**: Commands automatically use selected template when no template is specified

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
- Command history and tab completion (readline support)
- Context-aware help and suggestions
- Graceful error handling and recovery

## Command History & Completion

The interactive CLI includes built-in support for command history and tab completion:

- **Command History**: Use ↑/↓ arrow keys to navigate through previous commands
  - History is maintained during the session
  - Commands are saved to `~/.mcp/.mcpt_history` and restored between sessions
  - The prompt stays visible when navigating history
- **Tab Completion**: Press Tab to auto-complete:
  - Commands (e.g., `tem[Tab]` → `templates`)
  - Template names (e.g., `select dem[Tab]` → `select demo`)
  - Configuration keys (e.g., `config back[Tab]` → `config backend`)
- **History Persistence**: Command history is saved and restored between sessions
- **Clean Prompt Display**: The prompt remains stable when using arrow keys

## Template Selection Workflow

Use template selection to streamline repetitive operations:

```bash
# Traditional approach (repetitive)
mcpt> tools demo
mcpt> call demo say_hello '{"name": "Alice"}'
mcpt> config demo port=8080

# Enhanced approach (with template selection)
mcpt> select demo        # Select template once
✅ Selected template: demo

mcpt(demo)> tools        # No need to specify template
mcpt(demo)> call say_hello '{"name": "Alice"}'
mcpt(demo)> config port=8080
mcpt(demo)> unselect     # Return to global mode
```

## Example Session

```bash
# Start interactive session
mcpt interactive
✨ Command history and tab completion enabled

# List available templates
mcpt> templates

# Select a template for the session
mcpt> select demo
✅ Selected template: demo

# List tools (uses selected template automatically)
mcpt(demo)> tools

# Call a tool with force refresh
mcpt(demo)> tools --force-refresh

# Execute a tool
mcpt(demo)> call say_hello '{"name": "World"}'

# View servers
mcpt(demo)> servers

# Unselect template
mcpt(demo)> unselect
📤 Unselected template: demo

# Exit session
mcpt> exit
Goodbye!
```

## Available Commands

The interactive CLI supports all standard MCP operations plus enhanced session management:

### Core Commands
- `help` - Show help information
- `templates` - List available templates
- `servers` - List running servers
- `tools [template] [--force-refresh] [--help-info]` - List tools
- `call <template|tool> <tool> <args>` - Execute a tool
- `deploy <template>` - Deploy a template
- `logs <deployment>` - View deployment logs
- `stop <deployment>` - Stop a deployment
- `remove <deployment>` - Remove a deployment
- `cleanup` - Clean up stopped containers

### Session Management
- `select <template>` - Select template for session
- `unselect` - Unselect current template
- `config [template] <key>=<value>` - Set configuration
- `exit` / `quit` - Exit interactive session

### Enhanced Features
- **Smart Template Detection**: Commands automatically detect whether the first argument is a template name or parameter
- **Force Refresh**: Use `--force-refresh` flag with tools command to bypass cache
- **Rich Output**: All commands feature beautiful tables and colored output
- **Error Recovery**: Graceful error handling with helpful suggestions

## Benefits

- **Faster development**: No need to retype `mcp-template` for each command
- **Better testing**: Quickly iterate between deploy, test, and debug
- **Tool integration**: Direct access to template tools via `call` command
- **User-friendly**: More intuitive for extended usage sessions

## Related Commands

- [`call`](../interactive-cli/call.md) - Execute template tools (available in interactive mode)
- [`deploy`](deploy.md) - Deploy templates for tool calling
- [`list`](list.md) - List available templates
