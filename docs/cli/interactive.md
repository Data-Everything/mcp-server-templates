# Interactive Command

The `interactive` command launches an interactive CLI session for streamlined template management and testing.

## Usage

```bash
mcp-template interactive
```

## Description

The interactive mode provides a command-line interface with enhanced features:

- **Streamlined workflow**: Execute multiple commands without retyping the base command
- **Command completion**: Tab completion for commands and arguments
- **Session persistence**: Maintain context across multiple operations
- **Enhanced tool calling**: Use the `call` command for tool execution
- **Real-time feedback**: Immediate responses to your actions

## Available Commands in Interactive Mode

Once in interactive mode, you can use all standard mcp-template commands plus:

- `call` - Execute tools from deployed templates (replaces deprecated `run-tool`)
- `exit` or `quit` - Exit interactive session
- All other CLI commands work without the `mcp-template` prefix

## Examples

Start interactive session:
```bash
mcp-template interactive
```

Example interactive session:
```
$ mcp-template interactive
Welcome to MCP Template Interactive CLI
Type 'help' for available commands, 'exit' to quit

mcp> list
[Shows available templates]

mcp> deploy github
[Deploys GitHub template]

mcp> call list_repositories
[Calls tool from deployed template]

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
