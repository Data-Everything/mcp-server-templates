# `status` Command

Show backend health and deployment summary.

## Functionality
- Shows overall system status
- Displays backend health information
- Summary of active deployments
- Resource usage information

## Options & Arguments
- `--format FORMAT`: Output format (table, json, yaml)

## Configuration
- No configuration required

## Example
```
status
status --format json
```

### Sample Output
```
📊 System Status

Backend Health:
  Docker: ✅ Running
  Kubernetes: ⚠️  Not available

Deployments Summary:
  Active: 3
  Stopped: 1
  Failed: 0

Resource Usage:
  CPU: 15%
  Memory: 2.1GB
  Disk: 45GB
```

## When and How to Run
- Use to check overall system health
- Run before deploying new servers
- Monitor resource usage and capacity

## Related Commands
- `servers` - List individual deployments
- `cleanup` - Free up resources
- `logs` - Check for specific issues
