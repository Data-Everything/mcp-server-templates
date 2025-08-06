# Troubleshooting Guide

**Common issues and solutions for MCP Template Platform deployments and development.**

## Quick Diagnostics

### Check System Status

```bash
# Verify MCP Template Platform installation
mcp-template --version

# Check Docker status
docker --version
docker info

# List all deployments
mcp-template list

# Check deployment health
mcp-template status
```

### Basic Health Check

```bash
# Test a simple deployment
mcp-template deploy demo --config debug=true

# Verify tools are discovered
mcp-template tools demo

# Check logs for errors
mcp-template logs demo --tail 50
```

## Common Issues

### Installation Problems

#### 1. Python Package Installation Fails

**Symptoms:**
```
ERROR: Could not build wheels for mcp-templates
```

**Solutions:**
```bash
# Update pip and build tools
pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -v mcp-templates

# Use conda if pip fails
conda install -c conda-forge mcp-templates
```

#### 2. Docker Connection Issues

**Symptoms:**
```
ERROR: Cannot connect to Docker daemon
```

**Solutions:**
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker works
docker run hello-world
```

### Deployment Issues

#### 1. Template Not Found

**Symptoms:**
```
ERROR: Template 'my-template' not found
```

**Solutions:**
```bash
# List available templates
mcp-template list

# Check templates directory
ls -la templates/

# Validate template structure
mcp-template create --help

# Create missing template
mcp-template create my-template
```

#### 2. Container Fails to Start

**Symptoms:**
```
ERROR: Container exited with code 1
```

**Diagnostics:**
```bash
# Check container logs
mcp-template logs deployment-name

# Inspect container
docker logs mcp-deployment-name

# Check image exists
docker images | grep mcp

# Test image directly
docker run -it mcp/template:latest /bin/bash
```

**Solutions:**
```bash
# Force image pull
mcp-template deploy template --force-pull

# Check configuration
mcp-template config template

# Use debug mode
mcp-template deploy template --config debug=true
```

#### 3. Port Conflicts

**Symptoms:**
```
ERROR: Port 8080 already in use
```

**Solutions:**
```bash
# Find what's using the port
sudo netstat -tulpn | grep 8080

# Use different port
mcp-template deploy template --port 8081

# Stop conflicting service
sudo systemctl stop service-on-port-8080
```

### Tool Discovery Issues

#### 1. No Tools Discovered

**Symptoms:**
```
No tools found in deployment
```

**Diagnostics:**
```bash
# Test MCP protocol directly
mcp-template tools --image template:latest

# Check container logs
mcp-template logs deployment --filter "tool\|mcp"

# Verify MCP server is running
docker exec -it mcp-deployment python -c "import sys; print(sys.version)"
```

**Solutions:**
```bash
# Update to latest image
mcp-template deploy template --force-pull

# Check template configuration
mcp-template config template

# Test with stdio transport
mcp-template connect template --transport stdio
```

#### 2. Partial Tool Discovery

**Symptoms:**
```
Only 3 of 10 tools discovered
```

**Solutions:**
```bash
# Increase discovery timeout
mcp-template tools --image template

# Check for tool initialization errors
mcp-template logs deployment --filter "error\|exception"

# Restart deployment
mcp-template deploy template --force-recreate
```

### Configuration Issues

#### 1. Environment Variables Not Set

**Symptoms:**
```
Missing required configuration: API_KEY
```

**Solutions:**
```bash
# Check current configuration
mcp-template config template

# Set environment variable
export MCP_API_KEY="your-key-here"

# Use config file
echo '{"api_key": "your-key"}' > config.json
mcp-template deploy template --config-file config.json

# Pass inline configuration
mcp-template deploy template --config api_key=your-key
```

#### 2. Configuration Validation Fails

**Symptoms:**
```
ERROR: Invalid configuration schema
```

**Solutions:**
```bash
# Validate configuration file
python -m json.tool config.json

# Check template schema
mcp-template config template --show-schema

# Use minimal configuration
mcp-template deploy template --config debug=true
```

### Performance Issues

#### 1. Slow Tool Discovery

**Symptoms:**
- Discovery takes >30 seconds
- Timeouts during tool enumeration

**Solutions:**
```bash
# Increase timeouts
mcp-template tools --image template

# Use HTTP transport instead of stdio
mcp-template deploy template --transport http

# Check container resources
docker stats mcp-deployment
```

#### 2. High Memory Usage

**Symptoms:**
- Container using excessive memory
- Out of memory errors

**Solutions:**
```bash
# Set memory limits
mcp-template deploy template --memory 512m

# Check for memory leaks
mcp-template logs deployment --filter "memory\|oom"

# Monitor resource usage
mcp-template status deployment --watch
```

### Network Issues

#### 1. Connection Refused

**Symptoms:**
```
Connection refused to localhost:8080
```

**Solutions:**
```bash
# Check if port is mapped
docker port mcp-deployment

# Verify container is running
mcp-template status deployment

# Test network connectivity
docker exec mcp-deployment curl http://localhost:8080/health

# Use stdio transport instead
mcp-template connect deployment --transport stdio
```

#### 2. DNS Resolution Issues

**Symptoms:**
```
Could not resolve hostname
```

**Solutions:**
```bash
# Use IP address instead of hostname
mcp-template deploy template --config host=127.0.0.1

# Check Docker DNS
docker exec mcp-deployment nslookup google.com

# Restart Docker daemon
sudo systemctl restart docker
```

## Development Issues

### Template Development

#### 1. Template Validation Fails

**Symptoms:**
```
ERROR: Invalid template.json format
```

**Solutions:**
```bash
# Validate JSON syntax
python -m json.tool templates/my-template/template.json

# Check required fields
mcp-template create --help

# Use template wizard
mcp-template create my-template
```

#### 2. Docker Build Fails

**Symptoms:**
```
ERROR: Build failed for template
```

**Solutions:**
```bash
# Build manually to see errors
cd templates/my-template
docker build -t my-template .

# Check Dockerfile syntax
docker build --no-cache -t my-template .

# Use smaller base image
# Change FROM python:3.11 to FROM python:3.11-slim
```

### Testing Issues

#### 1. Tests Not Running

**Symptoms:**
```
No tests found for template
```

**Solutions:**
```bash
# Check test directory exists
ls -la templates/my-template/tests/

# Create test structure
mkdir -p templates/my-template/tests
touch templates/my-template/tests/test_server.py

# Run tests manually
cd templates/my-template
python -m pytest tests/
```

## Advanced Diagnostics

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export MCP_LOG_LEVEL=DEBUG
export MCP_DEBUG=true

# Deploy with debug configuration
mcp-template deploy template --config debug=true log_level=DEBUG

# Monitor debug logs
mcp-template logs deployment --follow --filter "DEBUG"
```

### Container Inspection

Deep dive into container issues:

```bash
# Get container information
docker inspect mcp-deployment

# Access container shell
docker exec -it mcp-deployment /bin/bash

# Check process tree
docker exec mcp-deployment ps aux

# Monitor container stats
docker stats mcp-deployment --no-stream
```

### MCP Protocol Debugging

Test MCP protocol directly:

```bash
# Test stdio communication
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
docker exec -i mcp-deployment python server.py

# Test HTTP endpoint
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Monitor MCP messages
mcp-template connect deployment --debug
```

## Getting Help

### Self-Service Resources

1. **Check Documentation**
   - [CLI Reference](../cli/index.md)
   - [Template Creation Guide](creating-templates.md)
   - [Tool Discovery Documentation](../tool-discovery.md)

2. **Search Common Issues**
   ```bash
   # Search logs for error patterns
   mcp-template logs deployment | grep -i error

   # Check GitHub issues
   # Visit: https://github.com/data-everything/mcp-server-templates/issues
   ```

3. **Community Resources**
   - GitHub Discussions
   - Discord Community
   - Stack Overflow (tag: mcp-templates)

### Professional Support

For production environments:

- **Enterprise Support**: Contact support@dataeverything.ai
- **Custom Templates**: Professional template development services
- **Training**: Team training and workshops available

### Reporting Issues

When reporting issues, include:

1. **System Information**
   ```bash
   mcp-template --version
   docker --version
   python --version
   uname -a
   ```

2. **Error Details**
   ```bash
   # Full error logs
   mcp-template logs deployment --since 1h

   # Configuration
   mcp-template config deployment

   # Status information
   mcp-template status deployment --detailed
   ```

3. **Steps to Reproduce**
   - Exact commands used
   - Template configuration
   - Expected vs actual behavior

## Prevention Best Practices

### Regular Maintenance

```bash
# Update MCP Template Platform
pip install --upgrade mcp-templates

# Clean up old containers
docker system prune -f

# Check deployment health
mcp-template status --health-only
```

### Monitoring Setup

```bash
# Set up health checks
mcp-template status --watch --refresh 60 > health.log &

# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  $(docker ps --filter "name=mcp-" --format "{{.Names}}")
```

### Configuration Management

```bash
# Backup configurations
mkdir -p ~/.mcp/backups
cp -r ~/.mcp/config ~/.mcp/backups/config-$(date +%Y%m%d)

# Version control templates
cd templates/
git init
git add .
git commit -m "Initial template configuration"
```

By following this troubleshooting guide, most common issues can be resolved quickly. For complex problems, don't hesitate to seek community or professional support.
