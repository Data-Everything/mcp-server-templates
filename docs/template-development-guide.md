# Template Development Guide

This guide walks you through creating new MCP server templates with the comprehensive configuration system and deployment support.

## 🎯 Overview

MCP Server Templates provide a standardized way to create Model Context Protocol servers with:
- **Generic Configuration System**: Automatic mapping from nested JSON/YAML to environment variables
- **Multi-Source Configuration**: Template defaults → Config files → CLI options → Environment variables
- **Type Conversion**: Schema-based automatic type conversion
- **Deployment Flexibility**: Support for Docker, Kubernetes, and Mock backends

## 🔧 New Configuration System Features

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

## 🏗️ Architecture

### Template Structure

```
templates/your-template/
├── README.md                 # Template documentation
├── template.json            # Configuration schema & metadata
├── Dockerfile              # Container definition
├── docker-compose.yml      # Local development setup
├── requirements.txt        # Python dependencies (if needed)
├── package.json           # Node.js dependencies (if needed)
├── src/                   # Source code
│   ├── server.py         # Main MCP server implementation
│   ├── server.js         # Alternative: Node.js implementation
│   ├── platform-wrapper.js  # Environment integration layer
│   └── tools.py          # MCP tools implementation
├── config/               # Configuration examples
│   ├── config.yaml.example
│   └── advanced.yaml.example
└── tests/                # Template-specific tests
    ├── test_server.py
    └── test_integration.py
```

### Configuration Flow

```
User Input (Web UI) → template.json schema → Environment Variables → Container → MCP Server
```

## 🚀 Step-by-Step Tutorial

### Step 1: Choose Your Template Type

Start by copying the base template:

```bash
cp -r templates/base templates/my-new-template
cd templates/my-new-template
```

### Step 2: Define Your Configuration Schema

Edit `template.json` to define what settings your template needs:

```json
{
  "name": "My New Template",
  "description": "Brief description of what this template does",
  "version": "1.0.0",
  "author": "Your Name <your.email@domain.com>",
  "docker_image": "data-everything/mcp-my-new-template",
  "categories": ["productivity", "development"],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "title": "API Key",
        "description": "Your service API key",
        "env_mapping": "MCP_API_KEY",
        "secret": true
      },
      "base_url": {
        "type": "string",
        "title": "Base URL",
        "description": "Service base URL",
        "env_mapping": "MCP_BASE_URL",
        "default": "https://api.service.com"
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
  }
}
```

### Step 3: Implement Your MCP Server

#### Python Implementation (`src/server.py`)

```python
import asyncio
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyTemplateServer:
    def __init__(self, config: dict):
        self.config = config
        self.server = Server("my-template-server")
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="my://resource/1",
                    name="Example Resource",
                    description="An example resource",
                    mimeType="text/plain"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource."""
            if uri == "my://resource/1":
                return "This is example resource content"
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="my_tool",
                    description="An example tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to process"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls."""
            if name == "my_tool":
                query = arguments.get("query", "")
                result = await self.process_query(query)
                return [types.TextContent(type="text", text=result)]
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def process_query(self, query: str) -> str:
        """Process a query using your service."""
        # Implement your logic here
        api_key = self.config.get('api_key')
        base_url = self.config.get('base_url')
        timeout = self.config.get('timeout', 30)

        # Example API call logic
        return f"Processed query '{query}' with config: {self.config}"

    async def run(self):
        """Run the server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="my-template-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

def load_config() -> dict:
    """Load configuration from environment variables and config files."""
    import os
    import yaml

    config = {}

    # Load from environment variables
    config['api_key'] = os.getenv('MCP_API_KEY')
    config['base_url'] = os.getenv('MCP_BASE_URL', 'https://api.service.com')
    config['timeout'] = int(os.getenv('MCP_TIMEOUT', '30'))

    # Parse array from environment
    features_str = os.getenv('MCP_FEATURES', 'feature1')
    config['features'] = [f.strip() for f in features_str.split(',')]

    # Parse nested config
    config['advanced_config'] = {
        'cache_size': int(os.getenv('MCP_ADVANCED__CACHE_SIZE', '100')),
        'retry_policy': {
            'max_attempts': int(os.getenv('MCP_ADVANCED__RETRY_MAX_ATTEMPTS', '3'))
        }
    }

    # Merge with config file if present
    config_file = '/app/config/config.yaml'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = yaml.safe_load(f)
            config.update(file_config)

    return config

async def main():
    """Main entry point."""
    config = load_config()
    server = MyTemplateServer(config)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Create Platform Integration Layer

#### Platform Wrapper (`src/platform-wrapper.js`)

```javascript
const fs = require('fs');
const yaml = require('js-yaml');
const { spawn } = require('child_process');

class PlatformWrapper {
    constructor() {
        this.config = null;
        this.serverProcess = null;
    }

    async loadConfiguration() {
        const config = {};

        // Parse environment variables based on template.json schema
        if (process.env.MCP_API_KEY) {
            config.api_key = process.env.MCP_API_KEY;
        }

        if (process.env.MCP_BASE_URL) {
            config.base_url = process.env.MCP_BASE_URL;
        }

        if (process.env.MCP_TIMEOUT) {
            config.timeout = parseInt(process.env.MCP_TIMEOUT);
        }

        // Parse array values
        if (process.env.MCP_FEATURES) {
            config.features = process.env.MCP_FEATURES.split(',').map(s => s.trim());
        }

        // Parse nested configuration with separators
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

                // Set the final value
                const finalKey = parts[parts.length - 1].toLowerCase();
                current[finalKey] = this.parseEnvValue(env[key]);
            }
        });
    }

    parseEnvValue(value) {
        // Try to parse as number
        if (/^\d+$/.test(value)) {
            return parseInt(value);
        }

        // Try to parse as boolean
        if (value.toLowerCase() === 'true') return true;
        if (value.toLowerCase() === 'false') return false;

        // Return as string
        return value;
    }

    deepMerge(target, source) {
        Object.keys(source).forEach(key => {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                if (!target[key]) target[key] = {};
                this.deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        });
    }

    async startServer() {
        await this.loadConfiguration();

        console.log('Starting MCP server with configuration:', JSON.stringify(this.config, null, 2));

        // Set environment variables for the Python server
        const env = { ...process.env };
        this.setEnvFromConfig(env, this.config);

        // Start the Python MCP server
        this.serverProcess = spawn('python', ['/app/src/server.py'], {
            stdio: 'inherit',
            env: env
        });

        this.serverProcess.on('error', (error) => {
            console.error('Server process error:', error);
            process.exit(1);
        });

        this.serverProcess.on('close', (code) => {
            console.log(`Server process exited with code ${code}`);
            process.exit(code);
        });

        // Handle graceful shutdown
        process.on('SIGTERM', () => this.shutdown());
        process.on('SIGINT', () => this.shutdown());
    }

    setEnvFromConfig(env, config, prefix = 'MCP') {
        Object.keys(config).forEach(key => {
            const envKey = `${prefix}_${key.toUpperCase()}`;
            const value = config[key];

            if (Array.isArray(value)) {
                env[envKey] = value.join(',');
            } else if (typeof value === 'object' && value !== null) {
                this.setEnvFromConfig(env, value, envKey);
            } else {
                env[envKey] = String(value);
            }
        });
    }

    async shutdown() {
        console.log('Shutting down server...');
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
        }
        process.exit(0);
    }

    async healthCheck() {
        // Implement health check logic
        return { status: 'healthy', config: !!this.config };
    }
}

// Health check endpoint (if running as HTTP server)
const express = require('express');
const app = express();

const wrapper = new PlatformWrapper();

app.get('/health', async (req, res) => {
    try {
        const health = await wrapper.healthCheck();
        res.json(health);
    } catch (error) {
        res.status(500).json({ status: 'unhealthy', error: error.message });
    }
});

// Start the server
if (require.main === module) {
    wrapper.startServer().catch(error => {
        console.error('Failed to start server:', error);
        process.exit(1);
    });

    // Start health check server
    const port = process.env.HEALTH_PORT || 8000;
    app.listen(port, () => {
        console.log(`Health check server running on port ${port}`);
    });
}

module.exports = PlatformWrapper;
```

### Step 5: Create Docker Configuration

#### Dockerfile

```dockerfile
FROM node:18-alpine AS builder

# Install Python for MCP server
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Copy Python requirements
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set ownership
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8000/health', (res) => process.exit(res.statusCode === 200 ? 0 : 1))"

EXPOSE 8000

CMD ["node", "src/platform-wrapper.js"]
```

### Step 6: Add Local Development Support

#### docker-compose.yml

```yaml
version: '3.8'

services:
  my-template-dev:
    build: .
    container_name: my-template-dev
    ports:
      - "8000:8000"
    environment:
      - MCP_API_KEY=your-dev-api-key
      - MCP_BASE_URL=https://api.service.com
      - MCP_TIMEOUT=30
      - MCP_FEATURES=feature1,feature2
      - MCP_ADVANCED__CACHE_SIZE=50
      - MCP_ADVANCED__RETRY_MAX_ATTEMPTS=2
      - NODE_ENV=development
    volumes:
      # Mount source for development
      - ./src:/app/src
      - ./config:/app/config

      # Optional: mount config file
      - ./config/config.yaml.example:/app/config/config.yaml:ro
    restart: unless-stopped
```

### Step 7: Create Documentation

#### Template README.md

```markdown
# My New Template

Brief description of what this template does and its main features.

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_API_KEY` | Your service API key | - | ✅ |
| `MCP_BASE_URL` | Service base URL | `https://api.service.com` | |
| `MCP_TIMEOUT` | Request timeout (seconds) | `30` | |
| `MCP_FEATURES` | Enabled features (comma-separated) | `feature1` | |

### Advanced Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ADVANCED__CACHE_SIZE` | Cache size | `100` |
| `MCP_ADVANCED__RETRY_MAX_ATTEMPTS` | Max retry attempts | `3` |

### Config File (Optional)

Mount a YAML file at `/app/config/config.yaml`:

```yaml
api_key: "your-api-key"
base_url: "https://api.service.com"
timeout: 30
features:
  - feature1
  - feature2
advanced_config:
  cache_size: 100
  retry_policy:
    max_attempts: 3
```

## Usage Examples

### Docker

```bash
docker run -d \
  --name my-template \
  --env=MCP_API_KEY=your-api-key \
  --env=MCP_FEATURES=feature1,feature2 \
  -p 8000:8000 \
  data-everything/mcp-my-new-template:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  my-template:
    image: data-everything/mcp-my-new-template:latest
    environment:
      - MCP_API_KEY=your-api-key
      - MCP_BASE_URL=https://api.service.com
      - MCP_FEATURES=feature1,feature2
    ports:
      - "8000:8000"
```

## Development

### Local Testing

```bash
# Build the image
docker build -t my-template-local .

# Run with development config
docker-compose up
```

### Running Tests

```bash
# Run template tests
python -m pytest tests/

# Integration tests
python -m pytest tests/test_integration.py
```

## Troubleshooting

### Common Issues

**Issue**: Server fails to start
- **Solution**: Check that all required environment variables are set

**Issue**: API authentication errors
- **Solution**: Verify your API key is correct and has necessary permissions

## Support

- [Documentation](../../docs/)
- [Issues](https://github.com/data-everything/mcp-server-templates/issues)
- [Discussions](https://github.com/data-everything/mcp-server-templates/discussions)
```

### Step 8: Testing Your Template

Create comprehensive tests in the `tests/` directory:

```python
# tests/test_server.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import MyTemplateServer, load_config

class TestMyTemplateServer:
    @pytest.fixture
    def config(self):
        return {
            'api_key': 'test-key',
            'base_url': 'https://test.api.com',
            'timeout': 30,
            'features': ['feature1'],
            'advanced_config': {
                'cache_size': 100,
                'retry_policy': {'max_attempts': 3}
            }
        }

    @pytest.fixture
    def server(self, config):
        return MyTemplateServer(config)

    def test_server_initialization(self, server, config):
        assert server.config == config
        assert server.server is not None

    @pytest.mark.asyncio
    async def test_process_query(self, server):
        result = await server.process_query("test query")
        assert "test query" in result
        assert server.config['api_key'] in result

@patch.dict(os.environ, {
    'MCP_API_KEY': 'env-key',
    'MCP_BASE_URL': 'https://env.api.com',
    'MCP_TIMEOUT': '60',
    'MCP_FEATURES': 'feature1,feature2',
    'MCP_ADVANCED__CACHE_SIZE': '200'
})
def test_load_config_from_env():
    config = load_config()

    assert config['api_key'] == 'env-key'
    assert config['base_url'] == 'https://env.api.com'
    assert config['timeout'] == 60
    assert config['features'] == ['feature1', 'feature2']
    assert config['advanced_config']['cache_size'] == 200
```

### Step 9: Build and Test Locally

```bash
# Build your template
./scripts/build-template.sh my-new-template

# Test with basic config
docker run --rm \
  --env=MCP_API_KEY=test-key \
  --env=MCP_FEATURES=feature1,feature2 \
  -p 8000:8000 \
  data-everything/mcp-my-new-template:latest

# Test health check
curl http://localhost:8000/health

# Test with config file
docker run --rm \
  --volume=$(pwd)/templates/my-new-template/config:/app/config \
  -p 8000:8000 \
  data-everything/mcp-my-new-template:latest
```

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

- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Template Examples](../templates/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## 🤝 Getting Help

- Check existing templates for reference implementations
- Read the MCP protocol documentation
- Ask questions in GitHub Discussions
- Submit issues for bugs or feature requests

Happy template building! 🚀
