# Template Development Guide

Complete guide for creating, testing, and deploying MCP server templates with the comprehensive configuration system.

## 🎯 Overview

MCP Server Templates provide a standardized way to create Model Context Protocol servers with:
- **Generic Configuration System**: Automatic mapping from nested JSON/YAML to environment variables
- **Multi-Source Configuration**: Template defaults → Config files → CLI options → Environment variables
- **Type Conversion**: Schema-based automatic type conversion
- **Deployment Flexibility**: Support for Docker, Kubernetes, and Mock backends
- **Integrated Testing**: Comprehensive test framework with CI/CD integration

## 🔧 Configuration System Features

### Generic Configuration Mapping
The system automatically maps configuration from various sources:

```python
# Config file: {"security": {"readOnly": true}}
# Automatically maps to: MCP_READ_ONLY=true

# Config file: {"logging": {"level": "debug"}}
# Automatically maps to: MCP_LOG_LEVEL=debug

# CLI: --config read_only_mode=true
# Maps to: MCP_READ_ONLY=true

# CLI: --config security__read_only=true (nested notation)
# Maps to: MCP_READ_ONLY=true
```

### Nested Configuration Support
The CLI supports nested configuration using double underscore (`__`) notation:

```bash
# These are equivalent:
--config read_only_mode=true
--config security__read_only=true

# Both map to the same environment variable: MCP_READ_ONLY=true
```

### Configuration Precedence (Highest to Lowest)
1. **Environment Variables** (`--env MCP_READ_ONLY=true`)
2. **CLI Options** (`--config read_only_mode=true`)
3. **Config Files** (`--config-file config.json`)
4. **Template Defaults** (from `template.json`)

### Common Pattern Recognition
The system recognizes common configuration patterns across templates:
- `log_level` → `logging.level`, `log.level`
- `read_only_mode` → `security.readOnly`, `security.readonly`
- `max_file_size` → `security.maxFileSize`, `limits.maxFileSize`
- `allowed_directories` → `security.allowedDirs`, `paths.allowed`

## 🚀 Step-by-Step Tutorial

### Step 1: Create Template Structure

```bash
# Interactive template creation
python -m mcp_template create my-template

# Create with specific options
python -m mcp_template create my-template \
  --name "My Custom Server" \
  --description "Custom MCP server with special features" \
  --author "Your Name"
```

This creates the following structure:

```
templates/my-template/
├── template.json          # Template metadata and config schema
├── Dockerfile            # Container definition
├── README.md             # Usage instructions
├── USAGE.md              # Detailed usage examples
├── src/                  # Source code
│   ├── __init__.py
│   ├── server.py         # Main MCP server implementation
│   ├── tools.py          # MCP tools implementation
│   └── config.py         # Configuration handling
├── config/               # Configuration examples
│   ├── server.json       # Default configuration
│   └── production.json   # Production configuration
├── docs/                 # Documentation
│   └── index.md          # Template documentation
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_server.py    # Server tests
│   ├── test_tools.py     # Tool tests
│   └── test_config.py    # Configuration tests
└── requirements.txt      # Python dependencies
```

### Step 2: Define Your Configuration Schema

Create a comprehensive `template.json` with configuration schema:

```json
{
  "id": "my-template",
  "name": "My Custom MCP Server",
  "description": "A custom MCP server with advanced features",
  "version": "1.0.0",
  "author": "Your Name",
  "docker_image": "dataeverything/mcp-my-template",
  "docker_tag": "latest",
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "title": "API Key",
        "description": "API key for external service authentication",
        "env_mapping": "MCP_API_KEY",
        "secret": true
      },
      "timeout": {
        "type": "integer",
        "title": "Request Timeout",
        "description": "Timeout in seconds",
        "env_mapping": "MCP_TIMEOUT",
        "default": 30,
        "minimum": 5,
        "maximum": 300
      },
      "features": {
        "type": "array",
        "title": "Enabled Features",
        "description": "List of features to enable",
        "env_mapping": "MCP_FEATURES",
        "env_separator": ",",
        "items": {
          "type": "string",
          "enum": ["feature1", "feature2", "feature3"]
        },
        "default": ["feature1"]
      },
      "advanced_config": {
        "type": "object",
        "title": "Advanced Configuration",
        "description": "Complex nested configuration",
        "env_mapping": "MCP_ADVANCED",
        "env_separator": "__",
        "properties": {
          "cache_size": {
            "type": "integer",
            "env_mapping": "MCP_ADVANCED__CACHE_SIZE",
            "default": 100
          },
          "retry_policy": {
            "type": "object",
            "env_mapping": "MCP_ADVANCED__RETRY",
            "env_separator": "_",
            "properties": {
              "max_attempts": {
                "type": "integer",
                "env_mapping": "MCP_ADVANCED__RETRY_MAX_ATTEMPTS",
                "default": 3
              }
            }
          }
        }
      }
    },
    "required": ["api_key"]
  },
  "health_check": {
    "path": "/health",
    "interval": "30s",
    "timeout": "10s"
  },
  "capabilities": [
    {
      "name": "my_tool",
      "description": "Custom tool functionality",
      "example": "Perform custom operation",
      "example_args": {
        "param1": "value1",
        "param2": 42
      },
      "example_response": "Operation completed successfully"
    }
  ],
  "tools": [
    {
      "name": "my_tool",
      "description": "Performs a custom operation",
      "parameters": [
        {
          "name": "param1",
          "description": "First parameter",
          "type": "string",
          "required": true
        },
        {
          "name": "param2",
          "description": "Second parameter",
          "type": "integer",
          "required": false,
          "default": 0
        }
      ]
    }
  ],
  "volumes": {
    "/data": "/app/data",
    "/logs": "/app/logs"
  },
  "env_vars": {
    "MCP_PORT": "8080",
    "MCP_HOST": "0.0.0.0"
  },
  "example_config": "{\"mcpServers\":{\"my-template\":{\"command\":\"docker\",\"args\":[\"exec\",\"-i\",\"mcp-my-template\",\"python\",\"-m\",\"src.server\"]}}}"
}
```

### Step 3: Implement Your MCP Server

Create the main server implementation in `src/server.py`:

```python
#!/usr/bin/env python3
"""
My Custom MCP Server
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import Tool
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyMCPServer:
    def __init__(self):
        self.server = Server("my-template")
        self.config = self._load_config()
        self._setup_tools()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "api_key": os.getenv("MCP_API_KEY"),
            "timeout": int(os.getenv("MCP_TIMEOUT", "30")),
            "features": os.getenv("MCP_FEATURES", "feature1").split(","),
            "cache_size": int(os.getenv("MCP_ADVANCED__CACHE_SIZE", "100")),
        }

    def _setup_tools(self):
        """Setup MCP tools."""
        @self.server.tool()
        async def my_tool(param1: str, param2: int = 0) -> str:
            """Performs a custom operation."""
            logger.info(f"Executing my_tool with param1={param1}, param2={param2}")

            # Your custom logic here
            result = f"Processed {param1} with value {param2}"

            return result

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting My Custom MCP Server")
        logger.info(f"Configuration: {self.config}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point."""
    server = MyMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Create Platform Integration Layer

#### Platform Wrapper (`src/platform-wrapper.js`)

For advanced platform integration, create a wrapper that handles configuration parsing:

```javascript
#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');
const yaml = require('js-yaml');

class MCPPlatformWrapper {
    constructor() {
        this.config = this.loadConfiguration();
    }

    loadConfiguration() {
        const config = {};

        // Parse environment variables with nested structure
        this.parseNestedEnvVars(config, 'MCP_ADVANCED', process.env, '__');

        // Merge with config file if present
        const configFile = '/app/config/config.yaml';
        if (fs.existsSync(configFile)) {
            try {
                const fileConfig = yaml.load(fs.readFileSync(configFile, 'utf8'));
                this.deepMerge(config, fileConfig);
            } catch (error) {
                console.error('Error loading config file:', error);
            }
        }

        this.config = config;
        return config;
    }

    parseNestedEnvVars(config, prefix, env, separator) {
        Object.keys(env).forEach(key => {
            if (key.startsWith(prefix + separator)) {
                const parts = key.substring(prefix.length + separator.length).split(separator);
                let current = config;

                // Navigate/create nested structure
                for (let i = 0; i < parts.length - 1; i++) {
                    const part = parts[i].toLowerCase();
                    if (!current[part]) current[part] = {};
                    current = current[part];
                }

                // Set the value
                const finalKey = parts[parts.length - 1].toLowerCase();
                current[finalKey] = this.convertValue(env[key]);
            }
        });
    }

    convertValue(value) {
        // Try to convert to appropriate type
        if (value === 'true') return true;
        if (value === 'false') return false;
        if (!isNaN(value) && !isNaN(parseFloat(value))) return parseFloat(value);
        if (value.includes(',')) return value.split(',');
        return value;
    }

    deepMerge(target, source) {
        Object.keys(source).forEach(key => {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                if (!target[key] || typeof target[key] !== 'object') target[key] = {};
                this.deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        });
    }

    async start() {
        console.log('🚀 Starting MCP Server with configuration:');
        console.log(JSON.stringify(this.config, null, 2));

        const pythonProcess = spawn('python', ['-m', 'src.server'], {
            stdio: 'inherit',
            env: {
                ...process.env,
                MCP_CONFIG: JSON.stringify(this.config)
            }
        });

        pythonProcess.on('close', (code) => {
            console.log(`MCP Server exited with code ${code}`);
            process.exit(code);
        });
    }
}

if (require.main === module) {
    const wrapper = new MCPPlatformWrapper();
    wrapper.start().catch(console.error);
}

module.exports = MCPPlatformWrapper;
```

### Step 5: Create Comprehensive Tests

#### Unit Tests (`tests/test_server.py`)

```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.server import MyMCPServer

class TestMyMCPServer:
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        with patch.dict('os.environ', {
            'MCP_API_KEY': 'test-key',
            'MCP_TIMEOUT': '60',
            'MCP_FEATURES': 'feature1,feature2'
        }):
            return MyMCPServer()

    def test_config_loading(self, server):
        """Test configuration loading from environment."""
        assert server.config['api_key'] == 'test-key'
        assert server.config['timeout'] == 60
        assert server.config['features'] == ['feature1', 'feature2']

    @pytest.mark.asyncio
    async def test_my_tool(self, server):
        """Test the custom tool."""
        # This would test the actual tool implementation
        # You'll need to mock the MCP server framework
        pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_startup(self, server):
        """Test server can start up successfully."""
        # Integration test for server startup
        pass
```

#### Configuration Tests (`tests/test_config.py`)

```python
import pytest
import os
from src.config import ConfigManager

class TestConfigManager:
    def test_nested_env_var_parsing(self):
        """Test parsing of nested environment variables."""
        with patch.dict(os.environ, {
            'MCP_ADVANCED__CACHE_SIZE': '200',
            'MCP_ADVANCED__RETRY_MAX_ATTEMPTS': '5'
        }):
            config = ConfigManager.load_from_env()
            assert config['advanced']['cache_size'] == 200
            assert config['advanced']['retry']['max_attempts'] == 5

    def test_config_file_loading(self):
        """Test loading configuration from files."""
        # Test JSON and YAML config file loading
        pass
```

### Step 6: Create Docker Configuration

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY config/ config/

# Create non-root user
RUN addgroup --gid 1001 --system mcp && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group mcp

# Set ownership and permissions
RUN chown -R mcp:mcp /app
USER mcp

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Labels for metadata
LABEL mcp.template-id="my-template"
LABEL mcp.template-version="1.0.0"
LABEL mcp.server-type="python-native"

# Run the server
CMD ["python", "-m", "src.server"]
```

### Step 7: Testing and Validation

#### Template Testing Workflow

The system includes comprehensive testing that validates:

1. **Unit Tests**: Fast tests without external dependencies
2. **Integration Tests**: Tests with MCP client simulation
3. **Coverage Check**: Ensures 80%+ test coverage
4. **Configuration Validation**: Validates template.json and docs
5. **Server Startup Test**: Ensures server can start without errors
6. **Docker Build Test**: Validates Dockerfile builds successfully

#### Local Testing

```bash
# Test your template locally
cd templates/my-template

# Run unit tests
pytest tests/ -v

# Test with different configurations
python -m mcp_template deploy my-template --config api_key=test-key

# Test Docker build
docker build -t my-template .
docker run -it --rm my-template

# Test configuration options
python -m mcp_template deploy my-template --show-config
```

#### CI/CD Integration

Templates are automatically tested when:
- Changes are pushed to template directories
- Pull requests are created
- Manual dispatch is triggered

Only templates that pass all tests get built and pushed to Docker Hub.

## 🏗️ Template Requirements

For a template to be valid and deployable:

- ✅ `template.json` with required fields and valid schema
- ✅ `Dockerfile` that builds successfully
- ✅ `docs/index.md` documentation
- ✅ `src/server.py` or equivalent main server file
- ✅ Tests that pass (if `tests/` directory exists)
- ✅ Valid MCP server that starts without errors
- ✅ Configuration schema matches implementation

## 🔧 Best Practices

### Configuration Design

1. **Environment Variables First**: Support env vars for all settings
2. **Sensible Defaults**: Provide good defaults for optional settings
3. **Validation**: Validate configuration on startup
4. **Documentation**: Document all configuration options clearly

### Security

1. **Secrets Management**: Mark sensitive fields with `"secret": true`
2. **Input Validation**: Validate all user inputs
3. **Principle of Least Privilege**: Run as non-root user
4. **Error Handling**: Don't leak sensitive information in errors

### Performance

1. **Resource Limits**: Set appropriate memory/CPU limits
2. **Caching**: Implement caching where appropriate
3. **Connection Pooling**: Reuse connections to external services
4. **Graceful Shutdown**: Handle SIGTERM properly

### Observability

1. **Health Checks**: Implement meaningful health checks
2. **Logging**: Use structured logging with appropriate levels
3. **Metrics**: Consider adding metrics for monitoring
4. **Error Handling**: Provide useful error messages

## 📚 Additional Resources

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Template Testing Guide](testing.md)
- [Architecture Overview](../development/architecture.md)

## 🤝 Getting Help

- **GitHub Issues**: [Bug reports and feature requests](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Discussions**: [Community questions](https://github.com/Data-Everything/mcp-server-templates/discussions)
- **Commercial Support**: [tooling@dataeverything.ai](mailto:tooling@dataeverything.ai)
