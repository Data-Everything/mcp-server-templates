# `logs` Command

Get logs from a deployment.

## Functionality
- Retrieves and displays server logs
- Shows recent activity and error information
- Supports filtering by number of lines
- Works with different backends

## Options & Arguments
- `<target>`: Target deployment ID or name
- `--lines N`: Number of log lines to retrieve (default: recent)
- `--backend NAME`: Specify backend to use

## Configuration
- No configuration required

## Example
```
logs abc123def456
logs demo-server --lines 50
logs my-deployment --backend docker
```

### Sample Output
```
📋 Logs for deployment: abc123def456
2025-08-26 10:30:15 [INFO] Server starting on port 7071
2025-08-26 10:30:16 [INFO] MCP server ready to accept connections
2025-08-26 10:30:20 [INFO] Tool call: say_hello
2025-08-26 10:30:20 [DEBUG] Processing request with args: {"name": "Alice"}
```

## When and How to Run
- Use to debug server issues
- Run when investigating deployment problems
- Check recent activity or error messages

## Related Commands
- `servers` - List available deployments
- `status` - Check deployment health
- `deploy` - Deploy new servers
