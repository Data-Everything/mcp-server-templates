# CLI Reference

This document provides comprehensive reference for the MCP Template CLI tool.

## Installation

```bash
pip install mcp-template
```

## Usage

```bash
mcpt [OPTIONS] COMMAND [ARGS]...
```

The MCP Template CLI provides commands to deploy and manage Model Context Protocol servers.

## Global Options

- `--verbose, -v` - Enable verbose output
- `--backend TEXT` - Backend type to use (default: docker)
- `--help` - Show help message and exit

## Commands

### deploy

Deploy an MCP server template.

```bash
mcpt deploy [OPTIONS] TEMPLATE
```

**Arguments:**
- `TEMPLATE` - Template name to deploy (required)

**Options:**
- `--config, -c PATH` - Path to config file
- `--env, -e TEXT` - Environment variables (KEY=VALUE), can be used multiple times
- `--set TEXT` - Config overrides (key=value), can be used multiple times
- `--override TEXT` - Template data overrides (key=value). Supports double underscore notation for nested fields, e.g., tools__0__custom_field=value
- `--transport TEXT` - Transport protocol (http, stdio)
- `--no-pull` - Don't pull latest Docker image
- `--dry-run` - Show what would be deployed without actually deploying

**Examples:**
```bash
# Basic deployment
mcpt deploy demo

# Deploy with configuration file
mcpt deploy github --config github-config.json

# Deploy with config overrides
mcpt deploy filesystem --set allowed_dirs=/tmp --dry-run

# Deploy with template data overrides
mcpt deploy demo --override metadata__version=2.0 --transport stdio

# Deploy with environment variables
mcpt deploy demo --env PORT=8080 --env DEBUG=true
```

### list

List available MCP server templates with deployment status.

```bash
mcpt list [OPTIONS]
```

**Options:**
- `--deployed` - Show only deployed templates

This command shows all templates that can be deployed, along with their current deployment status and running instance count.

**Examples:**
```bash
# List all templates
mcpt list

# Show only deployed templates
mcpt list --deployed
```

### list-tools

List available tools from a template or deployment.

```bash
mcpt list-tools [OPTIONS] TEMPLATE
```

**Arguments:**
- `TEMPLATE` - Template name or deployment ID (required)

**Options:**
- `--method TEXT` - Discovery method (default: auto)
- `--force-refresh` - Force refresh cache
- `--format TEXT` - Output format (table, json) (default: table)

This command discovers and displays tools available from MCP servers. The discovery method indicates how the tools were found.

**Examples:**
```bash
# List tools for a template
mcpt list-tools github

# List tools with cache refresh
mcpt list-tools demo-12345 --force-refresh

# List tools with JSON output
mcpt list-tools filesystem --method static --format json
```

### list-templates

List available MCP server templates.

```bash
mcpt list-templates [OPTIONS]
```

This command shows all templates that can be deployed.

**Examples:**
```bash
mcpt list-templates
```

### list-deployments

List running MCP server deployments.

```bash
mcpt list-deployments [OPTIONS]
```

This command shows all currently running MCP servers.

**Examples:**
```bash
mcpt list-deployments
```

### stop

Stop a running MCP server deployment.

```bash
mcpt stop [OPTIONS] DEPLOYMENT_ID
```

**Arguments:**
- `DEPLOYMENT_ID` - Deployment ID to stop (required)

**Options:**
- `--dry-run` - Show what would be stopped

This command stops and removes the specified deployment.

**Examples:**
```bash
# Stop a deployment
mcpt stop demo-12345

# Preview what would be stopped
mcpt stop demo-12345 --dry-run
```

### cleanup

Clean up stopped containers and unused resources.

```bash
mcpt cleanup [OPTIONS] [TEMPLATE]
```

**Arguments:**
- `TEMPLATE` - Template to cleanup (or all if not specified) (optional)

**Options:**
- `--dry-run` - Show what would be cleaned up
- `--force` - Force cleanup without confirmation

This command removes stopped containers and cleans up resources.

**Examples:**
```bash
# Clean up all stopped containers
mcpt cleanup

# Clean up specific template
mcpt cleanup demo

# Preview cleanup
mcpt cleanup --dry-run
```

### interactive

Start the interactive CLI mode.

```bash
mcpt interactive [OPTIONS]
```

This command launches an interactive shell for MCP server management. See [Interactive CLI Guide](../interactive-cli/commands.md) for details.

**Examples:**
```bash
mcpt interactive
```

### install-completion

Install shell completion for the CLI.

```bash
mcpt install-completion [OPTIONS]
```

This command installs shell completion for Bash, Zsh, Fish, or PowerShell.

**Examples:**
```bash
mcpt install-completion
```

## Configuration

### Configuration Files

Configuration can be provided via JSON or YAML files:

```json
{
  "greeting": "Hello from config file",
  "port": 8080,
  "debug": true,
  "security": {
    "read_only": false,
    "max_file_size": "100MB"
  }
}
```

### Environment Variables

Environment variables can be set using `--env`:

```bash
mcpt deploy demo --env PORT=8080 --env DEBUG=true
```

### Configuration Overrides

Use `--set` for config schema properties:

```bash
mcpt deploy filesystem --set allowed_dirs=/tmp --set read_only=true
```

### Template Data Overrides

Use `--override` for template data with double underscore notation:

```bash
mcpt deploy demo --override metadata__version=2.0 --override tools__0__custom_field=value
```

### Configuration Priority

Configuration is merged in the following order (highest to lowest priority):

1. Command line overrides (`--override`, `--set`)
2. Environment variables (`--env`)
3. Configuration file (`--config`)
4. Template defaults

## Error Handling

The CLI returns appropriate exit codes:

- `0` - Success
- `1` - General error
- `2` - Command line argument error

Use `--verbose` to see detailed error information.

## Completion

The CLI supports shell completion for:

- Commands and subcommands
- Template names
- Deployment IDs
- Configuration options

Install completion with:

```bash
mcpt install-completion
```

Delete a deployment.

```bash
mcpt delete DEPLOYMENT_NAME [OPTIONS]
```

**Arguments:**
- `DEPLOYMENT_NAME` - Name of the deployment to delete

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to use (default: docker)

**Examples:**
```bash
# Delete Docker deployment
mcpt delete demo-deployment

# Delete Kubernetes deployment
mcpt delete demo-deployment --backend k8s
```

### status

Get status information for a deployment.

```bash
mcpt status DEPLOYMENT_NAME [OPTIONS]
```

**Arguments:**
- `DEPLOYMENT_NAME` - Name of the deployment

**Options:**
- `--backend {docker,k8s,mock}` - Deployment backend to use (default: docker)

**Examples:**
```bash
# Get Docker deployment status
mcpt status demo-deployment

# Get Kubernetes deployment status
mcpt status demo-deployment --backend k8s
```

### tools

List available tools for a template or discover tools from a Docker image.

```bash
mcpt> tools TEMPLATE_NAME [OPTIONS]
mcpt> tools --image IMAGE_NAME [SERVER_ARGS...]
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
mcpt> tools demo

# List tools with cache refresh
mcpt> tools demo --refresh

# List tools for dynamic template with config
mcpt> tools github --config github_token=your_token

# Discover tools from Docker image
mcpt> tools --image mcp/filesystem /tmp

# Discover tools with multiple config values
mcpt> tools github --config github_token=token --config log_level=DEBUG
```

**Note:** For templates with `tool_discovery: "dynamic"`, if standard discovery methods fail, the command will automatically attempt to spin up the Docker image specified in the template configuration to discover tools dynamically.

### config

Show configuration options for a template.

```bash
mcpt config TEMPLATE_NAME
```

**Arguments:**
- `TEMPLATE_NAME` - Template to show configuration for

**Examples:**
```bash
# Show configuration options for demo template
mcpt config demo
```

### connect

Show integration examples for LLMs and frameworks.

```bash
mcpt connect TEMPLATE_NAME [OPTIONS]
```

**Arguments:**
- `TEMPLATE_NAME` - Template to show integration examples for

**Options:**
- `--llm {fastmcp,claude,vscode,curl,python}` - Show specific LLM integration example

**Examples:**
```bash
# Show all integration examples
mcpt connect demo

# Show specific integration
mcpt connect demo --llm claude
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
