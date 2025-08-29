# `servers` Command

List all deployed MCP servers currently running.

## Functionality
- Shows a table of active servers with details (ID, template, transport, status, endpoint, ports, etc).
- Only running servers are shown.
- Beautified output using Rich tables.

## Options & Arguments
- `--template NAME`: Filter by specific template
- `--all-backends`: Show servers from all backends

## Configuration
- No configuration required.

## Example
```
servers
servers --template github
servers --all-backends
```

### Sample Output
```
🔍 Discovering deployed MCP servers...
                                                                 Deployed MCP Servers (3 active)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID         ┃ Template             ┃ Transport    ┃ Status     ┃ Endpoint                       ┃ Ports                ┃ Since                     ┃ Tools      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ bc0e605ab… │ mcp-demo-0806-14315… │ http         │ running    │ http://localhost:42651         │ 42651->7071          │ 54 minutes ago            │ 3          │
│ 38063d7c4… │ mcp-demo-0806-14292… │ stdio        │ running    │ N/A                            │ 54411->7071          │ 57 minutes ago            │ 3          │
└────────────┴──────────────────────┴──────────────┴────────────┴────────────────────────────────┴──────────────────────┴───────────────────────────┴────────────┘
```

## When and How to Run
- Use when you want to see which MCP servers are currently deployed and running.
- Run at any time during an interactive CLI session.
- Use before deploying to check if a server is already running.

## Related Commands
- `deploy` - Deploy a new server
- `stop` - Stop running servers
- `logs` - View server logs
- `remove` - Remove servers
