# How to Use MCP Platform File Server

## Quick Start Guide

### 1. Platform-Managed Deployment (Recommended)

```bash
# No setup required! Use the web UI:
# 1. Visit https://mcp-platform.dataeverything.ai
# 2. Click "Add Server" → "File Server Template"
# 3. Configure your settings via UI
# 4. Deploy with one click
```

### 2. Self-Hosted Docker Deployment

```bash
# Clone the template
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates/file-server

# Build the enhanced container
docker build -t mcp-file-server-enhanced .

# Run with platform enhancements
docker run -d \
  --name mcp-file-server \
  -v /your/data:/data \
  -v /your/workspace:/workspace \
  -v /var/log/mcp:/logs \
  -e MCP_ALLOWED_DIRS="/data:/workspace" \
  -e MCP_READ_ONLY=false \
  -e MCP_MAX_FILE_SIZE=104857600 \
  -e MCP_EXCLUDE_PATTERNS="**/.git/**,**/node_modules/**" \
  -e LOG_LEVEL=info \
  mcp-file-server-enhanced
```

### 3. Connect to AI Assistant

```json
{
  "mcpServers": {
    "file-server": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-file-server", "node", "src/platform-wrapper.js"]
    }
  }
}
```

## Value Comparison

| Feature | Vanilla MCP Filesystem | Our Platform Enhancement |
|---------|----------------------|---------------------------|
| **Setup** | Manual CLI configuration | GUI configuration + Docker |
| **Security** | Basic path validation | File size limits, exclusions, audit logs |
| **Monitoring** | None | Health checks, metrics, structured logging |
| **Configuration** | Command-line only | JSON config + environment variables |
| **Production Ready** | Requires custom setup | Docker + health checks included |
| **Platform Integration** | None | Built-in dashboard, monitoring, scaling |

## Configuration Examples

### Development Environment
```bash
# Permissive settings for development
docker run -d \
  -e MCP_ALLOWED_DIRS="/workspace:/tmp" \
  -e MCP_READ_ONLY=false \
  -e MCP_MAX_FILE_SIZE=1073741824 \
  -e LOG_LEVEL=debug \
  mcp-file-server-enhanced
```

### Production Environment
```bash
# Restricted settings for production
docker run -d \
  -e MCP_ALLOWED_DIRS="/app/data" \
  -e MCP_READ_ONLY=true \
  -e MCP_MAX_FILE_SIZE=52428800 \
  -e MCP_EXCLUDE_PATTERNS="**/.env*,**/.git/**,**/secrets/**" \
  -e LOG_LEVEL=warn \
  mcp-file-server-enhanced
```

## Health Monitoring

```bash
# Check server health
docker exec mcp-file-server node src/health-check.js

# Get detailed health info
docker exec -e HEALTH_CHECK_VERBOSE=true mcp-file-server node src/health-check.js

# View logs
docker logs mcp-file-server

# Monitor metrics
docker exec mcp-file-server cat /logs/file-server.log | grep AUDIT
```

## What Makes This Better Than Vanilla

1. **Zero Configuration Friction**: Platform UI vs manual CLI setup
2. **Production Monitoring**: Built-in health checks and metrics
3. **Security by Default**: Configurable limits and exclusions
4. **Enterprise Logging**: Structured logs with rotation
5. **Platform Integration**: Dashboard, scaling, team management
6. **Docker Best Practices**: Multi-stage builds, non-root user, health checks

## AI Assistant Integration

Once running, your AI assistant can use enhanced file operations:

```
User: "Read the config.json file and show me the database settings"
AI: Uses read_file tool with audit logging and security validation

User: "Create a backup of all .py files in the project"  
AI: Uses search_files + read_multiple_files with size limits

User: "Update the README with the new feature list"
AI: Uses edit_file with pattern matching and diff preview
```

The AI gets all the power of the official filesystem server, plus:
- Automatic security validation
- File size protection  
- Pattern-based exclusions
- Audit trail of all operations
- Health monitoring integration
