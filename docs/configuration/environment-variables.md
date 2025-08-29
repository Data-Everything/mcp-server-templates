# Environment Variables

**Comprehensive reference for all environment variables that configure MCP Template behavior.**

## Overview

MCP Templates supports various environment variables to configure system behavior, set defaults, and customize operations. This document provides a complete reference for all available environment variables.

## Discovery and Tool Management

### MCP_DISCOVERY_TIMEOUT
- **Description**: Maximum time (in seconds) to wait for tool discovery operations
- **Default**: `60`
- **Type**: Integer
- **Usage**: Controls timeout for both Docker and Kubernetes probe operations
- **Example**:
  ```bash
  export MCP_DISCOVERY_TIMEOUT=120
  ```

### MCP_DISCOVERY_RETRIES
- **Description**: Number of retry attempts for failed discovery operations
- **Default**: `3`
- **Type**: Integer
- **Usage**: Uses tenacity library for retry logic on subprocess errors, timeouts, and OS errors
- **Example**:
  ```bash
  export MCP_DISCOVERY_RETRIES=5
  ```

### MCP_DISCOVERY_RETRY_SLEEP
- **Description**: Sleep time (in seconds) between discovery retry attempts
- **Default**: `5`
- **Type**: Integer
- **Usage**: Fixed wait time between retries using tenacity's wait_fixed strategy
- **Example**:
  ```bash
  export MCP_DISCOVERY_RETRY_SLEEP=10
  ```

## Backend Configuration

### MCP_BACKEND
- **Description**: Default backend type for deployments
- **Default**: `docker`
- **Type**: String
- **Valid Values**: `docker`, `kubernetes`, `podman`
- **Usage**: Sets the default backend when not explicitly specified in commands
- **Example**:
  ```bash
  export MCP_BACKEND=kubernetes
  ```

### MCP_STDIO_TIMEOUT
- **Description**: Timeout (in seconds) for stdio-based MCP server communications
- **Default**: `30`
- **Type**: Integer
- **Usage**: Used by Docker and Podman backends for stdio protocol timeout
- **Example**:
  ```bash
  export MCP_STDIO_TIMEOUT=60
  ```

## Caching Configuration

### MCP_DEFAULT_CACHE_MAX_AGE_HOURS
- **Description**: Maximum age (in hours) for cached tool discovery results
- **Default**: `24.0`
- **Type**: Float
- **Usage**: Controls persistent cache expiration for discovered tools
- **Example**:
  ```bash
  export MCP_DEFAULT_CACHE_MAX_AGE_HOURS=48.0
  ```

### MCP_CACHE_FILE_PATTERN
- **Description**: File pattern for tool cache files
- **Default**: `*.tools.json`
- **Type**: String
- **Usage**: Glob pattern used to identify cache files for cleanup operations
- **Example**:
  ```bash
  export MCP_CACHE_FILE_PATTERN="*_tools_*.json"
  ```

## CLI Behavior

### MCP_VERBOSE
- **Description**: Enable verbose output by default
- **Default**: `false`
- **Type**: Boolean (string)
- **Valid Values**: `true`, `false`
- **Usage**: Sets default verbosity level for CLI operations
- **Example**:
  ```bash
  export MCP_VERBOSE=true
  ```

### MCP_DRY_RUN
- **Description**: Enable dry-run mode by default
- **Default**: `false`
- **Type**: Boolean (string)
- **Valid Values**: `true`, `false`
- **Usage**: Makes CLI commands show what would be done without executing
- **Example**:
  ```bash
  export MCP_DRY_RUN=true
  ```

## Container Registry

### MCP_DEFAULT_REGISTRY
- **Description**: Default Docker registry for image operations
- **Default**: `docker.io`
- **Type**: String
- **Usage**: Used when pulling or referencing container images without explicit registry
- **Example**:
  ```bash
  export MCP_DEFAULT_REGISTRY=ghcr.io
  ```

## Template Configuration

### MCP_TRANSPORT
- **Description**: Default transport protocol for MCP servers
- **Default**: Server-specific (usually `http`)
- **Type**: String
- **Valid Values**: `stdio`, `http`
- **Usage**: Controls how MCP servers communicate with clients
- **Example**:
  ```bash
  export MCP_TRANSPORT=stdio
  ```

### MCP_LOG_LEVEL
- **Description**: Default logging level for MCP servers and CLI
- **Default**: `info`
- **Type**: String
- **Valid Values**: `debug`, `info`, `warning`, `error`, `critical`
- **Usage**: Controls verbosity of log output across the system
- **Example**:
  ```bash
  export MCP_LOG_LEVEL=debug
  ```

### MCP_CONFIG_FILE
- **Description**: Path to custom configuration file
- **Default**: Server/template specific
- **Type**: String (file path)
- **Usage**: Allows overriding default config file locations
- **Example**:
  ```bash
  export MCP_CONFIG_FILE=/app/config/custom.json
  ```

## Template Creation Variables

### MCP_TEMPLATE_DEFAULT_TRANSPORT
- **Description**: Default transport for newly created templates
- **Default**: `http`
- **Type**: String
- **Valid Values**: `stdio`, `http`
- **Usage**: Used during template creation process
- **Example**:
  ```bash
  export MCP_TEMPLATE_DEFAULT_TRANSPORT=stdio
  ```

### MCP_TEMPLATE_DEFAULT_PYTHON_IMAGE
- **Description**: Default Python base image for template creation
- **Default**: `python:3.10-slim`
- **Type**: String
- **Usage**: Sets the base image for Python-based MCP server templates
- **Example**:
  ```bash
  export MCP_TEMPLATE_DEFAULT_PYTHON_IMAGE=python:3.11-alpine
  ```

## System Environment Variables

### SHELL
- **Description**: User's shell for interactive CLI operations
- **Default**: System default
- **Type**: String
- **Usage**: Used by interactive CLI to provide shell-specific completion and formatting
- **Note**: Standard Unix environment variable, not MCP-specific

## Template-Specific Variables

Templates may define their own environment variables for configuration. Common patterns include:

### Configuration Override Pattern
Templates often support environment variables that override config values:
```bash
export CUSTOM_API_KEY=your-api-key
export CUSTOM_BASE_URL=https://api.example.com
export CUSTOM_FEATURES=feature1,feature2
export CUSTOM_ADVANCED__TIMEOUT=30
export CUSTOM_ADVANCED__RETRY_ATTEMPTS=3
```

### Runtime Behavior
Templates may use environment variables for runtime behavior:
```bash
export DATA_DIR=/custom/data/path
export ENABLED_FEATURES=auth,logging,metrics
```

## Configuration Precedence

Environment variables are processed with the following precedence (highest to lowest):

1. **Command-line arguments** - Explicit flags and options
2. **Environment variables** - System or user-defined variables
3. **Configuration files** - Template or user config files
4. **Template defaults** - Built-in template defaults

## Best Practices

### Development
- Use `.env` files for local development environment variables
- Set `MCP_DRY_RUN=true` for testing configuration changes
- Enable `MCP_VERBOSE=true` for debugging deployment issues

### Production
- Set appropriate timeouts for your infrastructure:
  ```bash
  export MCP_DISCOVERY_TIMEOUT=120
  export MCP_STDIO_TIMEOUT=60
  ```
- Configure caching for better performance:
  ```bash
  export MCP_DEFAULT_CACHE_MAX_AGE_HOURS=72.0
  ```
- Use appropriate backend for your environment:
  ```bash
  export MCP_BACKEND=kubernetes  # For K8s environments
  ```

### Security
- Avoid setting sensitive values directly in environment variables
- Use secure configuration management for API keys and credentials
- Consider using template-specific config files for sensitive data

## Validation

You can verify environment variable configuration using:

```bash
# Check current backend
mcpt config show | grep backend

# Test discovery settings
mcpt tools list --template demo --verbose

# Verify cache settings
mcpt cache status
```

## Related Documentation

- [Configuration](../getting-started/configuration.md) - General configuration guide
- [CLI Deploy](../cli/deploy.md) - Command-line deployment options
- [Template Creation](../templates/creating.md) - Creating custom templates
