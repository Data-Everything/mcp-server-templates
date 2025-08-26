# MCP Interactive CLI: Command Reference

This document provides detailed information about each command available in the MCP Interactive CLI. Each command can be run interactively in the CLI session.

---

## Template Selection

### `select`
**Description:** Select a template for the session to avoid repeating template names.
**Usage:**
```
select <template_name>
```
**Behavior:**
- Sets the template as the default for the session
- Subsequent commands can omit the template name
- Shows confirmation with template details

### `unselect`
**Description:** Unselect the currently selected template.
**Usage:**
```
unselect
```
**Behavior:**
- Clears the session template selection
- Commands will require explicit template names again

---

## Template & Server Management

### `templates`
**Description:** List all available MCP templates.
**Usage:**
```
templates [--status] [--all-backends]
```
**Options:**
- `--status`: Show template configuration status
- `--all-backends`: Show templates from all backends
**Behavior:**
- Shows a table of all templates, their transport, default port, available tools, and description.
- Useful for discovering what you can deploy and use.

### `servers`
**Description:** List all deployed MCP servers currently running.
**Usage:**
```
servers [--template NAME] [--all-backends]
```
**Options:**
- `--template NAME`: Filter by specific template
- `--all-backends`: Show servers from all backends
**Behavior:**
- Shows a table of active servers with details (ID, template, transport, status, endpoint, ports, etc).
- Only running servers are shown.
- Beautified output using Rich tables.

### `deploy`
**Description:** Deploy a template as an MCP server.
**Usage:**
```
deploy [template] [options]
```
**Options:**
- Various deployment options (transport, port, backend, etc.)
**Behavior:**
- Deploys the specified template as a running server
- Prompts for missing configuration if needed
- Shows deployment status and connection details

---

## Tool Operations

### `tools`
**Description:** List available tools for a template.
**Usage:**
```
tools [template] [--force-refresh] [--help-info]
```
**Options:**
- `--force-refresh`: Force server-side tool discovery (MCP probe only, no static fallback).
- `--help-info`: Show detailed help for the template and its tools.
**Behavior:**
- Lists all tools for the specified template, with details and parameters.
- If `--help-info` is used, shows configuration schema and usage examples.
- If `--force-refresh` is used, skips static tool discovery.
- Uses selected template if no template specified.

### `call`
**Description:** Call a tool from a template (via stdio or HTTP transport).
**Usage:**
```
call [template] <tool_name> [json_args] [options]
```
**Arguments:**
- `json_args`: Optional JSON string of arguments for the tool (e.g. '{"param": "value"}').
**Options:**
- `--config-file`: Path to JSON config file
- `--env KEY=VALUE`: Environment variables (can be used multiple times)
- `--config KEY=VALUE`: Temporary config KEY=VALUE pairs (can be used multiple times)
- `--raw`: Show raw JSON response instead of formatted table
- `--stdio`: Force stdio transport mode
**Behavior:**
- Executes the specified tool, prompting for missing configuration if needed.
- Handles both stdio and HTTP transports.
- Beautifies the tool response and error output.
- Uses selected template if no template specified.

---

## Configuration Management

### `configure`
**Description:** Set configuration for a template interactively.
**Usage:**
```
configure [template] <key>=<value> [<key2>=<value2> ...]
```
**Behavior:**
- Stores configuration in session and cache.
- Masks sensitive values in output.
- Supports multiple config values at once.
- Uses selected template if no template specified.

### `show-config`
**Description:** Show current configuration for a template.
**Usage:**
```
show-config [template]
```
**Behavior:**
- Displays all config values for the template, masking sensitive values.
- Shows comprehensive property information with status indicators:
  - ✅ SET - Property has been configured
  - ❌ REQUIRED - Required property not yet set
  - ⚪ OPTIONAL - Optional property (shows default value)
- Uses selected template if no template specified.

### `clear-config`
**Description:** Clear configuration for a template.
**Usage:**
```
clear-config [template]
```
**Behavior:**
- Removes configuration from session and cache.
- Uses selected template if no template specified.

---

## Server Operations

### `logs`
**Description:** Get logs from a deployment.
**Usage:**
```
logs <target> [--lines N] [--backend NAME]
```
**Options:**
- `--lines N`: Number of log lines to retrieve
- `--backend NAME`: Specify backend to use
**Behavior:**
- Retrieves and displays server logs
- Shows recent activity and error information

### `stop`
**Description:** Stop deployments.
**Usage:**
```
stop [target] [--all] [--template NAME] [--force]
```
**Options:**
- `--all`: Stop all deployments
- `--template NAME`: Stop deployments for specific template
- `--force`: Force stop without confirmation
**Behavior:**
- Stops running server deployments
- Prompts for confirmation unless forced

### `status`
**Description:** Show backend health and deployment summary.
**Usage:**
```
status [--format FORMAT]
```
**Options:**
- `--format FORMAT`: Output format (table, json, etc.)
**Behavior:**
- Shows overall system status
- Displays backend health information
- Summary of active deployments

### `remove`
**Description:** Remove deployments.
**Usage:**
```
remove <target> [--all] [--template NAME] [--force]
```
**Options:**
- `--all`: Remove all deployments
- `--template NAME`: Remove deployments for specific template
- `--force`: Force removal without confirmation
**Behavior:**
- Removes server deployments and associated resources
- Prompts for confirmation unless forced

### `cleanup`
**Description:** Cleanup stopped containers and unused resources.
**Usage:**
```
cleanup
```
**Behavior:**
- Removes stopped containers
- Cleans up unused Docker resources
- Frees up system resources

---

## General Commands

### `help`
**Description:** Show help information for all commands or a specific command.
**Usage:**
```
help [command]
```
**Behavior:**
- Shows a summary of all available commands, usage, and examples.
- If a command is specified, shows detailed help for that command.

### `quit` / `exit`
**Description:** Exit the interactive CLI session.
**Usage:**
```
quit
exit
```
**Behavior:**
- Gracefully exits the CLI, saving session state if needed.

---

## Notes
- Configuration can also be set via environment variables or config files.
- For stdio templates, configuration is prompted if missing mandatory properties.
- For HTTP templates, server deployment is prompted if not running.
- All output is beautified for readability and clarity.
- Template selection with `select` allows omitting template names in subsequent commands.
- Use `help <command>` for detailed information about specific commands.

### `call <template_name> <tool_name> [json_args]`
**Description:** Call a tool from a template (via stdio or HTTP transport).
**Usage:**
```
call <template_name> <tool_name> [json_args]
```
**Arguments:**
- `json_args`: Optional JSON string of arguments for the tool (e.g. '{"param": "value"}').
**Behavior:**
- Executes the specified tool, prompting for missing configuration if needed.
- Handles both stdio and HTTP transports.
- Beautifies the tool response and error output.

---

## Configuration Management

### `config <template_name> <key>=<value> [<key2>=<value2> ...]`
**Description:** Set configuration for a template interactively.
**Usage:**
```
config <template_name> <key>=<value> [<key2>=<value2> ...]
```
**Behavior:**
- Stores configuration in session and cache.
- Masks sensitive values in output.
- Supports multiple config values at once.

---

### `show_config <template_name>`
**Description:** Show current configuration for a template.
**Usage:**
```
show_config <template_name>
```
**Behavior:**
- Displays all config values for the template, masking sensitive values.

---

### `clear_config <template_name>`
**Description:** Clear configuration for a template.
**Usage:**
```
clear_config <template_name>
```
**Behavior:**
- Removes configuration from session and cache.

---

## General Commands

### `help [command]`
**Description:** Show help information for all commands or a specific command.
**Usage:**
```
help [command]
```
**Behavior:**
- Shows a summary of all available commands, usage, and examples.
- If a command is specified, shows detailed help for that command.

---

### `quit` / `exit`
**Description:** Exit the interactive CLI session.
**Usage:**
```
quit
exit
```
**Behavior:**
- Gracefully exits the CLI, saving session state if needed.

---

## Notes
- Configuration can also be set via environment variables or config files.
- For stdio templates, configuration is prompted if missing mandatory properties.
- For HTTP templates, server deployment is prompted if not running.
- All output is beautified for readability and clarity.
