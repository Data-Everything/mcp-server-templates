# CLI Commands

Complete reference for the `python -m mcp_template` command-line interface.

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
python -m mcp_template list [OPTIONS]
```

**Options:**
- `--format TEXT`: Output format (table, json, yaml)
- `--filter TEXT`: Filter templates by name or tag

**Examples:**
```bash
python -m mcp_template list
python -m mcp_template list --format json
python -m mcp_template list --filter database
```

### `deploy`

Deploy a template.

```bash
python -m mcp_template deploy TEMPLATE [OPTIONS]
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
python -m mcp_template deploy demo
python -m mcp_template deploy demo --port 8080
python -m mcp_template deploy demo --env DEBUG=true --env LOG_LEVEL=debug
```

### `stop`

Stop a running deployment.

```bash
python -m mcp_template stop NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name

**Options:**
- `--force`: Force stop without graceful shutdown

### `remove`

Remove a deployment.

```bash
python -m mcp_template remove NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name

**Options:**
- `--force`: Remove without confirmation

### `logs`

View deployment logs.

```bash
python -m mcp_template logs NAME [OPTIONS]
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
python -m mcp_template status [NAME] [OPTIONS]
```

**Arguments:**
- `NAME`: Deployment name (optional, shows all if omitted)

### `create`

Create a new template.

```bash
python -m mcp_template create NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Template name

**Options:**
- `--author TEXT`: Template author
- `--description TEXT`: Template description
- `--port INTEGER`: Default port
