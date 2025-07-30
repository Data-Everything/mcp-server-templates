# MCP Server Templates - LLM Developer Guide

**A comprehensive reference for understanding the MCP Server Templates project architecture, components, and development patterns.**

## Project Overview

**MCP Server Templates** is a production-ready deployment system for Model Context Protocol (MCP) servers. It provides a unified architecture for deploying, configuring, and managing MCP server templates with extensive configuration support and multiple deployment backends.

### Core Purpose
- **Template-driven deployment**: Deploy MCP servers from standardized templates
- **Configuration flexibility**: Support multiple configuration sources and patterns
- **Backend abstraction**: Deploy to Docker, Kubernetes, or mock environments
- **Developer experience**: Rich CLI with comprehensive configuration options
- **Template data overrides**: Advanced double underscore notation for template modifications

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐
│   CLI Layer     │    │  Management Layer   │    │    Backend Layer        │
│                 │    │                     │    │                         │
│ ┌─────────────┐ │    │ ┌─────────────────┐ │    │ ┌─────────────────────┐ │
│ │ __init__.py │─┼────┼▶│ DeploymentMgr   │─┼────┼▶│ DockerBackend       │ │
│ │ CLI Parser  │ │    │ │ (manager.py)    │ │    │ │ KubernetesBackend   │ │
│ └─────────────┘ │    │ └─────────────────┘ │    │ │ MockBackend         │ │
│ ┌─────────────┐ │    │ ┌─────────────────┐ │    │ └─────────────────────┘ │
│ │ MCPDeployer │─┼────┼▶│ TemplateDiscov  │ │    │                         │
│ │(deployer.py)│ │    │ │ ConfigMapping   │ │    │                         │
│ └─────────────┘ │    │ └─────────────────┘ │    │                         │
└─────────────────┘    └─────────────────────┘    └──────────────────────────┘

┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐
│ Discovery Layer │    │   Template Layer    │    │      Tools Layer        │
│                 │    │                     │    │                         │
│ ┌─────────────┐ │    │ ┌─────────────────┐ │    │ ┌─────────────────────┐ │
│ │Tool Discovery│ │    │ │ Template JSON   │ │    │ │ Dynamic Discovery   │ │
│ │Docker Probe │ │    │ │ Config Schema   │ │    │ │ Cache Management    │ │
│ │MCP Client   │ │    │ │ Override Logic  │ │    │ │ HTTP Probe          │ │
│ └─────────────┘ │    │ └─────────────────┘ │    │ └─────────────────────┘ │
└─────────────────┘    └─────────────────────┘    └──────────────────────────┘
```

---

## Core Components

### 1. Entry Point & CLI (`mcp_template/__init__.py`)
**Purpose**: Main entry point and argument parsing
- **Key Functions**: `main()`, argument parsing, enhanced CLI integration
- **Features**:
  - Rich CLI interface with argparse
  - Graceful fallback for enhanced CLI features
  - Template deployment orchestration
  - Configuration processing (`--config`, `--override`, `--env`)
- **Exports**: `MCPDeployer`, `TemplateDiscovery`, `DeploymentManager`

### 2. Deployment Orchestrator (`mcp_template/deployer.py`)
**Purpose**: High-level deployment interface and configuration management
- **Class**: `MCPDeployer`
- **Key Methods**:
  - `deploy()`: Main deployment method with override support
  - `list_templates()`: Template discovery and display
  - `_apply_template_overrides()`: Double underscore notation processing
  - `_convert_override_value()`: Type conversion (bool, int, float, JSON)
- **Features**:
  - Template data override system
  - Configuration precedence handling
  - Rich console output with progress indicators
  - MCP config generation

### 3. Backend Management (`mcp_template/manager.py`)
**Purpose**: Backend abstraction and deployment coordination
- **Class**: `DeploymentManager`
- **Backend Support**: Docker, Kubernetes, Mock
- **Key Methods**:
  - `deploy_template()`: Backend-agnostic deployment
  - `_get_deployment_backend()`: Backend selection and caching
- **Features**: Unified interface across different deployment targets

### 4. Backend Implementations (`mcp_template/backends/`)

#### Docker Backend (`docker.py`)
- **Class**: `DockerDeploymentService`
- **Features**: Container management, image pulling, network setup
- **Methods**: `deploy()`, `stop()`, `get_logs()`, `shell_access()`

#### Kubernetes Backend (`kubernetes.py`)
- **Class**: `KubernetesDeploymentService`
- **Features**: Pod/Service management, ConfigMap handling
- **Graceful fallback**: Falls back to Docker if k8s client unavailable

#### Mock Backend (`mock.py`)
- **Class**: `MockDeploymentService`
- **Purpose**: Testing and development without actual deployment

### 5. Template System (`mcp_template/template/`)

#### Template Discovery (`discovery.py`)
- **Class**: `TemplateDiscovery`
- **Purpose**: Automatic template detection and loading
- **Features**:
  - Scans `templates/` directory
  - Validates `template.json` structure
  - Processes configuration schemas
  - Handles volume and port mappings

#### Template Creation (`creation.py`)
- **Class**: `TemplateCreator`
- **Purpose**: Interactive template creation wizard
- **Features**: Scaffolding new templates with proper structure

### 6. Tools & Discovery (`mcp_template/tools/`)

#### Tool Discovery (`discovery.py`)
- **Class**: `ToolDiscovery`
- **Purpose**: Dynamic MCP tool discovery from containers
- **Features**:
  - Multi-endpoint discovery
  - Result normalization
  - Caching system

#### Docker Probe (`docker_probe.py`)
- **Class**: `DockerProbe`
- **Purpose**: Discover tools from Docker containers
- **Features**:
  - Container lifecycle management
  - HTTP endpoint probing
  - Port discovery

#### Cache Management (`cache.py`)
- **Class**: `CacheManager`
- **Purpose**: Tool discovery result caching
- **Features**: TTL-based expiration, JSON serialization

### 7. Enhanced CLI (`mcp_template/cli.py`)
**Purpose**: Advanced CLI features and tool management
- **Class**: `EnhancedCLI`
- **Features**:
  - Tool discovery and listing
  - Configuration display
  - Integration examples
  - Transport-specific deployment

---

## Template Structure

### Template Directory Layout
```
templates/
├── __init__.py
└── demo/
    ├── __init__.py
    ├── template.json          # Template metadata & config schema
    ├── Dockerfile            # Container build instructions
    ├── README.md             # Template documentation
    ├── server.py             # MCP server implementation
    ├── config.py             # Configuration management
    ├── requirements.txt      # Python dependencies
    └── tests/
        ├── __init__.py
        ├── test_demo_server.py
        └── test_config.py
```

### Template JSON Schema
```json
{
  "name": "Template Name",
  "description": "Template description",
  "version": "1.0.0",
  "author": "Author Name",
  "category": "Category",
  "tags": ["tag1", "tag2"],
  "docker_image": "image:tag",
  "ports": {"8080": 8080},
  "volumes": {"/data": "/host/path"},
  "config_schema": {
    "type": "object",
    "properties": {
      "property_name": {
        "type": "string|boolean|number",
        "env_mapping": "ENV_VAR_NAME",
        "default": "default_value",
        "description": "Property description"
      }
    },
    "required": ["required_properties"]
  },
  "transport": {
    "default": "http|stdio",
    "supported": ["http", "stdio"],
    "port": 8080
  }
}
```

---

## Configuration System

### Configuration Sources (Priority Order)
1. **Environment Variables** (`--env`, system env)
2. **CLI Options** (`--config`, `--override`)
3. **Configuration Files** (`--config-file`)
4. **Template Defaults**

### Configuration Types

#### 1. Config Schema Properties (`--config`)
- Maps to `config_schema` properties in `template.json`
- Becomes environment variables via `env_mapping`
- Validated against schema types
- Example: `--config log_level=debug` → `MCP_LOG_LEVEL=debug`

#### 2. Template Data Overrides (`--override`)
- Modifies template JSON structure directly
- Supports double underscore notation: `metadata__version=2.0.0`
- Array indexing: `tools__0__enabled=false`
- Automatic type conversion: `"true"` → `true`, `"123"` → `123`
- Complex structures: `config__db__connection__host=localhost`

### Double Underscore Notation
```bash
# Simple nested override
--override "metadata__version=2.0.0"

# Array element modification
--override "tools__0__enabled=false"
--override "tools__1__description=Updated tool"

# Deep nested structures
--override "config__database__connection__host=localhost"
--override "config__database__connection__port=5432"

# Type conversion examples
--override "config__debug=true"                    # → boolean
--override "config__port=8080"                     # → integer
--override "config__timeout=30.5"                  # → float
--override "config__tags=[\"a\",\"b\"]"            # → JSON array
--override "config__meta={\"key\":\"value\"}"      # → JSON object
```

---

## Key Features

### 1. Template Data Override System
- **Purpose**: Allow modification of template structure without changing template files
- **Implementation**: `_apply_template_overrides()` in `deployer.py`
- **Features**:
  - Nested structure navigation
  - Array index access with auto-extension
  - Automatic type conversion
  - Deep merging of structures

### 2. Tool Discovery System
- **Purpose**: Dynamically discover MCP tools from running containers
- **Components**: `ToolDiscovery`, `DockerProbe`, `CacheManager`
- **Features**:
  - Multi-endpoint probing
  - Result caching with TTL
  - Container lifecycle management
  - Tool normalization

### 3. Backend Abstraction
- **Purpose**: Support multiple deployment targets
- **Pattern**: Strategy pattern with unified interface
- **Benefits**: Easy testing, multiple environments, extensibility

### 4. Rich CLI Experience
- **Features**: Progress indicators, colored output, tables, panels
- **Library**: Rich console library
- **Error handling**: Comprehensive error messages and suggestions

---

## Testing Architecture

### Test Organization
```
tests/
├── test_cli_integration.py     # End-to-end CLI testing
├── test_cli_overrides.py       # Override functionality tests
├── test_backends/              # Backend-specific tests
├── test_template/              # Template system tests
├── test_tools/                 # Tool discovery tests
└── test_demo_simplified.py     # Demo template tests
```

### Key Test Categories

#### 1. CLI Integration Tests (`test_cli_integration.py`)
- **Purpose**: End-to-end CLI functionality
- **Coverage**: Argument parsing, deployment flow, override processing
- **Features**: Mock-based testing, sys.argv manipulation

#### 2. Override System Tests (`test_cli_overrides.py`)
- **Purpose**: Template data override functionality
- **Coverage**: Double underscore notation, type conversion, array handling
- **Edge cases**: Empty values, invalid structures, boundary conditions

#### 3. Tool Discovery Tests (`test_tools/`)
- **Purpose**: Dynamic tool discovery functionality
- **Coverage**: Docker probe, HTTP discovery, caching
- **Mocking**: Docker commands, HTTP requests, filesystem operations

### Testing Patterns
- **Mocking**: Extensive use of `unittest.mock` for external dependencies
- **Fixtures**: pytest fixtures for common test data
- **Parametrization**: Testing multiple scenarios with pytest.mark.parametrize
- **Coverage**: Comprehensive coverage of core functionality

---

## Development Patterns

### 1. Configuration Management Pattern
```python
# Standard config schema properties
config_values = {"log_level": "debug"}  # → MCP_LOG_LEVEL=debug

# Template data overrides
override_values = {"metadata__version": "2.0.0"}  # → Modifies template JSON
```

### 2. Backend Abstraction Pattern
```python
# Unified interface across backends
class DeploymentBackend:
    def deploy(self, template_data, configuration): ...
    def stop(self, deployment_name): ...
    def get_logs(self, deployment_name): ...
```

### 3. Template Discovery Pattern
```python
# Automatic template detection
templates = template_discovery.discover_templates()
# Returns: {"template_name": template_data_dict}
```

### 4. Rich Console Pattern
```python
# Consistent UI experience
console.print(Panel("Deployment Status", border_style="blue"))
with Progress() as progress:
    task = progress.add_task("Deploying...", total=None)
```

---

## Extension Points

### 1. Adding New Backends
1. Create new class in `mcp_template/backends/`
2. Inherit from base backend interface
3. Implement required methods: `deploy()`, `stop()`, `get_logs()`
4. Register in `DeploymentManager._get_deployment_backend()`

### 2. Adding New Templates
1. Create directory in `templates/`
2. Add `template.json` with metadata and config schema
3. Add `Dockerfile` and server implementation
4. Include `README.md` with usage instructions
5. Add tests in `templates/template_name/tests/`

### 3. Extending Tool Discovery
1. Create new probe class in `mcp_template/tools/`
2. Implement discovery methods
3. Add to `ToolDiscovery` integration
4. Include caching support

### 4. CLI Enhancements
1. Add new commands to argument parser in `__init__.py`
2. Implement handlers in `deployer.py` or `cli.py`
3. Add rich console output formatting
4. Include comprehensive help text

---

## Common Development Workflows

### 1. Adding Override Support to New Field
```python
# In deployer.py _apply_template_overrides()
# The system already handles arbitrary nested structures
# No code changes needed - just use: --override "new__field=value"
```

### 2. Adding New Configuration Type
```python
# In _convert_override_value()
if value.startswith('custom:'):
    return parse_custom_format(value[7:])
```

### 3. Adding New Tool Discovery Method
```python
# Create new probe class
class CustomProbe:
    def discover_tools_from_endpoint(self, endpoint): ...

# Register in ToolDiscovery
discovery_methods.append(CustomProbe())
```

---

## Key Dependencies

### Runtime Dependencies
- **fastmcp**: MCP server framework
- **rich**: Terminal formatting and UI
- **requests**: HTTP client for tool discovery
- **pyyaml**: YAML configuration file support
- **docker**: Docker API client (optional)
- **kubernetes**: Kubernetes API client (optional)

### Development Dependencies
- **pytest**: Testing framework
- **pytest-mock**: Mock utilities
- **coverage**: Code coverage analysis
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking

---

## Performance Considerations

### 1. Template Discovery Caching
- Templates are discovered once per deployer instance
- Results cached in memory for subsequent operations

### 2. Tool Discovery Caching
- HTTP responses cached with TTL (6 hours default)
- Reduces redundant container startup for discovery

### 3. Backend Connection Pooling
- Docker client reused across operations
- Kubernetes client cached per manager instance

### 4. Container Lifecycle Management
- Containers created only when needed
- Automatic cleanup of discovery containers

---

## Security Considerations

### 1. Configuration Validation
- Config schema validation prevents injection
- Type checking on override values
- Environment variable sanitization

### 2. Container Security
- No privileged container execution
- Limited volume mounting
- Network isolation options

### 3. Template Validation
- JSON schema validation for template.json
- Dockerfile security scanning (external)
- Dependency vulnerability checking

---

## Debugging and Troubleshooting

### 1. Verbose Logging
```bash
# Enable debug logging
python -m mcp_template deploy demo --verbose
```

### 2. Configuration Inspection
```bash
# Show configuration options
python -m mcp_template deploy demo --show-config
```

### 3. Tool Discovery Debugging
```bash
# Manual tool discovery
python -c "from mcp_template.tools.discovery import ToolDiscovery; print(ToolDiscovery().discover_tools('image:tag'))"
```

### 4. Override Testing
```bash
# Test override syntax
python -c "from mcp_template.deployer import MCPDeployer; print(MCPDeployer()._apply_template_overrides({'test': {}}, {'test__field': 'value'}))"
```

---

## Current State & Recent Changes

### Recent Major Features
1. **Template Data Override System**: Double underscore notation with type conversion
2. **Enhanced Tool Discovery**: Docker probe and HTTP discovery with caching
3. **Backend Abstraction**: Support for Docker, Kubernetes, and Mock backends
4. **Rich CLI Experience**: Progress indicators, colored output, comprehensive help

### Active Development Areas
1. **Template ecosystem expansion**: Adding more server templates
2. **Configuration pattern standardization**: Best practices for template authors
3. **Tool discovery improvements**: Better endpoint detection and normalization
4. **Documentation enhancement**: Comprehensive guides and examples

### Known Limitations
1. **Kubernetes backend**: Limited testing in production environments
2. **Windows support**: Some path handling may need adjustment
3. **Template validation**: Could benefit from more comprehensive schema validation
4. **Error recovery**: Some failure scenarios could have better recovery mechanisms

---

This document provides a comprehensive understanding of the MCP Server Templates project. For specific implementation details, refer to the individual source files and their docstrings.
