# create

**Create new MCP server templates with interactive guidance, configuration schemas, and best practices.**

## Synopsis

```bash
python -m mcp_template create [TEMPLATE_ID] [OPTIONS]
```

## Description

The `create` command provides a comprehensive template creation workflow that guides you through building custom MCP server templates. It supports both interactive and non-interactive modes, generates boilerplate code, creates configuration schemas, and ensures best practices compliance.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE_ID` | Unique identifier for the template (optional, will prompt if not provided) |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config-file PATH` | Path to template configuration file | Interactive prompts |
| `--non-interactive` | Run in non-interactive mode (requires config file) | Interactive mode |
| `--from-image IMAGE` | Create template from existing Docker image | Fresh template |
| `--from-discovery PATH` | Create template from tool discovery results | Fresh template |

## Interactive Template Creation

### Basic Interactive Flow

```bash
# Start interactive template creation
python -m mcp_template create

# Example interactive session:
╭─────────────────────────────────────────────────────────────╮
│              🛠️  MCP Template Creator                       │
╰─────────────────────────────────────────────────────────────╯

📝 Template Information:
Template ID (e.g., 'my-api-server'): custom-server
Template Name: Custom API Server
Description: Integration server for external APIs
Version [1.0.0]: 1.0.0
Author: Your Name
Category [general]: api
Tags (comma-separated): rest,api,integration

🐳 Docker Configuration:
Base image [python:3.11-slim]: python:3.11-slim
Docker registry [dataeverything]: myregistry
Expose port [8080]: 8080

🔧 MCP Configuration:
Default transport [stdio]: stdio
Supported transports: stdio,http
HTTP port (if http enabled) [8080]: 8080

📋 Tools Configuration:
Add tools interactively? [y/N]: y
Tool name: get_data
Tool description: Retrieve data from external API
Add parameters? [y/N]: y
Parameter name: endpoint
Parameter type [string]: string
Parameter required [y/N]: y
Add another parameter? [y/N]: n
Add another tool? [y/N]: n

⚙️  Configuration Schema:
Add configuration options? [y/N]: y
Config option: api_base_url
Type [string]: string
Description: Base URL for the API
Default value: https://api.example.com
Required [y/N]: y
Environment variable mapping: API_BASE_URL
Add another option? [y/N]: y

Config option: api_token
Type [string]: string
Description: Authentication token
Required [y/N]: y
Environment variable mapping: API_TOKEN
Add another option? [y/N]: n

✅ Template created successfully at: templates/custom-server/
📁 Generated files:
  - template.json (template configuration)
  - Dockerfile (container definition)
  - src/server.py (MCP server implementation)
  - src/tools.py (tool implementations)
  - requirements.txt (Python dependencies)
  - README.md (documentation)
  - config/schema.json (configuration schema)

🚀 Next steps:
  1. Implement your tools in src/tools.py
  2. Test: python -m mcp_template deploy custom-server
  3. Verify: python -m mcp_template tools custom-server
```

### Specify Template ID

```bash
# Create with specific template ID
python -m mcp_template create my-database-server

# Skips the template ID prompt and uses 'my-database-server'
```

## Non-Interactive Creation

### Using Configuration File

```bash
# Create from configuration file
python -m mcp_template create --config-file template-config.json --non-interactive

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
  "mcp": {
    "default_transport": "stdio",
    "supported_transports": ["stdio", "http"],
    "http_port": 8080
  },
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "parameters": {
        "location": {
          "type": "string",
          "required": true,
          "description": "City name or coordinates"
        },
        "units": {
          "type": "string",
          "required": false,
          "default": "metric",
          "enum": ["metric", "imperial", "kelvin"]
        }
      }
    },
    {
      "name": "get_forecast",
      "description": "Get weather forecast",
      "parameters": {
        "location": {"type": "string", "required": true},
        "days": {"type": "integer", "required": false, "default": 5}
      }
    }
  ],
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "Weather API key",
      "required": true,
      "env_mapping": "WEATHER_API_KEY"
    },
    "base_url": {
      "type": "string",
      "description": "Weather API base URL",
      "default": "https://api.openweathermap.org/data/2.5",
      "required": false,
      "env_mapping": "WEATHER_BASE_URL"
    },
    "timeout": {
      "type": "integer",
      "description": "Request timeout in seconds",
      "default": 30,
      "required": false
    }
  }
}
```

### From Existing Docker Image

```bash
# Create template from existing MCP-compatible image
python -m mcp_template create --from-image mcp/filesystem my-file-server

# Automatically discovers tools and generates template
# Example output:
╭─────────────────────────────────────────────────────────────╮
│         🔍 Analyzing Docker Image: mcp/filesystem          │
╰─────────────────────────────────────────────────────────────╯

✅ Discovered 11 tools via MCP protocol
✅ Generated configuration schema from analysis
✅ Created template structure

📁 Template created: templates/my-file-server/
🛠️  Discovered tools:
  - read_file: Read complete file contents
  - write_file: Create or overwrite files
  - list_directory: List directory contents
  - create_directory: Create directories
  - ... and 7 more

🎯 Ready for customization and deployment
```

### From Tool Discovery Results

```bash
# First, discover tools from an image
python -m mcp_template tools --image custom/mcp-server:latest > discovery.json

# Then create template from discovery
python -m mcp_template create --from-discovery discovery.json custom-template

# Uses discovered tool information to generate template
```

## Generated Template Structure

The create command generates a complete template structure:

```
templates/my-template/
├── template.json          # Template configuration and metadata
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── README.md            # Template documentation
├── src/
│   ├── __init__.py      # Package initialization
│   ├── server.py        # Main MCP server implementation
│   ├── tools.py         # Tool implementations
│   └── config.py        # Configuration management
├── config/
│   ├── schema.json      # Configuration schema
│   └── examples/        # Example configurations
│       ├── basic.json   # Basic configuration example
│       ├── advanced.json # Advanced configuration example
│       └── production.json # Production configuration
├── tests/
│   ├── __init__.py      # Test package
│   ├── test_server.py   # Server tests
│   ├── test_tools.py    # Tool tests
│   └── test_config.py   # Configuration tests
└── docs/
    ├── README.md        # Detailed documentation
    ├── tools.md         # Tool documentation
    └── examples.md      # Usage examples
```

## Template Configuration Schema

### template.json Structure

```json
{
  "id": "my-template",
  "name": "My Custom Template",
  "description": "Description of what this template does",
  "version": "1.0.0",
  "author": "Your Name",
  "category": "api",
  "tags": ["rest", "api", "custom"],
  "docker": {
    "image": "myregistry/my-template",
    "tag": "latest",
    "base_image": "python:3.11-slim",
    "port": 8080,
    "volumes": [
      {"host": "./data", "container": "/app/data"},
      {"host": "./config", "container": "/app/config"}
    ],
    "environment": {
      "PYTHONPATH": "/app/src"
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
      "name": "example_tool",
      "description": "Example tool description",
      "category": "general",
      "parameters": {
        "type": "object",
        "properties": {
          "input": {
            "type": "string",
            "description": "Input parameter"
          }
        },
        "required": ["input"]
      }
    }
  ],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API authentication key",
        "env_mapping": "API_KEY"
      },
      "debug": {
        "type": "boolean",
        "description": "Enable debug mode",
        "default": false,
        "env_mapping": "DEBUG"
      }
    },
    "required": ["api_key"]
  }
}
```

## Generated Code Examples

### Server Implementation (src/server.py)

```python
#!/usr/bin/env python3
"""
My Custom Template MCP Server

Generated by MCP Template Creator
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.tools import tool

from .config import load_config
from .tools import ExampleTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("My Custom Template")

class MyTemplateServer:
    """My Custom Template MCP Server"""

    def __init__(self):
        self.config = load_config()
        self.tools = ExampleTools(self.config)
        self._register_tools()

    def _register_tools(self):
        """Register all available tools"""

        @tool("example_tool")
        async def example_tool(input: str) -> Dict[str, Any]:
            """Example tool description"""
            return await self.tools.example_tool(input)

        logger.info("Registered tools: example_tool")

async def main():
    """Main server entry point"""
    server = MyTemplateServer()
    logger.info("My Custom Template server starting...")
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Tool Implementation (src/tools.py)

```python
"""
Tool implementations for My Custom Template
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ExampleTools:
    """Example tool implementations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def example_tool(self, input: str) -> Dict[str, Any]:
        """
        Example tool implementation

        Args:
            input: Input parameter

        Returns:
            Dict containing tool result
        """
        try:
            # TODO: Implement your tool logic here
            result = f"Processed input: {input}"

            logger.info(f"Tool executed: example_tool(input='{input}')")

            return {
                "success": True,
                "result": result,
                "input": input
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "input": input
            }
```

## Testing Created Templates

### Immediate Testing

```bash
# Test template creation
python -m mcp_template create test-template

# Deploy for testing
python -m mcp_template deploy test-template

# Verify tools are discovered
python -m mcp_template tools test-template

# Test with configuration
python -m mcp_template deploy test-template --config debug=true
```

### Development Workflow

```bash
# Edit template files
vim templates/test-template/src/tools.py

# Redeploy with changes
python -m mcp_template deploy test-template --no-pull

# Test specific tool
python -m mcp_template connect test-template --llm python
```

## Best Practices

### Template Design

1. **Clear Naming**: Use descriptive template IDs and tool names
2. **Comprehensive Schemas**: Define complete configuration schemas
3. **Error Handling**: Implement robust error handling in tools
4. **Documentation**: Include detailed README and tool documentation
5. **Testing**: Add comprehensive tests for all functionality

### Security Considerations

```bash
# Create template with security focus
python -m mcp_template create secure-api \
  --config-file secure-template-config.json

# Include security-focused configuration:
{
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "API key (keep secure)",
      "env_mapping": "API_KEY",
      "sensitive": true
    },
    "rate_limit": {
      "type": "integer",
      "description": "Rate limit per minute",
      "default": 60
    },
    "allowed_origins": {
      "type": "array",
      "description": "Allowed CORS origins",
      "default": []
    }
  }
}
```

## See Also

- [deploy](deploy.md) - Deploy created templates
- [tools](tools.md) - Discover tools from created templates
- [config](config.md) - View configuration options
- [Template Development Guide](../guides/creating-templates.md) - Advanced template development
