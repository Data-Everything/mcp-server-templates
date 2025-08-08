# Creating Custom Templates

**Comprehensive guide to creating custom MCP server templates with interactive guidance, best practices, and production deployment strategies.**

## Overview

Creating custom MCP server templates allows you to package your specific business logic, APIs, and data sources as reusable MCP servers. The MCP Template Platform provides comprehensive tools for template creation, validation, and deployment.

### What You'll Learn
- Template structure and requirements
- Interactive template creation process
- Configuration schema design with MCP-specific properties
- Volume mount and command argument patterns
- Transport configuration (stdio, HTTP, SSE)
- Tool implementation patterns
- Testing and validation strategies
- Deployment and distribution

### Quick Reference

- **📖 [Template.json Reference](template-json-reference.md)** - Complete configuration property guide
- **🔧 Configuration Properties** - volume_mount, command_arg, sensitive, env_mapping
- **🚀 Transport Options** - stdio, http, sse, streamable-http
- **🛠️ Tool Discovery** - static, dynamic, hybrid approaches

## Quick Start

### Interactive Template Creation

The fastest way to create a new template:

```bash
# Start interactive template creation wizard
mcp-template create

# Example interactive session:
╭─────────────────────────────────────────────────────────────╮
│              🛠️  MCP Template Creator                       │
╰─────────────────────────────────────────────────────────────╯

📝 Template Information:
Template ID: my-api-server
Template Name: My API Server
Description: Custom API integration server
Version [1.0.0]: 1.0.0
Author: Your Name
Category [general]: api
Tags (comma-separated): rest,api,integration

🐳 Docker Configuration:
Base image [python:3.11-slim]: python:3.11-slim
Registry [dataeverything]: myregistry
Port [8080]: 8080

🔧 MCP Configuration:
Default transport [stdio]: stdio
HTTP port [8080]: 8080

📋 Tools Configuration:
Add tools interactively? [y/N]: y
Tool name: fetch_data
Tool description: Fetch data from external API
Add parameters? [y/N]: y
Parameter name: endpoint
Parameter type [string]: string
Required [y/N]: y

⚙️  Configuration Schema:
Add config options? [y/N]: y
Config option: api_base_url
Type [string]: string
Description: Base URL for the API
Default: https://api.example.com
Required [y/N]: y
Environment variable: API_BASE_URL

✅ Template created at: templates/my-api-server/
📁 Generated files:
  - template.json (template configuration)
  - Dockerfile (container definition)
  - src/server.py (MCP server implementation)
  - src/tools.py (tool implementations)
  - README.md (documentation)
```

### Create with Specific Template ID

```bash
# Create template with specific ID
mcp-template create my-database-server

# Skips the template ID prompt
```

### Non-Interactive Creation

```bash
# Create from configuration file
mcp-template create --config-file template-config.json --non-interactive

# Example template-config.json:
{
  "id": "weather-server",
  "name": "Weather API Server",
  "description": "MCP server for weather data integration",
  "version": "1.0.0",
  "author": "Weather Corp",
  "category": "api",
  "tags": ["weather", "api", "forecast"],
  "docker": {
    "base_image": "python:3.11-slim",
    "registry": "weathercorp",
    "port": 8080
  },
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for location",
      "parameters": {
        "location": {"type": "string", "required": true},
        "units": {"type": "string", "default": "metric"}
      }
    }
  ],
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "Weather API key",
      "required": true,
      "env_mapping": "WEATHER_API_KEY"
    }
  }
}
```

### Create from Existing Image

```bash
# Create template from MCP-compatible Docker image
mcp-template create --from-image mcp/filesystem my-filesystem

# Automatically discovers tools and generates template structure
```

## Template Structure

### Required Files

Every template must include these essential files:

```
templates/my-template/
├── template.json         # ✅ Required: Template metadata and config schema
├── Dockerfile           # ✅ Required: Container build instructions
└── README.md            # ⚠️  Recommended: Template documentation
```

### Recommended Structure

For production templates, use this comprehensive structure:

```
templates/my-template/
├── template.json         # Template configuration and metadata
├── Dockerfile           # Container definition
├── README.md            # Template overview and usage
├── USAGE.md             # Detailed configuration guide
├── docker-compose.yml   # Local development setup
├── requirements.txt     # Python dependencies
├── src/                 # Source code
│   ├── __init__.py      # Package initialization
│   ├── server.py        # Main MCP server implementation
│   ├── tools.py         # Tool implementations
│   └── config.py        # Configuration management
├── config/              # Configuration examples
│   ├── basic.json       # Basic configuration
│   ├── advanced.json    # Advanced configuration
│   └── production.json  # Production configuration
├── tests/               # Test suite
│   ├── __init__.py      # Test package
│   ├── test_server.py   # Server tests
│   ├── test_tools.py    # Tool tests
│   └── test_config.py   # Configuration tests
└── docs/                # Documentation
    ├── usage.md         # Usage examples
    ├── tools.md         # Tool documentation
    └── integration.md   # Integration examples
```

## Template Configuration (template.json)

### Complete Example

```json
{
  "id": "my-custom-template",
  "name": "My Custom Template",
  "description": "Custom MCP server for specific business needs",
  "version": "1.0.0",
  "author": "Your Company",
  "category": "business",
  "tags": ["custom", "api", "business"],
  "docker": {
    "image": "mycompany/mcp-custom",
    "tag": "latest",
    "base_image": "python:3.11-slim",
    "port": 8080,
    "volumes": [
      {"host": "./data", "container": "/app/data"},
      {"host": "./config", "container": "/app/config"}
    ],
    "environment": {
      "PYTHONPATH": "/app/src",
      "MCP_LOG_LEVEL": "INFO"
    }
  },
  "mcp": {
    "protocol_version": "2025-06-18",
    "default_transport": "stdio",
    "supported_transports": ["stdio", "http"],
    "http_port": 8080,
    "capabilities": ["tools"]
  },
  "tools": [
    {
      "name": "process_data",
      "description": "Process business data with custom logic",
      "category": "data",
      "parameters": {
        "type": "object",
        "properties": {
          "input_data": {
            "type": "string",
            "description": "Input data to process"
          },
          "processing_mode": {
            "type": "string",
            "enum": ["fast", "thorough", "custom"],
            "default": "fast",
            "description": "Processing mode"
          }
        },
        "required": ["input_data"]
      }
    }
  ],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API authentication key",
        "env_mapping": "CUSTOM_API_KEY",
        "required": true
      },
      "base_url": {
        "type": "string",
        "description": "Base URL for external API",
        "default": "https://api.example.com",
        "env_mapping": "CUSTOM_BASE_URL"
      },
      "features": {
        "type": "array",
        "description": "Enabled features list",
        "env_mapping": "CUSTOM_FEATURES",
        "env_separator": ",",
        "default": ["feature1", "feature2"]
      },
      "advanced": {
        "type": "object",
        "description": "Advanced configuration options",
        "env_mapping": "CUSTOM_ADVANCED",
        "env_separator": "__",
        "properties": {
          "timeout": {
            "type": "integer",
            "description": "Request timeout in seconds",
            "default": 30,
            "env_mapping": "CUSTOM_ADVANCED__TIMEOUT"
          },
          "retry_attempts": {
            "type": "integer",
            "description": "Number of retry attempts",
            "default": 3,
            "env_mapping": "CUSTOM_ADVANCED__RETRY_ATTEMPTS"
          }
        }
      }
    },
    "required": ["api_key"]
  }
}
```

### Configuration Schema Features

#### Environment Variable Mapping
```json
{
  "config_option": {
    "type": "string",
    "env_mapping": "MCP_CONFIG_OPTION",
    "description": "Maps to MCP_CONFIG_OPTION environment variable"
  },
  "nested_config": {
    "type": "object",
    "env_mapping": "MCP_NESTED",
    "env_separator": "__",
    "properties": {
      "sub_option": {
        "env_mapping": "MCP_NESTED__SUB_OPTION"
      }
    }
  },
  "array_config": {
    "type": "array",
    "env_mapping": "MCP_ARRAY_CONFIG",
    "env_separator": ",",
    "default": ["item1", "item2"]
  }
}
```

#### Type Validation
```json
{
  "string_field": {"type": "string", "minLength": 1, "maxLength": 100},
  "number_field": {"type": "integer", "minimum": 0, "maximum": 1000},
  "boolean_field": {"type": "boolean", "default": false},
  "enum_field": {"type": "string", "enum": ["option1", "option2", "option3"]},
  "object_field": {
    "type": "object",
    "properties": {
      "nested_string": {"type": "string"}
    },
    "required": ["nested_string"]
  }
}
```

## Implementation Patterns

### MCP Server Implementation (src/server.py)

```python
#!/usr/bin/env python3
"""
Custom MCP Server Template

Generated by MCP Template Creator
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.tools import tool

from .config import load_config
from .tools import CustomTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("My Custom Template")

class CustomMCPServer:
    """Custom MCP Server Implementation"""

    def __init__(self):
        self.config = load_config()
        self.tools = CustomTools(self.config)
        self._register_tools()

    def _register_tools(self):
        """Register all available tools"""

        @tool("process_data")
        async def process_data(
            input_data: str,
            processing_mode: str = "fast"
        ) -> Dict[str, Any]:
            """Process business data with custom logic"""
            return await self.tools.process_data(input_data, processing_mode)

        @tool("get_status")
        async def get_status() -> Dict[str, Any]:
            """Get server status and configuration"""
            return await self.tools.get_status()

        logger.info("Registered tools: process_data, get_status")

async def main():
    """Main server entry point"""
    server = CustomMCPServer()
    logger.info("Custom MCP server starting...")
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Tool Implementation (src/tools.py)

```python
"""
Tool implementations for Custom MCP Server
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class CustomTools:
    """Custom tool implementations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.example.com")

    async def process_data(self, input_data: str, processing_mode: str) -> Dict[str, Any]:
        """
        Process business data with custom logic

        Args:
            input_data: Input data to process
            processing_mode: Processing mode (fast, thorough, custom)

        Returns:
            Dict containing processing results
        """
        try:
            # Implement your custom processing logic here
            processed_result = f"Processed '{input_data}' using {processing_mode} mode"

            logger.info(f"Data processed: mode={processing_mode}, input_length={len(input_data)}")

            return {
                "success": True,
                "result": processed_result,
                "processing_mode": processing_mode,
                "input_data": input_data,
                "timestamp": "2025-01-27T16:47:30Z"
            }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_data": input_data,
                "processing_mode": processing_mode
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get server status and configuration"""
        return {
            "server": "Custom MCP Server",
            "version": "1.0.0",
            "status": "healthy",
            "config": {
                "api_configured": bool(self.api_key),
                "base_url": self.base_url,
                "features_enabled": self.config.get("features", [])
            },
            "timestamp": "2025-01-27T16:47:30Z"
        }
```

### Configuration Management (src/config.py)

```python
"""
Configuration management for Custom MCP Server
"""

import json
import os
from typing import Any, Dict, Optional

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and config files

    Configuration precedence:
    1. Environment variables (highest)
    2. Config file
    3. Template defaults (lowest)
    """

    config = {}

    # Load from environment variables
    config.update(_load_from_env())

    # Load from config file if present
    config_file = os.environ.get("MCP_CONFIG_FILE", "/app/config/config.json")
    if os.path.exists(config_file):
        with open(config_file) as f:
            file_config = json.load(f)
        config.update(file_config)

    # Apply defaults
    defaults = {
        "base_url": "https://api.example.com",
        "features": ["feature1", "feature2"],
        "advanced": {
            "timeout": 30,
            "retry_attempts": 3
        }
    }

    for key, value in defaults.items():
        if key not in config:
            config[key] = value

    return config

def _load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {}

    # Simple string variables
    if os.environ.get("CUSTOM_API_KEY"):
        config["api_key"] = os.environ["CUSTOM_API_KEY"]

    if os.environ.get("CUSTOM_BASE_URL"):
        config["base_url"] = os.environ["CUSTOM_BASE_URL"]

    # Array variables (comma-separated)
    if os.environ.get("CUSTOM_FEATURES"):
        config["features"] = [
            feature.strip()
            for feature in os.environ["CUSTOM_FEATURES"].split(",")
        ]

    # Nested configuration (double underscore separator)
    advanced = {}
    if os.environ.get("CUSTOM_ADVANCED__TIMEOUT"):
        advanced["timeout"] = int(os.environ["CUSTOM_ADVANCED__TIMEOUT"])

    if os.environ.get("CUSTOM_ADVANCED__RETRY_ATTEMPTS"):
        advanced["retry_attempts"] = int(os.environ["CUSTOM_ADVANCED__RETRY_ATTEMPTS"])

    if advanced:
        config["advanced"] = advanced

    return config
```

## Testing Your Template

### Validation

```bash
# Validate template structure and configuration
mcp-template validate my-template

# Check configuration schema
mcp-template config my-template --show-schema

# Test configuration parsing
mcp-template config my-template --test-config config.json
```

### Deployment Testing

```bash
# Deploy for testing
mcp-template deploy my-template --config debug=true

# Check deployment status
mcp-template status my-template

# Test tool discovery
mcp-template tools my-template

# Test tools interactively
mcp-template connect my-template --test
```

### Integration Testing

```bash
# Generate Claude Desktop integration
mcp-template connect my-template --llm claude

# Test with VS Code
mcp-template connect my-template --llm vscode

# Generate Python client code
mcp-template connect my-template --llm python
```

## MCP Template Configuration

### Understanding MCP-Specific Properties

The MCP Template Platform extends standard configuration with powerful properties for Docker integration, environment management, and transport handling. Understanding these properties is essential for creating robust templates.

#### Volume Mount Configuration (`volume_mount`)

**Purpose**: Automatically create Docker volume mounts from configuration values, enabling secure host filesystem access.

**Basic Example**:
```json
{
  "data_directory": {
    "type": "string",
    "title": "Data Directory",
    "description": "Local directory for data storage",
    "env_mapping": "DATA_DIR",
    "volume_mount": true
  }
}
```

**How it works**:
- User input: `"/home/user/documents"`
- Creates volume: `-v "/home/user/documents:/data/documents:rw"`
- Environment: `DATA_DIR="/data/documents"`

**Multiple Paths Example**:
```json
{
  "allowed_paths": {
    "type": "string",
    "title": "Allowed File Paths",
    "description": "Space-separated list of allowed paths",
    "env_mapping": "ALLOWED_PATHS",
    "volume_mount": true,
    "command_arg": true
  }
}
```

**Advanced Usage**:
- Input: `"/home/user/docs /tmp/workspace /opt/data"`
- Creates volumes:
  ```
  -v "/home/user/docs:/data/docs:rw"
  -v "/tmp/workspace:/data/workspace:rw"
  -v "/opt/data:/data/data:rw"
  ```
- Environment: `ALLOWED_PATHS="/data/docs /data/workspace /data/data"`

#### Command Argument Injection (`command_arg`)

**Purpose**: Inject configuration values as command-line arguments to your container.

**Basic Example**:
```json
{
  "config_file": {
    "type": "string",
    "title": "Config File Path",
    "description": "Path to application configuration file",
    "env_mapping": "CONFIG_FILE",
    "command_arg": true
  }
}
```

**How it works**:
- User input: `"/etc/app/config.json"`
- Adds to command: `--config-file=/etc/app/config.json`

**Combined with Volume Mount**:
```json
{
  "ssl_cert_dir": {
    "type": "string",
    "title": "SSL Certificate Directory",
    "description": "Directory containing SSL certificates",
    "env_mapping": "SSL_CERT_DIR",
    "volume_mount": true,
    "command_arg": true
  }
}
```

**Result**:
- Volume: `-v "/etc/ssl/certs:/data/ssl:rw"`
- Environment: `SSL_CERT_DIR="/data/ssl"`
- Command arg: `--ssl-cert-dir=/data/ssl`

#### Sensitive Configuration (`sensitive`)

**Purpose**: Mark sensitive data for proper handling in logs, UI, and storage.

```json
{
  "api_key": {
    "type": "string",
    "title": "API Key",
    "description": "Authentication key for external service",
    "env_mapping": "API_KEY",
    "sensitive": true
  },
  "database_password": {
    "type": "string",
    "title": "Database Password",
    "description": "Password for database connection",
    "env_mapping": "DB_PASSWORD",
    "sensitive": true
  }
}
```

**Benefits**:
- Values masked in platform logs: `API_KEY=***`
- UI hides values with password fields
- Configuration files exclude sensitive values from plain text

#### Environment Variable Mapping (`env_mapping`)

**Purpose**: Map configuration properties to environment variables in your container.

**Standard Mapping**:
```json
{
  "log_level": {
    "type": "string",
    "title": "Log Level",
    "description": "Application logging level",
    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
    "default": "INFO",
    "env_mapping": "LOG_LEVEL"
  }
}
```

**Array Handling with Separators**:
```json
{
  "allowed_domains": {
    "type": "array",
    "title": "Allowed Domains",
    "description": "List of allowed domains",
    "items": {"type": "string"},
    "env_mapping": "ALLOWED_DOMAINS",
    "env_separator": ","
  }
}
```

**Result**: `ALLOWED_DOMAINS="domain1.com,domain2.com,domain3.com"`

### Transport Configuration

#### stdio Transport (Default)

**Best for**: Command-line tools, local development, direct integration

```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio"]
  }
}
```

**Container Command**: Direct execution with stdin/stdout communication

#### HTTP Transport

**Best for**: Web integration, REST APIs, remote access

```json
{
  "transport": {
    "default": "http",
    "supported": ["http", "stdio"],
    "port": 8080
  },
  "ports": {
    "8080": 8080
  }
}
```

**Features**:
- RESTful API endpoints
- Tool discovery at `/tools`
- Health checks at `/health`
- OpenAPI documentation

#### Server-Sent Events (SSE)

**Best for**: Real-time streaming, event-driven applications

```json
{
  "transport": {
    "default": "sse",
    "supported": ["sse", "http"],
    "port": 8080
  }
}
```

**Features**:
- Streaming responses
- Real-time updates
- Event-based communication

#### Multi-Transport Support

```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http", "sse"],
    "port": 8080
  }
}
```

**Benefits**:
- Flexibility for different use cases
- Platform can choose optimal transport
- Migration path between transports

### Tool Discovery Configuration

#### Dynamic Discovery (Recommended)

```json
{
  "tool_discovery": "dynamic",
  "tool_endpoint": "/tools"
}
```

**How it works**:
- Platform starts container
- Queries `/tools` endpoint
- Discovers available tools at runtime
- Supports tool changes without template updates

#### Static Discovery

```json
{
  "tool_discovery": "static",
  "tools": [
    {
      "name": "process_file",
      "description": "Process a file with custom logic",
      "parameters": {
        "file_path": {"type": "string", "required": true},
        "mode": {"type": "string", "default": "standard"}
      }
    }
  ]
}
```

**Use when**:
- Tools are fixed and won't change
- Performance-critical environments
- Offline or restricted environments

#### Hybrid Discovery

```json
{
  "tool_discovery": "hybrid",
  "tool_endpoint": "/tools",
  "tools": [
    {
      "name": "core_function",
      "description": "Core functionality always available"
    }
  ]
}
```

**Benefits**:
- Guaranteed core tools from static definition
- Additional tools from dynamic discovery
- Fallback if dynamic discovery fails

### Real-World Configuration Examples

#### Filesystem Template with Security

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "allowed_directories": {
        "type": "string",
        "title": "Allowed Directories",
        "description": "Space-separated allowed directories for file access",
        "env_mapping": "ALLOWED_DIRS",
        "volume_mount": true,
        "command_arg": true
      },
      "max_file_size": {
        "type": "integer",
        "title": "Max File Size (MB)",
        "description": "Maximum file size for operations in megabytes",
        "default": 100,
        "env_mapping": "MAX_FILE_SIZE"
      },
      "read_only": {
        "type": "boolean",
        "title": "Read Only Mode",
        "description": "Enable read-only mode for security",
        "default": false,
        "env_mapping": "READ_ONLY_MODE"
      }
    },
    "required": ["allowed_directories"]
  }
}
```

#### API Integration Template

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "api_base_url": {
        "type": "string",
        "title": "API Base URL",
        "description": "Base URL for the external API",
        "default": "https://api.example.com",
        "env_mapping": "API_BASE_URL"
      },
      "api_key": {
        "type": "string",
        "title": "API Key",
        "description": "Authentication key for API access",
        "env_mapping": "API_KEY",
        "sensitive": true
      },
      "rate_limit_requests": {
        "type": "integer",
        "title": "Rate Limit (requests/minute)",
        "description": "Maximum requests per minute",
        "default": 60,
        "env_mapping": "RATE_LIMIT"
      },
      "timeout_seconds": {
        "type": "integer",
        "title": "Request Timeout",
        "description": "HTTP request timeout in seconds",
        "default": 30,
        "env_mapping": "TIMEOUT_SECONDS"
      },
      "enable_caching": {
        "type": "boolean",
        "title": "Enable Response Caching",
        "description": "Cache API responses for performance",
        "default": true,
        "env_mapping": "ENABLE_CACHING"
      },
      "allowed_endpoints": {
        "type": "array",
        "title": "Allowed API Endpoints",
        "description": "List of allowed API endpoints",
        "items": {"type": "string"},
        "default": ["/users", "/data", "/status"],
        "env_mapping": "ALLOWED_ENDPOINTS",
        "env_separator": ","
      }
    },
    "required": ["api_key"]
  }
}
```

## Best Practices

### Template Design

1. **Clear Documentation**
   - Comprehensive README with usage examples
   - Tool documentation with parameter descriptions
   - Configuration guide with all options

2. **Flexible Configuration**
   - Support environment variables, files, and CLI options
   - Provide sensible defaults
   - Include development and production configurations

3. **Error Handling**
   - Comprehensive error handling in all tools
   - Meaningful error messages
   - Proper logging with appropriate levels

4. **Security**
   - Input validation for all parameters
   - Secure handling of API keys and secrets
   - Principle of least privilege

5. **Testing**
   - Unit tests for all tools
   - Integration tests with real deployments
   - Configuration validation tests

### Performance Considerations

1. **Resource Efficiency**
   - Optimize Docker image size
   - Use appropriate base images
   - Implement proper caching strategies

2. **Scalability**
   - Design for horizontal scaling
   - Minimize external dependencies
   - Use async/await patterns

3. **Monitoring**
   - Implement health check endpoints
   - Structured logging
   - Metrics collection

## Distribution

### Template Registry

```bash
# Package template for distribution
mcp-template package my-template

# Validate package
mcp-template validate-package my-template.tar.gz

# Submit to template registry
mcp-template submit my-template.tar.gz
```

### Docker Registry

```bash
# Build and push Docker image
cd templates/my-template
docker build -t myregistry/mcp-my-template:latest .
docker push myregistry/mcp-my-template:latest

# Update template.json with new image
{
  "docker": {
    "image": "myregistry/mcp-my-template",
    "tag": "latest"
  }
}
```

## Advanced Topics

### Multi-Language Templates

While Python is the primary language, you can create templates in other languages:

```dockerfile
# Node.js template example
FROM node:18-slim

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY src/ ./src/
COPY platform-wrapper.js ./

EXPOSE 8080
CMD ["node", "platform-wrapper.js"]
```

### Custom Transport Protocols

```json
{
  "mcp": {
    "default_transport": "http",
    "supported_transports": ["stdio", "http", "websocket"],
    "http_port": 8080,
    "websocket_port": 8081,
    "custom_endpoints": {
      "/health": "GET",
      "/metrics": "GET"
    }
  }
}
```

### Enterprise Features

```json
{
  "enterprise": {
    "rbac": {
      "enabled": true,
      "roles": ["admin", "user", "readonly"]
    },
    "audit_logging": {
      "enabled": true,
      "destination": "syslog"
    },
    "monitoring": {
      "prometheus": true,
      "custom_metrics": ["request_count", "processing_time"]
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Template Creation Fails**
   ```bash
   # Check template directory permissions
   ls -la templates/

   # Validate JSON syntax
   python -m json.tool templates/my-template/template.json

   # Check for required fields
   mcp-template validate my-template --verbose
   ```

2. **Docker Build Issues**
   ```bash
   # Build manually to see detailed errors
   cd templates/my-template
   docker build --no-cache -t my-template .

   # Check Dockerfile syntax
   docker build --help
   ```

3. **Configuration Problems**
   ```bash
   # Test configuration parsing
   mcp-template config my-template --test-env

   # Check environment variable mapping
   export MCP_DEBUG=true
   mcp-template deploy my-template --config debug=true
   ```

### Debug Mode

```bash
# Enable comprehensive debugging
export MCP_LOG_LEVEL=DEBUG
export MCP_DEBUG_TEMPLATE=true

# Deploy with debug options
mcp-template deploy my-template \
  --config debug=true \
  --config log_level=DEBUG \
  --verbose
```

## Getting Help

### Community Support

- **Documentation**: [Template documentation](index.md)
- **GitHub Issues**: [Report problems](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Discord Community**: [Join discussions](https://discord.gg/55Cfxe9gnr)

### Professional Services

- **Custom Template Development**: We build templates for your specific needs
- **Enterprise Support**: Commercial support with SLA
- **Training & Consulting**: Template development workshops
- **Contact**: [support@dataeverything.ai](mailto:support@dataeverything.ai)

---

**Next Steps:**
- [Deploy your custom template](../cli/deploy.md)
- [Test with integration examples](../examples/integrations.md)
- [Learn about advanced configuration](../user-guide/configuration.md)
- [Contribute to the template registry](../guides/contributing.md)
