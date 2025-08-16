# MCP Gateway User Guide

The MCP Gateway provides a unified HTTP endpoint for accessing multiple MCP servers with built-in load balancing and connection management.

## Quick Start

### 1. Create Gateway Configuration

Create a registry configuration file that defines your MCP servers:

```bash
# Generate example configuration
mcpt gateway example --output my-gateway.json
```

### 2. Start the Gateway

```bash
# Start with default settings
mcpt gateway start --registry my-gateway.json

# Or specify host and port
mcpt gateway start --registry my-gateway.json --host 0.0.0.0 --port 8080
```

### 3. Access Your Servers

Once running, access your MCP servers through the gateway:

```bash
# List available servers
curl http://localhost:8000/servers

# List tools from a specific server
curl http://localhost:8000/demo/tools

# Call a tool
curl -X POST http://localhost:8000/demo/tools/say_hello \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Server Configuration

The gateway supports three types of MCP servers:

### HTTP Servers

For servers that expose HTTP endpoints:

```json
{
  "my-http-server": {
    "type": "http",
    "instances": [
      {"endpoint": "http://server1:8080"},
      {"endpoint": "http://server2:8080"}
    ],
    "load_balancing": "round_robin",
    "health_check": "/health"
  }
}
```

Features:
- **Load balancing**: Round-robin or random distribution
- **Health checking**: Automatic unhealthy instance removal
- **Multiple instances**: Scale horizontally with multiple backends

### stdio Servers

For servers that use stdio transport:

```json
{
  "my-stdio-server": {
    "type": "stdio",
    "command": ["python", "-m", "my_mcp_server"],
    "pool_size": 3,
    "working_dir": "/app",
    "env_vars": {
      "LOG_LEVEL": "info"
    }
  }
}
```

Features:
- **Connection pooling**: Maintain multiple server processes
- **Automatic scaling**: Create connections as needed
- **Environment control**: Set working directory and environment variables

### Template Servers

For servers from the MCP template system:

```json
{
  "my-template-server": {
    "type": "template",
    "template_name": "demo",
    "instances": 2,
    "config": {
      "hello_from": "Gateway"
    }
  }
}
```

Features:
- **Dynamic deployment**: Automatically deploy from templates
- **Configuration override**: Customize template settings
- **Multiple instances**: Deploy multiple copies

## Gateway Configuration

Configure the gateway itself:

```json
{
  "gateway": {
    "host": "0.0.0.0",
    "port": 8000,
    "reload_registry": true,
    "health_check_interval": 30
  }
}
```

Options:
- **host**: Interface to bind to
- **port**: Port to listen on
- **reload_registry**: Automatically reload config changes
- **health_check_interval**: Health check frequency (seconds)

## URL Routing

The gateway uses a simple URL pattern:

```
/<server-id>/<path>
```

### Common Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Gateway status and server list |
| `GET /health` | Gateway health check |
| `GET /servers` | List all available servers |
| `GET /servers/{server-id}` | Get server information |
| `GET /{server-id}/tools` | List server tools |
| `POST /{server-id}/tools/{tool-name}` | Call a specific tool |
| `ALL /{server-id}/{path}` | Proxy request to server |

### Examples

```bash
# Gateway status
curl http://localhost:8000/

# List servers
curl http://localhost:8000/servers

# Get server info
curl http://localhost:8000/servers/demo

# List tools
curl http://localhost:8000/demo/tools

# Call a tool
curl -X POST http://localhost:8000/demo/tools/say_hello \
  -H "Content-Type: application/json" \
  -d '{"name": "Gateway User"}'

# Proxy arbitrary requests (for HTTP servers)
curl http://localhost:8000/my-http-server/api/v1/status
```

## Load Balancing

### HTTP Server Load Balancing

For HTTP servers with multiple instances:

```json
{
  "web-service": {
    "type": "http",
    "instances": [
      {"endpoint": "http://web1:8080"},
      {"endpoint": "http://web2:8080"},
      {"endpoint": "http://web3:8080"}
    ],
    "load_balancing": "round_robin"
  }
}
```

Strategies:
- **round_robin**: Distribute requests evenly across instances
- **random**: Random selection from healthy instances

### stdio Server Connection Pooling

For stdio servers:

```json
{
  "worker-service": {
    "type": "stdio",
    "command": ["python", "-m", "worker"],
    "pool_size": 5
  }
}
```

The gateway maintains a pool of `pool_size` connections, creating new ones as needed and cleaning up unhealthy connections automatically.

## Health Checking

### Automatic Health Management

The gateway automatically manages server health:

- **HTTP servers**: Mark instances unhealthy on connection errors
- **stdio servers**: Remove connections that fail repeatedly
- **Recovery**: Automatically retry unhealthy instances

### Manual Health Checks

For HTTP servers, you can specify a health check endpoint:

```json
{
  "my-server": {
    "type": "http",
    "instances": [{"endpoint": "http://server:8080"}],
    "health_check": "/health"
  }
}
```

## Configuration Management

### Validation

Validate your configuration before starting:

```bash
mcpt gateway validate my-gateway.json
```

### Dynamic Reloading

If `reload_registry` is enabled, the gateway will automatically reload configuration changes:

```json
{
  "gateway": {
    "reload_registry": true
  }
}
```

### Environment Variables

You can use environment variables in your configuration:

```bash
export MCP_HOST=0.0.0.0
export MCP_PORT=8080

mcpt gateway start --host $MCP_HOST --port $MCP_PORT
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["mcpt", "gateway", "start", "--registry", "production-gateway.json"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-gateway
  template:
    metadata:
      labels:
        app: mcp-gateway
    spec:
      containers:
      - name: gateway
        image: your-org/mcp-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_REGISTRY
          value: "/config/gateway.json"
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: gateway-config
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-gateway
spec:
  selector:
    app: mcp-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Monitoring

Monitor gateway health and performance:

```bash
# Gateway health
curl http://localhost:8000/health

# Server statistics
curl http://localhost:8000/servers/my-server

# Logs
mcpt gateway start --log-level DEBUG
```

## Troubleshooting

### Common Issues

1. **Server not found**: Check server ID in registry
2. **Connection errors**: Verify server endpoints and health
3. **Tool call failures**: Check server logs and tool arguments
4. **Load balancing issues**: Verify instance health and configuration

### Debugging

Enable debug logging:

```bash
mcpt gateway start --log-level DEBUG --registry my-gateway.json
```

Check server health:

```bash
curl http://localhost:8000/servers/my-server
```

Validate configuration:

```bash
mcpt gateway validate my-gateway.json
```

### Logs

The gateway provides structured logging:

```
2024-01-01 12:00:00 - mcp_template.gateway.server - INFO - Starting MCP Gateway on 0.0.0.0:8000
2024-01-01 12:00:01 - mcp_template.gateway.registry - INFO - Loaded registry with 3 servers
2024-01-01 12:00:02 - mcp_template.gateway.load_balancer - INFO - Created HTTP load balancer for server1
```

## Advanced Configuration

### Custom Load Balancing

```python
# Custom load balancer (future extension)
from mcp_template.gateway.load_balancer import LoadBalancer

class CustomLoadBalancer(LoadBalancer):
    def get_next_instance(self):
        # Custom logic here
        pass
```

### Middleware Integration

```python
# Custom middleware (future extension)
from mcp_template.gateway.server import MCPGateway

gateway = MCPGateway()
gateway.app.middleware("http")(my_custom_middleware)
```

### Authentication

```python
# Custom authentication (future extension)
from fastapi import Depends
from mcp_template.gateway.server import MCPGateway

def authenticate(token: str = Header(...)):
    # Verify token
    pass

gateway = MCPGateway()
gateway.app.dependency_overrides[authenticate] = authenticate
```

## API Reference

See the [API documentation](api-reference.md) for detailed endpoint specifications and response formats.