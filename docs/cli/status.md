# status

**Check deployment health, status, and detailed information for MCP server instances.**

## Synopsis

```bash
python -m mcp_template status [DEPLOYMENT_ID] [OPTIONS]
```

## Description

The `status` command provides comprehensive health monitoring and status information for MCP server deployments. It shows deployment state, container health, resource usage, configuration details, and recent activity logs.

## Arguments

| Argument | Description |
|----------|-------------|
| `DEPLOYMENT_ID` | ID of the deployment to check (optional, shows all if not provided) |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--watch` | Watch status continuously with auto-refresh | One-time check |
| `--refresh SECONDS` | Auto-refresh interval when watching | `5` |
| `--detailed` | Show detailed configuration and environment | Summary only |
| `--health-only` | Show only health status information | Full status |
| `--format FORMAT` | Output format: `table`, `json`, `yaml` | `table` |

## Usage Examples

### Check All Deployments

```bash
# Show status of all deployments
python -m mcp_template status

# Example output:
╭─────────────────── MCP Deployment Status ────────────────────╮
│                                                               │
│  🚀 Active Deployments: 3                                    │
│  ✅ Healthy: 2    ⚠️  Warning: 1    ❌ Failed: 0             │
│                                                               │
╰───────────────────────────────────────────────────────────────╯

┌──────────────────┬─────────────┬────────────┬──────────────────┬─────────────┐
│ Deployment ID    │ Template    │ Status     │ Health           │ Uptime      │
├──────────────────┼─────────────┼────────────┼──────────────────┼─────────────┤
│ demo-server      │ demo        │ ✅ Running │ ✅ Healthy       │ 2h 15m      │
│ file-server-prod │ file-server │ ✅ Running │ ✅ Healthy       │ 1d 5h       │
│ api-connector    │ custom-api  │ ✅ Running │ ⚠️  Warning      │ 45m         │
└──────────────────┴─────────────┴────────────┴──────────────────┴─────────────┘

💡 Use --detailed for more information or specify deployment ID for specific status
```

### Check Specific Deployment

```bash
# Check specific deployment status
python -m mcp_template status demo-server

# Example output:
╭────────────────── demo-server Status ─────────────────────╮
│                                                            │
│  📋 Deployment: demo-server                                │
│  🏷️  Template: demo v1.0.0                                │
│  📦 Image: dataeverything/mcp-demo:latest                  │
│  🔄 Status: ✅ Running                                     │
│  💚 Health: ✅ Healthy                                     │
│  ⏰ Uptime: 2h 15m 34s                                     │
│  🎯 Started: 2025-01-27 14:32:15 UTC                      │
│                                                            │
╰────────────────────────────────────────────────────────────╯

🐳 Container Information:
├─ Container ID: abc123def456
├─ Host Port: None (stdio transport)
├─ Memory Usage: 45.2 MB / 512 MB (8.8%)
├─ CPU Usage: 0.2%
└─ Restart Count: 0

🔧 Configuration:
├─ Transport: stdio
├─ Data Volume: ~/mcp-data → /data
├─ Log Volume: ~/.mcp/logs → /logs
└─ Environment: 3 variables set

🛠️  Tools Available: 3
├─ greet: Send a greeting message
├─ calculate: Perform basic calculations
└─ get_time: Get current time

📊 Recent Activity:
├─ Last Health Check: 2025-01-27 16:47:45 UTC (✅ Passed)
├─ Last Tool Call: 2025-01-27 16:45:12 UTC (greet)
├─ Log Entries (1h): 12 entries
└─ Errors (24h): 0 errors

🔗 Quick Actions:
├─ View logs: python -m mcp_template logs demo-server
├─ Connect: python -m mcp_template connect demo-server
└─ Redeploy: python -m mcp_template deploy demo --no-pull
```

### Detailed Status Information

```bash
# Show detailed status with full configuration
python -m mcp_template status demo-server --detailed

# Example output includes:
╭─────────────── Detailed Configuration ────────────────╮
│                                                        │
│  Environment Variables:                                │
│  ├─ MCP_GREETING="Hello from MCP!"                     │
│  ├─ MCP_DEBUG="false"                                  │
│  └─ MCP_LOG_LEVEL="INFO"                               │
│                                                        │
│  Volume Mounts:                                        │
│  ├─ ~/mcp-data → /data (rw)                            │
│  └─ ~/.mcp/logs → /logs (rw)                           │
│                                                        │
│  Network Configuration:                                │
│  ├─ Transport: stdio                                   │
│  ├─ Protocol: MCP 2025-06-18                          │
│  └─ Exposed Ports: None                                │
│                                                        │
│  Resource Limits:                                      │
│  ├─ Memory: 512 MB                                     │
│  ├─ CPU: No limit                                      │
│  └─ Disk: Host filesystem                              │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

### Health-Only Status

```bash
# Show only health status
python -m mcp_template status --health-only

# Example output:
🏥 Health Status Summary:

✅ demo-server: Healthy
   ├─ Container: Running (2h 15m uptime)
   ├─ MCP Protocol: Responding
   ├─ Tools: 3/3 available
   └─ Last Check: 30s ago

✅ file-server-prod: Healthy
   ├─ Container: Running (1d 5h uptime)
   ├─ MCP Protocol: Responding
   ├─ Tools: 11/11 available
   └─ Last Check: 45s ago

⚠️  api-connector: Warning
   ├─ Container: Running (45m uptime)
   ├─ MCP Protocol: Responding (slow)
   ├─ Tools: 5/6 available (1 failed)
   └─ Last Check: 2m ago
   └─ Issue: Tool 'fetch_data' returning errors
```

### Continuous Monitoring

```bash
# Watch status with auto-refresh every 5 seconds
python -m mcp_template status demo-server --watch

# Custom refresh interval
python -m mcp_template status --watch --refresh 10

# Example output (refreshes automatically):
╭─────────────── Live Status Monitor ───────────────╮
│                                                    │
│  🔄 Auto-refresh: Every 5 seconds                 │
│  ⏰ Last Update: 2025-01-27 16:47:52 UTC          │
│  📊 Monitoring: demo-server                       │
│                                                    │
╰────────────────────────────────────────────────────╯

Current Status: ✅ Running
Health Check: ✅ Healthy
Memory Usage: 45.3 MB / 512 MB (8.8%)
CPU Usage: 0.1%
Tool Calls (1m): 2
Errors (1m): 0

🔄 Refreshing in 3... 2... 1...

# Press Ctrl+C to exit watch mode
```

## Output Formats

### JSON Format

```bash
# Get status as JSON for scripting
python -m mcp_template status demo-server --format json

# Example output:
{
  "deployment_id": "demo-server",
  "template": {
    "name": "demo",
    "version": "1.0.0"
  },
  "status": {
    "state": "running",
    "health": "healthy",
    "uptime_seconds": 8134,
    "started_at": "2025-01-27T14:32:15Z"
  },
  "container": {
    "id": "abc123def456",
    "image": "dataeverything/mcp-demo:latest",
    "memory_usage": 47185920,
    "memory_limit": 536870912,
    "cpu_percent": 0.2,
    "restart_count": 0
  },
  "configuration": {
    "transport": "stdio",
    "environment": {
      "MCP_GREETING": "Hello from MCP!",
      "MCP_DEBUG": "false",
      "MCP_LOG_LEVEL": "INFO"
    },
    "volumes": {
      "~/mcp-data": "/data",
      "~/.mcp/logs": "/logs"
    }
  },
  "tools": {
    "available": 3,
    "total": 3,
    "list": ["greet", "calculate", "get_time"]
  },
  "health_checks": {
    "last_check": "2025-01-27T16:47:45Z",
    "status": "passed",
    "response_time_ms": 45
  },
  "activity": {
    "last_tool_call": "2025-01-27T16:45:12Z",
    "log_entries_1h": 12,
    "errors_24h": 0
  }
}
```

### YAML Format

```bash
# Get status as YAML
python -m mcp_template status demo-server --format yaml

# Example output:
deployment_id: demo-server
template:
  name: demo
  version: 1.0.0
status:
  state: running
  health: healthy
  uptime_seconds: 8134
  started_at: '2025-01-27T14:32:15Z'
container:
  id: abc123def456
  image: 'dataeverything/mcp-demo:latest'
  memory_usage: 47185920
  memory_limit: 536870912
  cpu_percent: 0.2
  restart_count: 0
configuration:
  transport: stdio
  environment:
    MCP_GREETING: 'Hello from MCP!'
    MCP_DEBUG: 'false'
    MCP_LOG_LEVEL: 'INFO'
  volumes:
    '~/mcp-data': '/data'
    '~/.mcp/logs': '/logs'
tools:
  available: 3
  total: 3
  list: [greet, calculate, get_time]
```

## Status Indicators

### Deployment States

| State | Icon | Description |
|-------|------|-------------|
| `running` | ✅ | Container is running and responsive |
| `starting` | 🔄 | Container is starting up |
| `stopped` | ⏹️ | Container is stopped |
| `failed` | ❌ | Container failed to start or crashed |
| `restarting` | 🔄 | Container is restarting |

### Health Status

| Health | Icon | Description |
|--------|------|-------------|
| `healthy` | ✅ | All systems operational |
| `warning` | ⚠️ | Minor issues detected |
| `critical` | 🔴 | Major issues affecting functionality |
| `unknown` | ❓ | Health status cannot be determined |

### Resource Usage Indicators

| Usage | Color | Description |
|-------|-------|-------------|
| 0-50% | 🟢 Green | Normal usage |
| 51-80% | 🟡 Yellow | High usage |
| 81-95% | 🟠 Orange | Very high usage |
| 95%+ | 🔴 Red | Critical usage |

## Troubleshooting Status Issues

### Container Not Running

```bash
# Check why container stopped
python -m mcp_template status failed-deployment --detailed

# Common solutions:
python -m mcp_template logs failed-deployment --tail 50
python -m mcp_template deploy template-name --force-recreate
```

### Health Check Failures

```bash
# Check health check details
python -m mcp_template status deployment --health-only

# Test MCP protocol directly
python -m mcp_template connect deployment --test-connection

# Review health check logs
python -m mcp_template logs deployment --filter "health"
```

### High Resource Usage

```bash
# Monitor resource usage over time
python -m mcp_template status deployment --watch --refresh 2

# Check for resource leaks
python -m mcp_template logs deployment --filter "memory\|cpu"

# Consider resource limits
python -m mcp_template deploy template --memory 1024m --cpu 0.5
```

### Missing Tools

```bash
# Verify tool availability
python -m mcp_template tools deployment

# Check tool discovery issues
python -m mcp_template discover-tools --deployment deployment

# Review server startup logs
python -m mcp_template logs deployment --since 1h --filter "tool\|error"
```

## Integration Examples

### Monitoring Scripts

```bash
#!/bin/bash
# Basic health monitoring script

check_deployment_health() {
    local deployment_id=$1
    local status=$(python -m mcp_template status "$deployment_id" --format json | jq -r '.status.health')

    if [ "$status" != "healthy" ]; then
        echo "ALERT: $deployment_id is $status"
        # Send notification
        python -m mcp_template logs "$deployment_id" --tail 10
    fi
}

# Check all critical deployments
for deployment in file-server-prod api-connector; do
    check_deployment_health "$deployment"
done
```

### Automated Recovery

```bash
#!/bin/bash
# Auto-recovery script for failed deployments

recover_failed_deployment() {
    local deployment_id=$1
    local status=$(python -m mcp_template status "$deployment_id" --format json | jq -r '.status.state')

    if [ "$status" = "failed" ]; then
        echo "Recovering failed deployment: $deployment_id"

        # Get template name
        local template=$(python -m mcp_template status "$deployment_id" --format json | jq -r '.template.name')

        # Redeploy
        python -m mcp_template deploy "$template" --force-recreate

        # Verify recovery
        sleep 30
        local new_status=$(python -m mcp_template status "$deployment_id" --format json | jq -r '.status.state')
        echo "Recovery result: $new_status"
    fi
}
```

### Prometheus Integration

```python
#!/usr/bin/env python3
"""Export MCP deployment metrics to Prometheus."""

import json
import subprocess
from prometheus_client import start_http_server, Gauge, Info
import time

# Prometheus metrics
deployment_status = Gauge('mcp_deployment_status', 'Deployment status', ['deployment_id', 'template'])
deployment_uptime = Gauge('mcp_deployment_uptime_seconds', 'Deployment uptime', ['deployment_id'])
deployment_memory = Gauge('mcp_deployment_memory_bytes', 'Memory usage', ['deployment_id'])
deployment_cpu = Gauge('mcp_deployment_cpu_percent', 'CPU usage', ['deployment_id'])
deployment_tools = Gauge('mcp_deployment_tools_available', 'Available tools', ['deployment_id'])

def collect_metrics():
    """Collect metrics from MCP deployments."""
    try:
        # Get all deployment status
        result = subprocess.run(
            ['python', '-m', 'mcp_template', 'status', '--format', 'json'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            deployments = data.get('deployments', [])

            for deployment in deployments:
                deployment_id = deployment['deployment_id']
                template_name = deployment['template']['name']

                # Status (1=healthy, 0.5=warning, 0=failed)
                status_value = {
                    'healthy': 1.0,
                    'warning': 0.5,
                    'critical': 0.0,
                    'unknown': -1.0
                }.get(deployment['status']['health'], -1.0)

                deployment_status.labels(
                    deployment_id=deployment_id,
                    template=template_name
                ).set(status_value)

                # Uptime
                deployment_uptime.labels(deployment_id=deployment_id).set(
                    deployment['status']['uptime_seconds']
                )

                # Resource usage
                container = deployment.get('container', {})
                deployment_memory.labels(deployment_id=deployment_id).set(
                    container.get('memory_usage', 0)
                )
                deployment_cpu.labels(deployment_id=deployment_id).set(
                    container.get('cpu_percent', 0)
                )

                # Tools
                tools = deployment.get('tools', {})
                deployment_tools.labels(deployment_id=deployment_id).set(
                    tools.get('available', 0)
                )

    except Exception as e:
        print(f"Error collecting metrics: {e}")

if __name__ == '__main__':
    # Start Prometheus HTTP server
    start_http_server(8000)
    print("Prometheus metrics server started on port 8000")

    # Collect metrics every 30 seconds
    while True:
        collect_metrics()
        time.sleep(30)
```

## Performance Considerations

### Status Check Performance

```bash
# Fast health-only checks
python -m mcp_template status --health-only

# Avoid detailed checks for monitoring scripts
python -m mcp_template status deployment --format json | jq '.status.health'

# Batch status checks are more efficient than individual
python -m mcp_template status  # All deployments
```

### Resource Monitoring

```bash
# Monitor resource trends
python -m mcp_template status --watch --refresh 60 > status.log &

# Analyze resource patterns
grep "Memory Usage" status.log | tail -100
```

## See Also

- [deploy](deploy.md) - Deploy MCP server templates
- [logs](logs.md) - View deployment logs and monitoring
- [list](list.md) - List templates and deployments
- [connect](connect.md) - Connect to deployments for testing
- [Monitoring Guide](../user-guide/monitoring.md) - Production monitoring strategies
