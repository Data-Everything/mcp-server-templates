# Quick Start

Get started with MCP Templates in minutes.

## 1. List Available Templates

```bash
mcp-template list
```

## 2. Deploy a Template

```bash
# Deploy the demo template
mcp-template deploy demo

# Deploy with custom configuration
mcp-template deploy file-server --port 8080
```

## 3. Test Your Deployment

```bash
# Check if the server is running
curl http://localhost:8080/health

# View server logs
mcp-template logs demo
```

## 4. Clean Up

```bash
# Stop the server
mcp-template stop demo

# Remove the deployment
mcp-template remove demo
```

## Next Steps

- Check out the [Templates Overview](../server-templates/index.md) to see what's available
- Learn about [Configuration](configuration.md) options
- Read the [Deployment Guide](../guides/deployment.md) for advanced usage
