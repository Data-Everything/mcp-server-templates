# deploy

**Deploy MCP server templates with comprehensive configuration options and deployment strategies.**

## Synopsis

```bash
mcp-template deploy TEMPLATE [OPTIONS]
```

## Description

The `deploy` command is the core functionality of MCP Templates, allowing you to deploy MCP- [`logs`](logs.md) - View deployment logs and statusserver templates with extensive configuration options. It supports multiple configuration sources, deployment backends, and provides zero-configuration deployment for quick starts.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE` | Name of the template to deploy (required) |

## Options

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `--name NAME` | Custom deployment name | Auto-generated |
| `--data-dir PATH` | Custom data directory for persistent storage | Template default |
| `--config-dir PATH` | Custom configuration directory | Template default |
| `--no-pull` | Skip pulling Docker image (use local) | Pull latest |

### Configuration Options

| Option | Description | Format |
|--------|-------------|--------|
| `--config KEY=VALUE` | Set configuration value (for config_schema properties) | `--config debug=true` |
| `--override KEY=VALUE` | Override template data (supports double underscore notation, type conversion) | `--override metadata__version=2.0.0` |
| `--config-file PATH` | Load configuration from file | JSON/YAML supported |
| `--env KEY=VALUE` | Set environment variable | `--env MCP_DEBUG=1` |
| `--show-config` | Display configuration options and exit | Boolean flag |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--backend {docker,k8s,mock}` | Deployment backend to use |
| `--transport {stdio,http}` | MCP transport protocol |
| `--port PORT` | Port for HTTP transport |

## Configuration Precedence

Configuration values are resolved in the following order (highest to lowest priority):

1. **Environment Variables** (`--env` or system)
2. **CLI Options** (`--config`, `--override`)
3. **Configuration File** (`--config-file`)
4. **Template Defaults**

## Examples

### Basic Deployment

```bash
# Deploy with defaults
mcp-template deploy demo

# Deploy with custom name
mcp-template deploy demo --name my-demo-server
```

### Configuration Examples

```bash
# Using CLI configuration (config_schema properties)
mcp-template deploy filesystem \
  --config read_only_mode=true \
  --config max_file_size=100 \
  --config log_level=debug

# Using double-underscore notation for nested config
mcp-template deploy filesystem \
  --config security__read_only=true \
  --config security__max_file_size=100 \
  --config logging__level=debug

# Using template-prefixed configuration
mcp-template deploy filesystem \
  --config filesystem__security__read_only=true \
  --config filesystem__logging__level=debug

# Using template data overrides (modifies template.json structure)
mcp-template deploy filesystem \
  --override "metadata__version=2.0.0" \
  --override "metadata__author=Your Name" \
  --override "tools__0__enabled=false" \
  --override "config__custom_setting=value"

# Advanced: Array and nested overrides with type conversion
mcp-template deploy demo \
  --override "tools__0__enabled=false" \
  --override "tools__1__timeout=30.5" \
  --override "metadata__tags=[\"custom\",\"modified\"]" \
  --override "config__database__connection__host=localhost" \
  --override "config__database__connection__port=5432" \
  --override "config__security__enabled=true"
```

### Configuration File

```bash
# Using JSON configuration file
mcp-template deploy filesystem --config-file config.json

# Using YAML configuration file
mcp-template deploy filesystem --config-file config.yml
```

**config.json example:**
```json
{
  "security": {
    "read_only": false,
    "allowed_dirs": ["/data", "/workspace"],
    "max_file_size": 100
  },
  "logging": {
    "level": "info",
    "enable_audit": true
  },
  "performance": {
    "max_concurrent_operations": 10,
    "timeout_ms": 30000
  }
}
```

### Environment Variables

```bash
# Using environment variables
mcp-template deploy filesystem \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50 \
  --env MCP_LOG_LEVEL=debug

# Mixed configuration (env variables override CLI)
mcp-template deploy filesystem \
  --config-file base-config.json \
  --config log_level=warning \
  --env MCP_READ_ONLY=true
```

### Advanced Deployment

```bash
# Deploy with custom backend and transport
mcp-template deploy demo \
  --backend docker \
  --transport http \
  --port 8080 \
  --name prod-demo

# Deploy without pulling image (development)
mcp-template deploy demo \
  --no-pull \
  --config debug=true \
  --data-dir ./local-data
```

## Configuration Discovery

Use the `--show-config` flag to see all available configuration options:

```bash
mcp-template deploy filesystem --show-config
```

This displays a comprehensive table showing:
- Property names and types
- CLI options (including double-underscore notation)
- Environment variable mappings
- Default values
- Required vs optional parameters
- Usage examples

## Template-Specific Configurations

Each template has its own configuration schema. Common patterns include:

### File Server Template

```bash
mcp-template deploy filesystem \
  --config security__allowed_dirs='["/data", "/workspace"]' \
  --config security__read_only=false \
  --config security__max_file_size=100 \
  --config logging__level=info \
  --config performance__max_concurrent=10
```

### Demo Template

```bash
mcp-template deploy demo \
  --config hello_from="Custom Server" \
  --config debug=true \
  --config port=8080
```

### PostgreSQL Server Template

```bash
mcp-template deploy postgres-server \
  --config database__host=localhost \
  --config database__port=5432 \
  --config database__name=mydb \
  --env POSTGRES_PASSWORD=secret
```

## Deployment Lifecycle

The deploy command follows this lifecycle:

1. **Template Discovery**: Locate and validate template
2. **Configuration Resolution**: Merge configuration sources
3. **Backend Initialization**: Prepare deployment backend
4. **Image Management**: Pull or validate Docker images
5. **Container Creation**: Create and configure containers
6. **Health Checks**: Verify deployment success
7. **Registration**: Register deployment for management

## Monitoring Deployment

After deployment, monitor your server:

```bash
# Check deployment status
mcp-template status demo

# View logs
mcp-template logs demo --follow

# Access container shell
mcp-template shell demo
```

## Error Handling

Common deployment errors and solutions:

### Template Not Found
```
❌ Template 'mytemplate' not found
Available templates: demo, filesystem, postgres-server
```
**Solution**: Use `mcp-template list` to see available templates.

### Configuration Error
```
❌ Invalid configuration: security.max_file_size must be a number
   Given: "unlimited"
   Expected: integer
```
**Solution**: Check configuration types using `--show-config`.

### Port Already in Use
```
❌ Port 8080 is already in use
```
**Solution**: Use `--port` to specify a different port or stop conflicting services.

### Docker Not Available
```
❌ Docker daemon not available
   Please ensure Docker is installed and running
```
**Solution**: Start Docker daemon or use `--backend mock` for testing.

## See Also

- [config](config.md) - View template configuration options
- [logs](logs.md) - Monitor deployment logs
- [stop](stop.md) - Stop deployments
- [logs](logs.md) - View deployment logs and status
