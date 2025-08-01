# Configuration

Learn how to configure MCP templates for your needs.

## Template Configuration

Each template includes a `template.json` file that defines its configuration schema:

```json
{
  "id": "demo",
  "name": "Demo Hello MCP Server",
  "description": "A simple demonstration MCP server",
  "version": "1.0.0",
  "author": "Data Everything",
  "requires": ["python>=3.10"],
  "ports": [8080],
  "environment": {
    "DEMO_MESSAGE": "Hello from MCP!"
  }
}
```

## Runtime Configuration

Override template defaults at deployment time:

```bash
# Set environment variables
mcp-template deploy demo --env DEMO_MESSAGE="Custom message"

# Change port
mcp-template deploy demo --port 9090

# Set multiple options
mcp-template deploy demo --port 8080 --env DEBUG=true --env LOG_LEVEL=info
```

## Configuration Files

Templates can include configuration files in the `config/` directory:

```
templates/demo/
├── config/
│   ├── server.json
│   └── logging.yaml
├── src/
└── template.json
```

## Environment Variables

Common environment variables supported by templates:

- `PORT`: Server port (default varies by template)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (debug, info, warn, error)
- `HOST`: Bind host (default: 0.0.0.0)
