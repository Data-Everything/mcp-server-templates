# Demo Hello MCP Server Template

A simple demonstration MCP server that provides greeting tools using the Model Context Protocol. This template serves as an example for learning MCP concepts and testing integrations.

## Features

- **Personalized Greetings**: Generate custom greeting messages
- **Server Information**: Get details about the running server
- **Configurable Source**: Customize the greeting source name
- **FastMCP Framework**: Built using the modern FastMCP framework

## Configuration

The template supports the following configuration options:

### hello_from (string)
- **Description**: Name or message to include in greetings
- **Default**: `"MCP Platform"`
- **Environment Variable**: `MCP_HELLO_FROM`

### log_level (string)
- **Description**: Logging level for the server
- **Options**: `debug`, `info`, `warn`, `error`
- **Default**: `"info"`
- **Environment Variable**: `MCP_LOG_LEVEL`

## Available Tools

### say_hello
Generate a personalized greeting message.
- **Parameters**:
  - `name` (optional): Name of the person to greet
- **Returns**: A personalized greeting message

### get_server_info
Get information about the demo server.
- **Parameters**: None
- **Returns**: Dictionary with server details including version, capabilities, and status

## Usage Examples

### Basic Deployment
```bash
mcp-deploy demo
```

### Custom Greeting Source
```bash
mcp-deploy demo --config hello_from="My Custom Bot"
```

### With Environment Variables
```bash
mcp-deploy demo --env MCP_HELLO_FROM="AI Assistant" --env MCP_LOG_LEVEL="debug"
```

### Using Config File
Create a `config.yaml`:
```yaml
hello_from: "My Personal Assistant"
log_level: "debug"
```

Then deploy:
```bash
mcp-deploy demo --config-file config.yaml
```

## MCP Client Configuration

After deployment, the template generates an MCP client configuration. Example usage in Claude Desktop:

```json
{
  "servers": {
    "demo-server": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-demo-container", "python", "-m", "src.server"]
    }
  }
}
```

## Development

### Local Testing
```bash
cd templates/demo
pip install -r requirements.txt
export MCP_HELLO_FROM="Development Server"
python src/server.py
```

### Docker Build
```bash
docker build -t mcp-demo-hello .
docker run -e MCP_HELLO_FROM="Docker Demo" mcp-demo-hello
```

This template demonstrates the core patterns used in MCP server development and serves as a foundation for building more complex servers.
