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

### tools

List available tools for a template or discover tools from a Docker image.

```bash
mcp-template tools TEMPLATE_NAME [OPTIONS]
mcp-template tools --image IMAGE_NAME [SERVER_ARGS...]
```

**Arguments:**
- `TEMPLATE_NAME` - Template to discover tools for
- `IMAGE_NAME` - Docker image name to discover tools from
- `SERVER_ARGS` - Arguments to pass to the MCP server (when using --image)

**Options:**
- `--image IMAGE_NAME` - Discover tools from Docker image instead of template
- `--no-cache` - Ignore cached tool discovery results
- `--refresh` - Force refresh of cached results
- `--config KEY=VALUE` - Configuration values for dynamic discovery (can be used multiple times)

**Examples:**
```bash
# List tools for a template
mcp-template tools demo

# List tools with cache refresh
mcp-template tools demo --refresh

# List tools for dynamic template with config
mcp-template tools github --config github_token=your_token

# Discover tools from Docker image
mcp-template tools --image mcp/filesystem /tmp

# Discover tools with multiple config values
mcp-template tools github --config github_token=token --config log_level=DEBUG
```

**Note:** For templates with `tool_discovery: "dynamic"`, if standard discovery methods fail, the command will automatically attempt to spin up the Docker image specified in the template configuration to discover tools dynamically.

### config

Show configuration options for a template.

```bash
mcp-template config TEMPLATE_NAME
```

**Arguments:**
- `TEMPLATE_NAME` - Template to show configuration for

**Examples:**
```bash
# Show configuration options for demo template
mcp-template config demo
```

### connect

Show integration examples for LLMs and frameworks.

```bash
mcp-template connect TEMPLATE_NAME [OPTIONS]
```

**Arguments:**
- `TEMPLATE_NAME` - Template to show integration examples for

**Options:**
- `--llm {fastmcp,claude,vscode,curl,python}` - Show specific LLM integration example

**Examples:**
```bash
# Show all integration examples
mcp-template connect demo

# Show specific integration
mcp-template connect demo --llm claude
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
