# list

**List available templates and active deployments with comprehensive filtering and formatting options.**

## Synopsis

```bash
mcpt list [OPTIONS]
```

## Description

The `list` command provides an overview of available MCP server templates and active deployments. It displays template information, deployment status, and resource usage in a clear, formatted interface.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format {table,json,yaml}` | Output format | `table` |
| `--filter TEXT` | Filter by name, category, or tag | No filter |
| `--backend {docker,k8s,mock}` | Backend to query | `docker` |
| `--all` | Show all templates (including inactive) | Active only |
| `--deployed` | Show only currently deployed (active) servers | All templates |

## Output Information

### Template Information
- **Name**: Template identifier
- **Description**: Brief template description
- **Version**: Template version
- **Category**: Template classification
- **Status**: Deployment status (Active, Stopped, Error)
- **Container**: Container name (if deployed)
- **Ports**: Exposed ports
- **Created**: Deployment timestamp

## Examples

### Basic Usage

```bash

# List all available templates
mcpt list

# List only currently deployed (active) servers
mcpt list --deployed

# Example output:
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Template             ┃ Description                           ┃ Status                                ┃ Container   ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ demo                 │ Demo MCP server with greeting tools   │ ✅ Active (2 minutes ago)           │ mcp-demo-123│
│ filesystem          │ Secure filesystem operations server   │ ✅ Active (1 hour ago)              │ mcp-file-456│
│ postgres-server      │ PostgreSQL database integration       │ ⏸️  Stopped                         │ -           │
│ api-server           │ REST API integration template         │ ❌ Error (Connection failed)        │ mcp-api-789 │
└──────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┴─────────────┘

📊 Summary: 4 templates (2 active, 1 stopped, 1 error)
💡 Use 'mcpt deploy <template>' to deploy
    Use 'mcpt logs <template>' to view logs
```

### Filtering Options

```bash
# Filter by template name
mcpt list --filter file

# Filter by category
mcpt list --filter database

# Filter by status
mcpt list --filter active
```

### Output Formats

```bash
# JSON format for programmatic use
mcpt list --format json

# Example JSON output:
{
  "templates": [
    {
      "name": "demo",
      "description": "Demo MCP server with greeting tools",
      "version": "1.0.0",
      "category": "example",
      "status": "active",
      "container_name": "mcp-demo-123456",
      "ports": {"8080": 8080},
      "created": "2024-01-15T10:30:00Z",
      "last_activity": "2024-01-15T10:32:00Z"
    }
  ],
  "summary": {
    "total": 4,
    "active": 2,
    "stopped": 1,
    "error": 1
  }
}

# YAML format
mcpt list --format yaml
```

### Backend-Specific Listing

```bash
# List Docker deployments (default)
mcpt list --backend docker

# List Kubernetes deployments
mcpt list --backend k8s

# List mock deployments (testing)
mcpt list --backend mock
```

## Template Categories

Templates are organized by category for easier discovery:

### Example Templates (`example`)
- **demo**: Basic greeting and echo functionality
- **hello-world**: Minimal example server

### File Operations (`file`)
- **filesystem**: Comprehensive file system operations
- **document-processor**: Document analysis and processing

### Database Integration (`database`)
- **postgres-server**: PostgreSQL database operations
- **mongodb-server**: MongoDB document operations
- **redis-server**: Redis cache and pub/sub

### API Integration (`api`)
- **rest-api**: General REST API client
- **github-api**: GitHub API integration
- **slack-api**: Slack workspace integration

### Development Tools (`development`)
- **code-analysis**: Static code analysis tools
- **test-runner**: Automated testing framework
- **deployment-tools**: CI/CD integration

## Status Indicators

### Active Status (`✅ Active`)
- Container is running and healthy
- Server is responding to requests
- All health checks passing

### Stopped Status (`⏸️ Stopped`)
- Container has been manually stopped
- No active processes
- Can be restarted with `deploy` command

### Error Status (`❌ Error`)
- Container failed to start or crashed
- Configuration or runtime errors
- Requires troubleshooting

### Starting Status (`🔄 Starting`)
- Container is currently starting up
- Health checks in progress
- Normal during deployment

## Detailed Information

For each template, the list command shows:

### Resource Usage
- **CPU Usage**: Current CPU utilization
- **Memory Usage**: RAM consumption
- **Network I/O**: Network traffic statistics
- **Disk Usage**: Storage utilization

### Configuration Summary
- **Image**: Docker image and tag
- **Transport**: MCP transport protocol (stdio/http)
- **Ports**: Exposed port mappings
- **Volumes**: Mounted directories

### Recent Activity
- **Last Activity**: Most recent request timestamp
- **Request Count**: Total requests served
- **Error Count**: Recent error count
- **Uptime**: Time since last restart

## Advanced Usage

### Monitoring Dashboard

```bash
# Watch list in real-time (requires watch command)
watch -n 5 'mcpt list'


# Show all information including stopped containers
mcpt list --all

# Show only currently deployed (active) servers
mcpt list --deployed

# Compact format for scripts
mcpt list --format json | jq -r '.templates[].name'
```

### Health Monitoring

```bash
# Show only error status deployments
mcpt list --filter error

# Show recently active deployments
mcpt list --filter active

# Export deployment list for monitoring
mcpt list --format json > deployments.json
```

## Troubleshooting

### No Templates Listed
```bash
❌ No templates found
```
**Solutions**:
- Verify templates directory exists
- Check template.json files are valid
- Ensure you have read permissions

### Backend Connection Error
```bash
❌ Cannot connect to Docker daemon
```
**Solutions**:
- Start Docker daemon
- Check Docker permissions
- Verify DOCKER_HOST environment variable

### Permission Denied
```bash
❌ Permission denied: Cannot access deployment information
```
**Solutions**:
- Run with appropriate permissions
- Check Docker group membership
- Verify backend configuration

## Integration Examples

### Monitoring Scripts

```bash
#!/bin/bash
# Simple monitoring script
ERRORS=$(mcpt list --format json | jq '.summary.error')
if [ "$ERRORS" -gt 0 ]; then
    echo "⚠️  $ERRORS deployments have errors"
    mcpt list --filter error
fi
```

### Health Check

```python
import json
import subprocess

def check_deployment_health():
    result = subprocess.run([
        'python', '-m', 'mcp_template', 'list', '--format', 'json'
    ], capture_output=True, text=True)

    data = json.loads(result.stdout)
    summary = data['summary']

    if summary['error'] > 0:
        print(f"⚠️  {summary['error']} deployments have errors")
        return False

    print(f"✅ All {summary['active']} deployments healthy")
    return True
```

## Configuration

### Default Settings
- **Backend**: Docker (can be overridden with `MCP_TEMPLATE_DEFAULT_BACKEND`)
- **Format**: Table (can be overridden with `MCP_LIST_DEFAULT_FORMAT`)
- **Refresh Interval**: 30 seconds for cached data

### Environment Variables
- `MCP_TEMPLATE_DEFAULT_BACKEND`: Default backend to query
- `MCP_LIST_DEFAULT_FORMAT`: Default output format
- `MCP_LIST_SHOW_STOPPED`: Include stopped deployments by default

## See Also

- [deploy](deploy.md) - Deploy templates
- [logs](logs.md) - Get detailed deployment logs
- [logs](logs.md) - View deployment logs
- [stop](stop.md) - Stop active deployments
