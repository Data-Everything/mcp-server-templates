# Templates Overview

This directory contains all available MCP server templates.

## Available Templates

Each template is a self-contained MCP server implementation with:

- **Complete functionality** - Ready to deploy and use
- **Comprehensive testing** - Unit and integration tests
- **Documentation** - Complete usage guides
- **Docker support** - Containerized deployment
- **Configuration** - Flexible environment-based config

## Template Structure

```
templates/{name}/
├── Dockerfile          # Container build
├── template.json       # Metadata and config schema
├── README.md          # Overview
├── USAGE.md           # Detailed usage
├── requirements.txt   # Python dependencies
├── src/              # Source code
│   └── server.py     # Main MCP server
├── tests/            # Test suite
│   ├── test_*_unit.py
│   └── test_*_integration.py
├── docs/             # Documentation
│   └── index.md      # Template-specific docs
└── config/           # Example configurations
```

## Quality Assurance

All templates go through automated testing before Docker images are built:

- ✅ **Unit Tests** - Fast, isolated functionality tests
- ✅ **Integration Tests** - End-to-end MCP protocol tests
- ✅ **Coverage Analysis** - Minimum 80% code coverage
- ✅ **Configuration Validation** - Schema and documentation checks
- ✅ **Docker Build** - Ensures containers build successfully
- ✅ **Server Startup** - Validates server can initialize

Only templates that pass all tests get published to Docker Hub.

## Using Templates

### Quick Deploy
```bash
# Deploy any template instantly
mcp-template deploy file-server
```

### Docker Direct
```bash
# Pull and run directly with Docker
docker pull dataeverything/mcp-file-server:latest
docker run dataeverything/mcp-file-server:latest
```

### Custom Configuration
```bash
# Deploy with custom config
mcp-template deploy file-server --config my-config.json
```

## Template Development

See the [Template Development Guide](../guides/creating-templates.md) for creating new templates.

## Testing

See [Template Testing Guide](template-testing.md) for details on the testing and release process.
