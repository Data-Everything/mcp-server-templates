# CLI Reference

This document provides comprehensive reference for the MCP Template CLI tool.

## Installation

```bash
pip install mcp-template
```

## Global Options

- `--help` - Show help message and exit
- `--version` - Show version information

## Commands

### create

Create a new MCP server template.

```bash
mcp-template create [TEMPLATE_ID] [OPTIONS]
```

**Arguments:**
- `TEMPLATE_ID` - Unique identifier for the template (optional, will prompt if not provided)

**Options:**
- `--config-file PATH` - Path to template configuration file
- `--non-interactive` - Run in non-interactive mode (requires config file)

**Examples:**
```bash
# Interactive template creation
mcp-template create

# Create with specific template ID
mcp-template create my-new-template

# Create from configuration file
mcp-template create --config-file template-config.json

# Non-interactive mode
mcp-template create my-template --config-file config.json --non-interactive
```

### deploy

Deploy a template using the specified deployment backend.

```bash
mcp-template deploy TEMPLATE_ID [OPTIONS]
```

**Arguments:**
- `TEMPLATE_ID` - Template to deploy

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to use (default: docker)
- `--config-file PATH` - Path to configuration file
- `--name NAME` - Custom deployment name
- `--no-pull` - Skip pulling container image (useful for local development)

**Examples:**
```bash
# Deploy with Docker backend
mcp-template deploy demo

# Deploy with custom name and skip image pull
mcp-template deploy demo --name my-demo --no-pull

# Deploy with configuration file
mcp-template deploy demo --config-file config.json

# Deploy using Kubernetes backend
mcp-template deploy demo --backend k8s
```

### list

List all active deployments.

```bash
mcp-template list [OPTIONS]
```

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to query (default: docker)

**Examples:**
```bash
# List Docker deployments
mcp-template list

# List Kubernetes deployments
mcp-template list --backend k8s
```

### delete

Delete a deployment.

```bash
mcp-template delete DEPLOYMENT_NAME [OPTIONS]
```

**Arguments:**
- `DEPLOYMENT_NAME` - Name of the deployment to delete

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to use (default: docker)

**Examples:**
```bash
# Delete Docker deployment
mcp-template delete demo-deployment

# Delete Kubernetes deployment
mcp-template delete demo-deployment --backend k8s
```

### status

Get status information for a deployment.

```bash
mcp-template status DEPLOYMENT_NAME [OPTIONS]
```

**Arguments:**
- `DEPLOYMENT_NAME` - Name of the deployment

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to use (default: docker)

**Examples:**
```bash
# Get Docker deployment status
mcp-template status demo-deployment

# Get Kubernetes deployment status
mcp-template status demo-deployment --backend k8s
```

## Configuration File Format

The configuration file is a JSON file that can be used with the `create` and `deploy` commands:

### Template Configuration (for create command)

```json
{
  "id": "my-template",
  "name": "My Template",
  "description": "A custom MCP server template",
  "version": "1.0.0",
  "author": "Your Name",
  "category": "General",
  "tags": ["custom", "example"],
  "docker_image": "dataeverything/mcp-my-template",
  "docker_tag": "latest",
  "ports": {
    "8080": 8080
  },
  "command": ["python", "server.py"],
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"],
    "port": 8080
  },
  "capabilities": [
    {
      "name": "my_tool",
      "description": "Description of the tool"
    }
  ],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API key for authentication"
      }
    }
  }
}
```

### Deployment Configuration (for deploy command)

```json
{
  "template_id": "demo",
  "deployment_name": "my-demo-deployment",
  "config": {
    "api_key": "your-api-key",
    "debug": true
  },
  "backend": "docker",
  "pull_image": false
}
```

## Environment Variables

- `MCP_TEMPLATE_DEFAULT_BACKEND` - Default deployment backend (docker, k8s, mock)
- `MCP_TEMPLATE_CONFIG_PATH` - Default configuration file path
- `DOCKER_HOST` - Docker daemon host (for Docker backend)

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid argument or configuration
- `3` - Template not found
- `4` - Deployment error
- `5` - Backend not available
