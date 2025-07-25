# File Server MCP Documentation

## Overview

Secure file system access for AI assistants using the official MCP filesystem server with additional platform integration and configuration options.

## Quick Start

Deploy this template:

```bash
python -m mcp_template deploy file-server
```

## Configuration Options

| Property | Type | Environment Variable | Default | Description |
|----------|------|---------------------|---------|-------------|
| `allowed_directories` | array | `MCP_ALLOWED_DIRS` | `['/data']` | List of directories the server can access. Paths will be mounted and validated for security. |
| `read_only_mode` | boolean | `MCP_READ_ONLY` | `False` | Enable read-only mode to prevent any file modifications |
| `enable_symlinks` | boolean | `MCP_ENABLE_SYMLINKS` | `True` | Allow following symbolic links (with security validation) |
| `max_file_size` | integer | `MCP_MAX_FILE_SIZE` | `100` | Maximum file size for read operations in megabytes |
| `exclude_patterns` | array | `MCP_EXCLUDE_PATTERNS` | `['**/.git/**', '**/node_modules/**', '**/.env*']` | Glob patterns for files/directories to exclude from operations |
| `log_level` | string | `MCP_LOG_LEVEL` | `info` | Logging level for the server |
| `enable_audit` | boolean | `MCP_ENABLE_AUDIT` | `True` | Enable detailed audit logging of file operations |
| `max_concurrent_operations` | integer | `MCP_MAX_CONCURRENT_OPS` | `10` | Maximum number of concurrent file operations |
| `timeout_ms` | integer | `MCP_TIMEOUT_MS` | `30000` | Timeout for file operations in milliseconds |
| `cache_enabled` | boolean | `MCP_CACHE_ENABLED` | `True` | Enable file content caching for better performance |
| `metrics_enabled` | boolean | `MCP_METRICS_ENABLED` | `True` | Enable performance and health metrics collection |

### Usage Examples

```bash
# Deploy with configuration
python -m mcp_template deploy file-server --show-config

# Using environment variables
python -m mcp_template deploy file-server --env MCP_ALLOWED_DIRS=value

# Using CLI configuration
python -m mcp_template deploy {template_id} --config {first_prop}=value

# Using nested configuration
python -m mcp_template deploy {template_id} --config category__property=value
```## Development

### Local Testing

```bash
cd templates/file-server
pytest tests/
```

## Support

For support, please open an issue in the main repository.
