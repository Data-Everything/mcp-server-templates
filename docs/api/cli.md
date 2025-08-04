# CLI Commands

Complete reference for the `mcp-template` command-line interface.

## Global Options

```
--version          Show version information
--help            Show help message
--verbose, -v     Enable verbose output
--quiet, -q       Suppress output
```

## Commands

### `list`

List available templates.

```bash
mcp-template list [OPTIONS]
```

**Options:**
- `--format TEXT`: Output format (table, json, yaml)
- `--filter TEXT`: Filter templates by name or tag

**Examples:**
```bash
mcp-template list
mcp-template list --format json
mcp-template list --filter database
```

### `deploy`

Deploy a template (HTTP transport only).

```bash
mcp-template deploy TEMPLATE [OPTIONS]
```

**Arguments:**
- `TEMPLATE`: Template name to deploy

**Options:**
- `--port INTEGER`: Port to bind (default: template default)
- `--env TEXT`: Environment variable (KEY=value)
- `--local`: Deploy locally without Docker
- `--docker`: Force Docker deployment
- `--name TEXT`: Custom deployment name

**Examples:**
```bash
mcp-template deploy demo
mcp-template deploy demo --port 8080
mcp-template deploy demo --env DEBUG=true --env LOG_LEVEL=debug
```

**Note:** Only HTTP transport templates can be deployed. Stdio transport templates will show an error with guidance to use `run-tool` instead.

### `run-tool`

Run a specific tool from a stdio MCP template.

```bash
mcp-template run-tool TEMPLATE TOOL_NAME [OPTIONS]
```

**Arguments:**
- `TEMPLATE`: Template name
- `TOOL_NAME`: Name of the tool to execute

**Options:**
- `--args TEXT`: JSON arguments to pass to the tool
- `--config TEXT`: Configuration values (KEY=VALUE)
- `--env TEXT`: Environment variables (KEY=VALUE)

**Examples:**
```bash
# Basic tool execution
mcp-template run-tool github search_repositories --args '{"query": "mcp"}'

# With authentication
mcp-template run-tool github create_issue \
  --args '{"owner": "user", "repo": "test", "title": "Bug"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=token

# With configuration
mcp-template run-tool filesystem read_file \
  --args '{"path": "/data/file.txt"}' \
  --config allowed_directories='["/data"]' \
  --config read_only=true
```

### `tools`

List available tools for a template or discover tools from a Docker image.

```bash
mcp-template tools [TEMPLATE] [OPTIONS]
```

**Arguments:**
- `TEMPLATE`: Template name (optional if using --image)

**Options:**
- `--image TEXT`: Docker image name to discover tools from
- `--no-cache`: Ignore cached results
- `--refresh`: Force refresh cached results
- `--config TEXT`: Configuration values for dynamic discovery (KEY=VALUE)

**Examples:**
```bash
# List tools for a template
mcp-template tools github
mcp-template tools filesystem

# Discover tools from Docker image
mcp-template tools --image mcp/github:latest

# List tools with configuration
mcp-template tools github --config github_token=your_token

# Force refresh tool discovery
mcp-template tools github --refresh
```

### `stop`

Stop a running deployment.

```bash
mcp-template stop NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name

**Options:**
- `--force`: Force stop without graceful shutdown

### `remove`

Remove a deployment.

```bash
mcp-template remove NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name

**Options:**
- `--force`: Remove without confirmation

### `logs`

View deployment logs.

```bash
mcp-template logs NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name

**Options:**
- `--follow, -f`: Follow log output
- `--tail INTEGER`: Number of lines to show
- `--since TEXT`: Show logs since timestamp

### `status`

Check deployment status.

```bash
mcp-template status [NAME] [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name (optional, shows all if omitted)

### `create`

Create a new template.

```bash
mcp-template create NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Template name

**Options:**
- `--author TEXT`: Template author
- `--description TEXT`: Template description
- `--port INTEGER`: Default port
