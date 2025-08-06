# MCP Interactive CLI: Command Reference

This document provides detailed information about each command available in the MCP Interactive CLI. Each command can be run interactively in the CLI session.

---

## Server Management

### `list_servers`
**Description:** List all deployed MCP servers currently running.
**Usage:**
```
list_servers
```
**Behavior:**
- Shows a table of active servers with details (ID, template, transport, status, endpoint, ports, etc).
- Only running servers are shown.
- Beautified output using Rich tables.

---

### `templates`
**Description:** List all available MCP templates.
**Usage:**
```
templates
```
**Behavior:**
- Shows a table of all templates, their transport, default port, available tools, and description.
- Useful for discovering what you can deploy and use.

---

## Tool Operations

### `tools <template_name> [--force-server] [--help]`
**Description:** List available tools for a template.
**Usage:**
```
tools <template_name> [--force-server] [--help]
```
**Options:**
- `--force-server`: Force server-side tool discovery (MCP probe only, no static fallback).
- `--help`: Show detailed help for the template and its tools.
**Behavior:**
- Lists all tools for the specified template, with details and parameters.
- If `--help` is used, shows configuration schema and usage examples.
- If `--force-server` is used, skips static tool discovery.

---

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
