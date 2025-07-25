---
# MCP Server Templates Documentation Hub

Welcome to the documentation hub for MCP Server Templates - a production-ready deployment system for Model Context Protocol servers with unified architecture and advanced configuration support.

---

## 🚀 Quick Start Guides

### For Users
- **[Getting Started](../README.md#getting-started)**: Deploy your first MCP server in minutes
- **[Configuration Guide](../README.md#configuration-options)**: Master the flexible configuration system
- **[CLI Reference](../README.md#cli-usage)**: Complete command reference

### For Developers  
- **[Template Development Guide](template-development-guide.md)**: Create new MCP server templates
- **[Configuration Strategy](CONFIGURATION_FINAL_RECOMMENDATIONS.md)**: Deep dive into config system design
- **[Testing Guide](TESTING.md)**: Testing strategies and tools

---

## 📋 Core Documentation

### Architecture & Design
- **[Configuration Strategy](CONFIGURATION_FINAL_RECOMMENDATIONS.md)**: 
  - Multi-source configuration precedence
  - Generic mapping system design
  - Type conversion and validation strategies

- **[Template Development Guide](template-development-guide.md)**:
  - Template structure and requirements
  - Config schema design best practices
  - Docker image creation and tagging

### Development & Testing
- **[Testing Guide](TESTING.md)**:
  - Test structure and organization
  - Configuration testing strategies
  - Integration testing approaches
  - Template validation tests

---

## 🔧 Configuration System

### Overview
The MCP deployment system features a sophisticated configuration management system that supports:

1. **Multiple Sources**: Template defaults → Config files → CLI options → Environment variables
2. **Generic Mapping**: Automatic mapping from nested JSON/YAML to environment variables
3. **Type Conversion**: Schema-based type conversion (string, boolean, integer, array)
4. **Flexible Patterns**: Support for common configuration patterns across templates

### Key Features

#### Multi-Source Configuration
```bash
# Configuration precedence (highest to lowest):
# 1. Environment variables (--env)
# 2. CLI options (--config)  
# 3. Config files (--config-file)
# 4. Template defaults

python -m mcp_deploy file-server 
  --config-file ./base.json \    # Loads base configuration
  --config log_level=warning \   # Overrides file setting
  --env MCP_READ_ONLY=true       # Highest priority
```

#### Generic Config Mapping
The system automatically maps nested configuration structures to environment variables:

```json
{
  "security": {
    "readOnly": true,
    "maxFileSize": 100
  },
  "logging": {
    "level": "debug"
  }
}
```

Maps to environment variables based on template schema:
- `security.readOnly` → `MCP_READ_ONLY=true`
- `security.maxFileSize` → `MCP_MAX_FILE_SIZE=100`
- `logging.level` → `MCP_LOG_LEVEL=debug`

#### Type Conversion
Automatic type conversion based on JSON schema:
- `boolean`: "true"/"false" strings
- `integer`: Numeric conversion with validation
- `array`: Comma-separated values with configurable separators

---

## 📁 Template Structure

### Required Files
Every template must include:

```
templates/{template-name}/
├── template.json          # Metadata and config schema
├── Dockerfile            # Container build instructions  
├── README.md             # Usage documentation
└── src/                  # Implementation code
```

### Optional Files
```
templates/{template-name}/
├── USAGE.md              # Detailed usage guide
├── requirements.txt      # Python dependencies
├── config/              # Default config files
│   ├── default.json
│   └── example.yml
└── tests/               # Template-specific tests
    ├── test_server.py
    └── test_tools.py
```

### Template Configuration Schema
```json
{
  "name": "Template Name",
  "description": "What this template does",
  "docker_image": "dataeverything/template-name",
  "docker_tag": "latest",
  "config_schema": {
    "type": "object",
    "properties": {
      "property_name": {
        "type": "string|boolean|integer|array",
        "env_mapping": "MCP_PROPERTY_NAME",
        "env_separator": ",",          // For arrays
        "file_mapping": "path.to.value", // Explicit file mapping
        "default": "default_value",
        "description": "Property description"
      }
    },
    "required": ["required_property"]
  }
}
```

---

## 🧪 Testing Framework

### Test Organization
```
tests/
├── test_configuration.py      # Configuration system tests
├── test_deployment_*.py       # Deployment backend tests  
├── test_all_templates.py      # Template validation tests
├── test_config_files/         # Sample configuration files
│   ├── file-server-config.json
│   └── __init__.py
└── __pycache__/
```

### Configuration Testing
The test suite includes comprehensive tests for:
- Generic configuration mapping
- Type conversion accuracy
- Multi-source configuration precedence
- Nested pattern matching
- Template-specific configuration validation

### Running Tests
```bash
# All tests
pytest

# Configuration tests only
pytest tests/test_configuration.py -v

# Template validation
pytest tests/test_all_templates.py -v

# With coverage
pytest --cov=mcp_deploy tests/
```

---

## 🏗️ Architecture Deep Dive

### Core Components

```
┌─────────────────┐    ┌──────────────────────┐    ┌────────────────────────┐
│   CLI Interface │────│  DeploymentManager   │────│  Backend Services      │
│                 │    │                      │    │                        │
│ • Argument      │    │ • Template Discovery │    │ • DockerDeployment     │  
│   Parsing       │    │ • Config Preparation │    │ • KubernetesDeployment │
│ • Config        │    │ • Backend Abstraction│    │ • MockDeployment       │
│   Discovery     │    │                      │    │                        │
└─────────────────┘    └──────────────────────┘    └────────────────────────┘
         │                        │                           │
         ▼                        ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐    ┌────────────────────────┐
│ Configuration   │    │  Template Discovery  │    │   Container Runtime    │
│ System          │    │                      │    │                        │
│                 │    │ • Schema Loading     │    │ • Docker Containers    │
│ • Multi-source  │    │ • Metadata Parse     │    │ • Kubernetes Pods      │
│ • Type Convert  │    │ • Auto Discovery     │    │ • Mock Instances       │
│ • Generic Map   │    │                      │    │                        │
└─────────────────┘    └──────────────────────┘    └────────────────────────┘
```

### Design Principles

1. **Generic Configuration**: The mapping system works with any template structure
2. **Backend Abstraction**: Easy to add new deployment targets (K8s, cloud)
3. **Schema-Driven**: Type conversion and validation based on JSON schema
4. **Extensible**: New templates and backends can be added without core changes
5. **Testable**: Comprehensive test coverage with mock backends

---

## 📖 API Reference

### Core Classes

#### `MCPDeployer`
Main CLI interface and orchestration class.

**Key Methods:**
- `deploy(template_name, ...)`: Deploy a template with configuration
- `list_templates()`: Show available templates
- `stop(template_name)`: Stop running deployment
- `logs(template_name)`: View deployment logs
- `cleanup()`: Clean up stopped deployments

#### `DeploymentManager`
Unified deployment abstraction.

**Key Methods:**
- `deploy_template(template_id, configuration, template_data)`: Deploy via backend
- `list_deployments()`: List active deployments
- `delete_deployment(name)`: Remove deployment
- `get_deployment_status(name)`: Get deployment details

#### `TemplateDiscovery`
Template auto-discovery and metadata loading.

**Key Methods:**
- `discover_templates()`: Find and load all templates
- `_load_template_config(template_dir)`: Load single template metadata
- `_generate_template_config(template_data, template_dir)`: Generate deployment config

---

## 🔗 Related Projects

### MCP Platform Ecosystem
- **[MCP Platform Core](https://github.com/Data-Everything/mcp-platform-core)**: Commercial managed hosting platform
- **[MCP Protocol Specification](https://spec.modelcontextprotocol.io/)**: Official MCP documentation
- **[Anthropic MCP](https://github.com/anthropics/mcp)**: Reference implementations

### Template Examples
Each template serves as a reference implementation:
- **file-server**: Secure file system access
- **github**: GitHub API integration  
- **database**: Database connectivity
- **demo**: Simple example template

---

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Make changes following patterns in existing code
4. Add tests for new functionality
5. Update documentation as needed
6. Submit pull request

### Adding New Templates
1. Create template directory structure
2. Implement `template.json` with proper config schema
3. Build and test Docker image
4. Add comprehensive tests
5. Update documentation

### Reporting Issues
- **Bug Reports**: Use GitHub Issues with reproduction steps
- **Feature Requests**: Describe use case and proposed solution
- **Documentation**: Help improve clarity and completeness

---

## 📞 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community help
- **Documentation**: This comprehensive guide and template READMEs
- **Code Examples**: Check `tests/` directory for usage patterns


---
