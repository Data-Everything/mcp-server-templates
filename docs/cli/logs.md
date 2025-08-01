# logs

**View and monitor deployment logs with filtering, streaming, and analysis capabilities.**

## Synopsis

```bash
mcp-template logs TEMPLATE [OPTIONS]
```

## Description

The `logs` command provides comprehensive log viewing and monitoring for deployed MCP server templates. It supports real-time log streaming, historical log analysis, filtering by severity levels, and formatted output for debugging and monitoring purposes.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE` | Name of the deployed template to view logs for |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--follow, -f` | Follow log output in real-time | Static view |
| `--tail N` | Show last N lines | All lines |
| `--since DURATION` | Show logs since duration (e.g., 1h, 30m, 2d) | All logs |
| `--until TIMESTAMP` | Show logs until timestamp | Current time |
| `--level {debug,info,warn,error}` | Filter by log level | All levels |
| `--grep PATTERN` | Filter logs matching pattern | No filter |
| `--format {auto,json,plain}` | Output format | `auto` |
| `--no-color` | Disable colored output | Colored output |

## Examples

### Basic Usage

```bash
# View all logs for demo template
mcp-template logs demo

# Example output:
2024-01-15 10:30:45 [INFO] MCP Server starting on stdio transport
2024-01-15 10:30:45 [INFO] Registered tool: say_hello
2024-01-15 10:30:45 [INFO] Registered tool: get_server_info
2024-01-15 10:30:45 [INFO] Registered tool: echo_message
2024-01-15 10:30:45 [INFO] Server ready to accept connections
2024-01-15 10:32:12 [INFO] Client connected via stdio
2024-01-15 10:32:15 [INFO] Tool called: say_hello(name="World")
2024-01-15 10:32:15 [INFO] Tool result: Hello, World!
```

### Real-time Monitoring

```bash
# Follow logs in real-time
mcp-template logs demo --follow

# Follow with tail (last 50 lines + new ones)
mcp-template logs demo --follow --tail 50

# Monitor specific log level
mcp-template logs demo --follow --level error
```

### Time-based Filtering

```bash
# Show logs from last hour
mcp-template logs demo --since 1h

# Show logs from last 30 minutes
mcp-template logs demo --since 30m

# Show logs from specific time range
mcp-template logs demo --since 2024-01-15T10:00:00 --until 2024-01-15T11:00:00

# Show recent activity
mcp-template logs demo --since 5m --follow
```

### Content Filtering

```bash
# Filter by log level
mcp-template logs demo --level error
mcp-template logs demo --level warn

# Search for specific patterns
mcp-template logs demo --grep "tool called"
mcp-template logs demo --grep "error\|exception" --level error

# Combine filters
mcp-template logs demo --since 1h --level info --grep "client"
```

### Output Formats

```bash
# JSON format for parsing
mcp-template logs demo --format json --tail 10

# Example JSON output:
[
  {
    "timestamp": "2024-01-15T10:30:45Z",
    "level": "INFO",
    "message": "MCP Server starting on stdio transport",
    "container": "mcp-demo-123456",
    "source": "server.py:45"
  },
  {
    "timestamp": "2024-01-15T10:32:15Z",
    "level": "INFO",
    "message": "Tool called: say_hello(name=\"World\")",
    "container": "mcp-demo-123456",
    "source": "tools.py:23",
    "metadata": {
      "tool_name": "say_hello",
      "parameters": {"name": "World"}
    }
  }
]

# Plain text format (no formatting)
mcp-template logs demo --format plain --no-color
```

## Log Levels and Filtering

### Available Log Levels

| Level | Description | Color |
|-------|-------------|-------|
| `DEBUG` | Detailed debugging information | Gray |
| `INFO` | General information messages | Blue |
| `WARN` | Warning messages | Yellow |
| `ERROR` | Error messages | Red |
| `FATAL` | Critical errors | Magenta |

### Level Filtering Examples

```bash
# Show only errors and warnings
mcp-template logs demo --level warn

# Debug-level logging (very verbose)
mcp-template logs demo --level debug --tail 100

# Production monitoring (errors only)
mcp-template logs demo --level error --follow
```

## Advanced Filtering

### Pattern Matching

```bash
# Case-insensitive search
mcp-template logs demo --grep "(?i)error"

# Multiple patterns (OR logic)
mcp-template logs demo --grep "error\|exception\|fail"

# Tool-specific logs
mcp-template logs demo --grep "Tool called: say_hello"

# Client connection logs
mcp-template logs demo --grep "client (connected|disconnected)"
```

### Complex Queries

```bash
# Errors in last hour
mcp-template logs demo --since 1h --level error

# Recent tool calls with debug info
mcp-template logs demo --since 30m --grep "Tool" --level debug

# Monitor specific functionality
mcp-template logs demo --follow --grep "file_server\|directory"
```

## Performance and Troubleshooting

### Debugging Deployment Issues

```bash
# Check startup logs
mcp-template logs demo --since 10m --level info

# Look for errors during initialization
mcp-template logs demo --grep "starting\|initializ" --level error

# Monitor resource usage logs
mcp-template logs demo --grep "memory\|cpu\|disk" --follow
```

### Common Log Patterns

#### Successful Startup
```
[INFO] MCP Server starting on stdio transport
[INFO] Configuration loaded: {...}
[INFO] Registered tool: tool_name
[INFO] Server ready to accept connections
```

#### Client Connection
```
[INFO] Client connected via stdio
[DEBUG] Received initialize request
[DEBUG] Sent initialize response
[INFO] Client session established
```

#### Tool Execution
```
[INFO] Tool called: tool_name(param="value")
[DEBUG] Tool execution started
[DEBUG] Tool execution completed: 0.045s
[INFO] Tool result: {...}
```

#### Error Patterns
```
[ERROR] Tool execution failed: tool_name
[ERROR] Invalid parameters for tool: {...}
[WARN] Client disconnected unexpectedly
[ERROR] Configuration error: missing required parameter
```

### Performance Analysis

```bash
# Monitor tool performance
mcp-template logs demo --grep "execution.*[0-9]+\.[0-9]+s" --follow

# Track client connections
mcp-template logs demo --grep "client.*connected\|disconnected" --since 1h

# Monitor error rates
mcp-template logs demo --level error --since 1h | wc -l
```

## Integration with Monitoring

### Log Analysis Scripts

```bash
#!/bin/bash
# Simple error monitoring script
ERROR_COUNT=$(mcp-template logs demo --since 1h --level error --format plain | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "⚠️  High error rate: $ERROR_COUNT errors in last hour"
    mcp-template logs demo --since 1h --level error --tail 5
fi
```

### Export for Analysis

```bash
# Export logs to file
mcp-template logs demo --since 1d --format json > demo_logs_$(date +%Y%m%d).json

# Import to log analysis tools
mcp-template logs demo --format json --since 1h | jq '.[] | select(.level == "ERROR")'

# Create CSV for spreadsheet analysis
mcp-template logs demo --since 1d --format json | \
  jq -r '.[] | [.timestamp, .level, .message] | @csv' > logs.csv
```

### Real-time Monitoring Dashboard

```python
#!/usr/bin/env python3
import subprocess
import json
import time
from collections import defaultdict

def monitor_logs():
    """Simple real-time log monitoring."""
    cmd = ["python", "-m", "mcp_template", "logs", "demo", "--follow", "--format", "json"]

    stats = defaultdict(int)

    with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True) as proc:
        for line in proc.stdout:
            try:
                log_entry = json.loads(line)
                stats[log_entry['level']] += 1

                # Print stats every 100 lines
                if sum(stats.values()) % 100 == 0:
                    print(f"Stats: {dict(stats)}")

                # Alert on errors
                if log_entry['level'] == 'ERROR':
                    print(f"🚨 ERROR: {log_entry['message']}")

            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    monitor_logs()
```

## Container Log Management

### Log Rotation and Storage

```bash
# Check log size
docker logs mcp-demo-123456 | wc -l

# Export container logs directly
docker logs mcp-demo-123456 --since 1h > container_logs.txt

# Configure log rotation (in docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Multi-container Deployments

```bash
# Monitor multiple templates simultaneously
mcp-template logs demo --follow &
mcp-template logs file-server --follow &
wait
```

## Troubleshooting Log Issues

### No Logs Available
```bash
❌ No logs available for template 'demo'
```
**Solutions**:
- Verify template is deployed: `mcp-template status demo`
- Check if container is running: `mcp-template list`
- Container may have just started: try `--since 1m`

### Permission Errors
```bash
❌ Permission denied accessing container logs
```
**Solutions**:
- Check Docker permissions
- Run with appropriate privileges
- Verify container accessibility

### Large Log Files
```bash
⚠️  Log file is very large (>100MB), consider using --tail or --since
```
**Solutions**:
- Use `--tail 1000` to limit output
- Use `--since 1h` for recent logs only
- Consider log rotation configuration

## See Also

- [status](status.md) - Check deployment health and status
- [shell](shell.md) - Access deployment containers for debugging
- [deploy](deploy.md) - Deploy templates with logging configuration
- [Monitoring Guide](../user-guide/monitoring.md) - Comprehensive monitoring setup
