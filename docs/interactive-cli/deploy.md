# `deploy` Command

Deploy a template as an MCP server.

## Functionality
- Deploys the specified template as a running server
- Prompts for missing configuration if needed
- Shows deployment status and connection details
- Supports various transport modes and backends

## Options & Arguments
- `[template]`: Template to deploy (uses selected template if omitted)
- `--transport`: Transport mode (stdio, http)
- `--port`: Port for HTTP transport
- `--backend`: Backend to use (docker, kubernetes, etc.)
- `--config KEY=VALUE`: Set configuration values
- `--env KEY=VALUE`: Set environment variables
- `--no-pull`: Don't pull Docker images

## Configuration
- Template configuration may be required
- Missing configuration will be prompted interactively

## Example
```
deploy demo
deploy github --transport http --port 8080
deploy --config github_token=ghp_xxx github
```

### Sample Output
```
🚀 Deploying template: demo
✅ Server deployed successfully
📍 Endpoint: http://localhost:7071
🆔 Server ID: abc123def456
```

## When and How to Run
- Use to start a new MCP server instance
- Run after configuring a template
- Use when you need an HTTP endpoint for tool calls

## Related Commands
- `servers` - List deployed servers
- `configure` - Set template configuration
- `stop` - Stop deployed servers
- `logs` - View deployment logs
