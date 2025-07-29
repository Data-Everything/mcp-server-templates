# Demo MCP Server

A simple demonstration MCP server that provides greeting tools using FastMCP and HTTP transport by default.

## Overview

This demo server showcases the MCP Platform architecture with:
- **FastMCP integration** for tool decorators and HTTP transport
- **HTTP-first approach** with stdio fallback
- **Docker deployment** with networking support
- **Modular code structure** following best practices
- **Comprehensive configuration** with environment variable mapping

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with defaults (HTTP on port 7071)
python server.py

# Run with custom configuration
python server.py --hello-from "Custom Server" --log-level debug

# Run with stdio transport (for testing)
python server.py --transport stdio
```

### Docker Deployment

```bash
# Build the image
docker build -t dataeverything/mcp-demo:latest .

# Run with defaults
docker run -p 7071:7071 dataeverything/mcp-demo:latest

# Run with custom configuration
docker run -p 7071:7071 \
  -e MCP_HELLO_FROM="Docker Server" \
  -e MCP_LOG_LEVEL=debug \
  dataeverything/mcp-demo:latest

# Join MCP Platform network
docker network create mcp-platform
docker run --network mcp-platform --name demo \
  -p 7071:7071 dataeverything/mcp-demo:latest
```

### Using MCP Template CLI

```bash
# Deploy using the CLI
python -m mcp_template deploy demo

# Deploy with custom configuration
python -m mcp_template deploy demo --config hello_from="CLI Server"

# Show configuration options
python -m mcp_template config demo

# List available tools
python -m mcp_template tools demo

# Get integration examples
python -m mcp_template connect demo --llm claude
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HELLO_FROM` | Name or message to include in greetings | "MCP Platform" |
| `MCP_LOG_LEVEL` | Logging level (debug, info, warning, error) | "info" |

### Configuration Options

```bash
# Direct configuration
--config hello_from="Custom Server"
--config log_level=debug

# Environment variables
--env MCP_HELLO_FROM="Custom Server"
--env MCP_LOG_LEVEL=debug

# Double-underscore notation (for nested configs)
--config demo__hello_from="Custom Server"
--config demo__log_level=debug
```

### Configuration Files

**JSON Configuration (`demo-config.json`):**
```json
{
  "hello_from": "Custom Server",
  "log_level": "debug"
}
```

**YAML Configuration (`demo-config.yml`):**
```yaml
hello_from: "Custom Server"
log_level: debug
```

## Available Tools

### 1. say_hello

Generate a personalized greeting message.

**Parameters:**
- `name` (optional): Name of the person to greet

**Examples:**
```python
# Without name
client.call("say_hello")
# Returns: "Hello! Greetings from MCP Platform!"

# With name
client.call("say_hello", name="Alice")
# Returns: "Hello Alice! Greetings from MCP Platform!"
```

### 2. get_server_info

Get comprehensive information about the demo server.

**Parameters:** None

**Returns:** JSON string with server metadata, configuration, and available tools.

### 3. echo_message

Echo back a message with server identification.

**Parameters:**
- `message` (required): Message to echo back

**Example:**
```python
client.call("echo_message", message="Hello World")
# Returns: "[MCP Platform] Echo: Hello World"
```

## Client Integration

### FastMCP Client

```python
from fastmcp.client import FastMCPClient

# Connect to the server
client = FastMCPClient(endpoint="http://localhost:7071")

# Call tools
greeting = client.call("say_hello", name="Alice")
server_info = client.call("get_server_info")
echo_result = client.call("echo_message", message="Test")

print(greeting)  # Hello Alice! Greetings from MCP Platform!
```

### Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "demo": {
      "command": "docker",
      "args": ["exec", "-i", "demo", "python", "server.py", "--transport", "stdio"]
    }
  }
}
```

### VS Code Integration

Add to your VS Code MCP configuration:

```json
{
  "mcp.servers": {
    "demo": {
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/templates/demo"
    }
  }
}
```

### cURL Testing

```bash
# Test say_hello
curl -X POST http://localhost:7071/call \
  -H "Content-Type: application/json" \
  -d '{"method": "say_hello", "params": {"name": "Alice"}}'

# Test get_server_info
curl -X POST http://localhost:7071/call \
  -H "Content-Type: application/json" \
  -d '{"method": "get_server_info", "params": {}}'

# Test echo_message
curl -X POST http://localhost:7071/call \
  -H "Content-Type: application/json" \
  -d '{"method": "echo_message", "params": {"message": "Hello World"}}'
```

## Development

### Project Structure

```
templates/demo/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── server.py            # Main server implementation
├── tools.py             # Tool definitions
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
├── template.json        # Template metadata
├── README.md            # This file
└── tests/               # Test suite
    ├── test_server.py   # Server tests
    ├── test_tools.py    # Tool tests
    └── test_config.py   # Configuration tests
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Style

This project follows:
- **PEP 8** style guidelines
- **Type hints** for all functions
- **Docstrings** for all public functions
- **Logging** instead of print statements

## Architecture

The demo server follows the MCP Platform architecture:

1. **BaseMCPServer**: Base class providing common functionality
2. **DemoServerConfig**: Configuration management with environment mapping
3. **Tools Module**: FastMCP tool definitions with decorators
4. **Server Module**: Main server implementation and CLI

This modular design ensures consistency across templates and makes the code:
- **Testable**: Each module can be tested independently
- **Maintainable**: Clear separation of concerns
- **Extensible**: Easy to add new tools and configuration options
- **Reusable**: Base classes can be used by other templates

## Troubleshooting

### Common Issues

1. **Import Error: FastMCP not found**
   ```bash
   pip install fastmcp>=2.10.0
   ```

2. **Port already in use**
   ```bash
   # Use a different port
   python server.py --port 7072
   ```

3. **Docker network issues**
   ```bash
   # Create the network first
   docker network create mcp-platform
   ```

### Debugging

Enable debug logging to see detailed information:

```bash
# Local development
python server.py --log-level debug

# Docker
docker run -e MCP_LOG_LEVEL=debug dataeverything/mcp-demo:latest

# CLI deployment
python -m mcp_template deploy demo --config log_level=debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
