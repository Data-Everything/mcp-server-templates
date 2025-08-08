# MCP Server Templates

**Comprehensive guide to available MCP server templates, their usage, and creation of custom templates with advanced configuration properties.**

## Overview

MCP Server Templates are pre-configured, production-ready implementations of the Model Context Protocol specification. Each template is designed for specific use cases and provides a complete deployment package including:

- 🔧 **Advanced configuration schemas** with MCP-specific properties (volume_mount, command_arg, sensitive)
- 📖 **Comprehensive documentation** and usage examples
- 🧪 **Built-in testing frameworks** and validation
- 🐳 **Docker containerization** with automatic volume mounting
- ⚙️ **CLI integration** for seamless deployment
- 🔗 **Client integration examples** for popular LLM platforms
- 🚀 **Multiple transport protocols** (stdio, HTTP, SSE)

## Template Configuration Features

### MCP-Specific Properties

| Property | Purpose | Example Use Case |
|----------|---------|------------------|
| `volume_mount: true` | Auto-create Docker volumes from config | Filesystem access, data processing |
| `command_arg: true` | Inject config as command arguments | Configuration files, debug flags |
| `sensitive: true` | Secure handling of secrets | API keys, passwords, tokens |
| `env_mapping` | Map config to environment variables | Application configuration |
| `transport` | Communication protocol options | stdio, HTTP, SSE, streamable-http |

### Configuration Documentation

| Resource | Description | Target Audience |
|----------|-------------|-----------------|
| **[📖 Template.json Reference](template-json-reference.md)** | Complete configuration property guide | All developers |
| **[🚀 Creating Templates](creating.md)** | Step-by-step template creation | Template creators |
| **[🔧 Development Setup](../development/setup.md)** | Advanced development patterns | Core developers |

## Available Templates

### Core Templates

| Template | Description | Use Cases | Status |
|----------|-------------|-----------|---------|
| **[demo](demo.md)** | Basic greeting and echo server | Learning, testing, examples | ✅ Ready |
| **[filesystem](filesystem.md)** | Secure filesystem operations | Document processing, file management | ✅ Ready |

### Database Templates

| Template | Description | Use Cases | Status |
|----------|-------------|-----------|---------|
| **postgres** | PostgreSQL database integration | Data analysis, query execution | 🚧 Development |
| **mongodb** | MongoDB document operations | NoSQL data operations | 🚧 Development |
| **redis** | Redis cache and pub/sub | Caching, real-time messaging | 🚧 Development |

### Integration Templates

| Template | Description | Use Cases | Status |
|----------|-------------|-----------|---------|
| **api-server** | REST API client with auth | External service integration | 🚧 Development |
| **github** | GitHub API integration | Repository operations, CI/CD | 📋 Planned |
| **slack** | Slack workspace integration | Team communication, automation | 📋 Planned |

## Quick Start

### Deploy a Template

```bash
# List available templates
mcpt list

# Deploy demo template
mcpt deploy demo

# Deploy with custom configuration
mcpt deploy filesystem \
  --config security__allowed_dirs='["/data", "/workspace"]' \
  --config security__read_only=false
```

### Explore Template Tools

```bash
# Discover available tools
mcpt> tools demo

# Get detailed tool information
mcpt> tools filesystem --detailed

# Generate integration examples
mcpt connect demo --llm claude
```

## Template Categories

### Learning & Development
- **demo** - Perfect for understanding MCP protocol and testing integrations
- Includes comprehensive examples and documentation

### File Operations
- **filesystem** - Secure filesystem access with configurable permissions
- Supports directory restrictions, read-only modes, and audit logging

### Data & Analytics
- **postgres** - Full-featured PostgreSQL integration with query execution
- **mongodb** - Document database operations with aggregation support
- **redis** - Caching and real-time data operations

### External Integrations
- **api-server** - Generic REST API client with authentication support
- **github** - Repository management and CI/CD automation
- **slack** - Team communication and workflow automation

## Template Features

### Configuration Management
All templates support:
- **Environment Variables**: Automatic parsing with nested structure support
- **Configuration Files**: JSON/YAML configuration with validation
- **CLI Options**: Command-line configuration overrides
- **Schema Validation**: Complete JSON schema validation for all options

### Security Features
- **Access Controls**: Fine-grained permission management
- **Audit Logging**: Comprehensive activity logging
- **Input Validation**: All inputs validated against schemas
- **Container Isolation**: Secure Docker container deployment

### Integration Support
- **Claude Desktop**: Ready-to-use configuration examples
- **VS Code**: Extensions and workspace integration
- **Python Applications**: Client libraries and examples
- **Custom LLMs**: Generic integration patterns

## Development Workflow

### Testing Templates
```bash
# Deploy for testing
mcpt deploy template-name --config debug=true

# Monitor logs
mcpt logs template-name --follow

# Check status
mcpt status template-name --detailed

# Test tools
mcpt connect template-name --test
```

### Template Validation
```bash
# Validate template structure
mcpt validate template-name

# Check configuration schema
mcpt config template-name --show-schema

# Test tool discovery
mcpt> tools --image template:latest
```

## Creating Custom Templates

For detailed information on creating your own templates, see:

- **[Creating Templates Guide](creating.md)** - Step-by-step template creation
- **[Development Guide](../guides/development.md)** - Advanced development patterns
- **[Template Testing](../guides/testing.md)** - Testing and validation strategies

### Quick Template Creation

```bash
# Interactive template creation
mcpt create

# Create from existing image
mcpt create --from-image mcp/custom my-template

# Create with configuration
mcpt create --config-file template-config.json --non-interactive
```

## Template Architecture

### Standard Structure
```
templates/my-template/
├── template.json         # Template metadata and configuration schema
├── Dockerfile           # Container build instructions
├── README.md            # Template documentation
├── src/                 # Source code
│   ├── server.py        # Main MCP server implementation
│   ├── tools.py         # Tool implementations
│   └── config.py        # Configuration management
├── config/              # Configuration examples
│   ├── basic.json       # Basic configuration
│   ├── advanced.json    # Advanced configuration
│   └── production.json  # Production configuration
├── tests/               # Test suite
│   ├── test_server.py   # Server tests
│   ├── test_tools.py    # Tool tests
│   └── test_config.py   # Configuration tests
└── docs/                # Documentation
    ├── usage.md         # Usage examples
    ├── tools.md         # Tool documentation
    └── integration.md   # Integration examples
```

### Template Metadata
Every template includes a `template.json` file with:
- Basic metadata (name, description, version, author)
- Docker configuration (image, ports, volumes)
- MCP configuration (transport, capabilities)
- Configuration schema with environment variable mapping
- Tool definitions and examples

## Best Practices

### Template Design
1. **Clear Documentation** - Comprehensive README with examples
2. **Flexible Configuration** - Support multiple deployment scenarios
3. **Error Handling** - Robust error handling and logging
4. **Security First** - Secure defaults and input validation
5. **Testing Coverage** - Comprehensive test suite

### Deployment Considerations
1. **Resource Limits** - Set appropriate memory and CPU limits
2. **Health Checks** - Implement proper health check endpoints
3. **Logging** - Structured logging with appropriate levels
4. **Monitoring** - Support for metrics and monitoring
5. **Scalability** - Design for horizontal scaling when needed

## Support & Contributing

### Getting Help
- **Documentation**: Check individual template documentation
- **Issues**: [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Community**: [Join our Discord server](https://discord.gg/55Cfxe9gnr)

### Contributing Templates
We welcome community contributions! See our [Contributing Guide](../guides/contributing.md) for:
- Template submission guidelines
- Code review process
- Testing requirements
- Documentation standards

### Commercial Templates
Need a custom template for your specific use case?
- **Custom Development**: We build proprietary templates
- **Enterprise Support**: Commercial support and SLA
- **Contact**: [support@dataeverything.ai](mailto:support@dataeverything.ai)

---

**Next Steps:**
- [Deploy your first template](../getting-started/quickstart.md)
- [Learn about configuration](../user-guide/configuration.md)
- [Explore CLI commands](../cli/index.md)
- [Create a custom template](creating.md)
