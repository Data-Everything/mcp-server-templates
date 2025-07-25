# Demo Hello MCP Server Documentation

## Overview

A simple demonstration MCP server that provides greeting tools

## Quick Start

Deploy this template:

```bash
python -m mcp_template deploy demo
```

## Configuration Options

| Property | Type | Environment Variable | Default | Description |
|----------|------|---------------------|---------|-------------|
| `hello_from` | string | `MCP_HELLO_FROM` | `MCP Platform` | Name or message to include in greetings |
| `log_level` | string | `MCP_LOG_LEVEL` | `info` | Logging level for the server |

### Usage Examples

```bash
# Deploy with configuration
python -m mcp_template deploy demo --show-config

# Using environment variables
python -m mcp_template deploy demo --env MCP_HELLO_FROM=value

# Using CLI configuration
python -m mcp_template deploy demo --config hello_from=value

# Using nested configuration
python -m mcp_template deploy demo --config category__property=value
```## Development

### Local Testing

```bash
cd templates/demo
pytest tests/
```

## Support

For support, please open an issue in the main repository.
