# Troubleshooting Guide

**Common issues and solutions for MCP Template Platform deployments and development.**

## Quick Diagnostics

### Check System Status

```bash
# Verify MCP Template Platform installation
python -m mcp_template --version

# Check Docker status
docker --version
docker info

# List all deployments
python -m mcp_template list

# Check deployment health
python -m mcp_template status
```

### Basic Health Check

```bash
# Test a simple deployment
python -m mcp_template deploy demo --config debug=true

# Verify tools are discovered
python -m mcp_template tools demo

# Check logs for errors
python -m mcp_template logs demo --tail 50
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
python -m mcp_template list

# Check templates directory
ls -la templates/

# Validate template structure
python -m mcp_template create --help

# Create missing template
python -m mcp_template create my-template
```

#### 2. Container Fails to Start

**Symptoms:**
```
ERROR: Container exited with code 1
```

**Diagnostics:**
```bash
# Check container logs
python -m mcp_template logs deployment-name

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
python -m mcp_template deploy template --force-pull

# Check configuration
python -m mcp_template config template

# Use debug mode
python -m mcp_template deploy template --config debug=true
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
python -m mcp_template deploy template --port 8081

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
python -m mcp_template tools --image template:latest

# Check container logs
python -m mcp_template logs deployment --filter "tool\|mcp"

# Verify MCP server is running
docker exec -it mcp-deployment python -c "import sys; print(sys.version)"
```

**Solutions:**
```bash
# Update to latest image
python -m mcp_template deploy template --force-pull

# Check template configuration
python -m mcp_template config template

# Test with stdio transport
python -m mcp_template connect template --transport stdio
```

#### 2. Partial Tool Discovery

**Symptoms:**
```
Only 3 of 10 tools discovered
```

**Solutions:**
```bash
# Increase discovery timeout
python -m mcp_template tools --image template

# Check for tool initialization errors
python -m mcp_template logs deployment --filter "error\|exception"

# Restart deployment
python -m mcp_template deploy template --force-recreate
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
python -m mcp_template config template

# Set environment variable
export MCP_API_KEY="your-key-here"

# Use config file
echo '{"api_key": "your-key"}' > config.json
python -m mcp_template deploy template --config-file config.json

# Pass inline configuration
python -m mcp_template deploy template --config api_key=your-key
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
python -m mcp_template config template --show-schema

# Use minimal configuration
python -m mcp_template deploy template --config debug=true
```

### Performance Issues

#### 1. Slow Tool Discovery

**Symptoms:**
- Discovery takes >30 seconds
- Timeouts during tool enumeration

**Solutions:**
```bash
# Increase timeouts
python -m mcp_template tools --image template

# Use HTTP transport instead of stdio
python -m mcp_template deploy template --transport http

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
python -m mcp_template deploy template --memory 512m

# Check for memory leaks
python -m mcp_template logs deployment --filter "memory\|oom"

# Monitor resource usage
python -m mcp_template status deployment --watch
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
python -m mcp_template status deployment

# Test network connectivity
docker exec mcp-deployment curl http://localhost:8080/health

# Use stdio transport instead
python -m mcp_template connect deployment --transport stdio
```

#### 2. DNS Resolution Issues

**Symptoms:**
```
Could not resolve hostname
```

**Solutions:**
```bash
# Use IP address instead of hostname
python -m mcp_template deploy template --config host=127.0.0.1

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
python -m mcp_template create --help

# Use template wizard
python -m mcp_template create my-template
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
python -m mcp_template deploy template --config debug=true log_level=DEBUG

# Monitor debug logs
python -m mcp_template logs deployment --follow --filter "DEBUG"
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
python -m mcp_template connect deployment --debug
```

## Getting Help

### Self-Service Resources

1. **Check Documentation**
   - [CLI Reference](cli/index.md)
   - [Template Development Guide](development/template-development.md)
   - [Tool Discovery Documentation](tool-discovery.md)

2. **Search Common Issues**
   ```bash
   # Search logs for error patterns
   python -m mcp_template logs deployment | grep -i error

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
   python -m mcp_template --version
   docker --version
   python --version
   uname -a
   ```

2. **Error Details**
   ```bash
   # Full error logs
   python -m mcp_template logs deployment --since 1h

   # Configuration
   python -m mcp_template config deployment

   # Status information
   python -m mcp_template status deployment --detailed
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
python -m mcp_template status --health-only
```

### Monitoring Setup

```bash
# Set up health checks
python -m mcp_template status --watch --refresh 60 > health.log &

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
