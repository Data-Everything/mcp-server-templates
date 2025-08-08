# Development Setup

Set up your development environment for MCP Templates and learn advanced template.json configuration for creating custom templates.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- Make (optional, for convenience commands)

## Clone Repository

```bash
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates
```

## Development Installation

### Option 1: Using Make (Recommended)

```bash
# Complete development setup
make dev-setup
```

This command will:
- Install all dependencies
- Install in development mode
- Set up the development environment

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
# OR manually:
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
make install-dev
# OR manually:
pip install -e .
```

## Developer Guide: Template.json Configuration

### Understanding MCP-Specific Properties

As a developer creating MCP templates, understanding the advanced configuration properties is crucial for building robust, secure, and user-friendly templates.

#### 1. Volume Mount Configuration (`volume_mount`)

**Use Case**: Enable secure host filesystem access for file processing, data analysis, or configuration management.

**Developer Pattern:**
```json
{
  "config_schema": {
    "properties": {
      "workspace_directory": {
        "type": "string",
        "title": "Workspace Directory",
        "description": "Local directory for processing files",
        "env_mapping": "WORKSPACE_DIR",
        "volume_mount": true
      }
    }
  }
}
```

**What Happens Behind the Scenes:**
1. User provides: `"/home/user/projects"`
2. Platform creates volume: `-v "/home/user/projects:/data/projects:rw"`
3. Container receives: `WORKSPACE_DIR="/data/projects"`

**Multiple Path Pattern:**
```json
{
  "allowed_paths": {
    "type": "string",
    "description": "Space-separated list of allowed paths",
    "env_mapping": "ALLOWED_PATHS",
    "volume_mount": true,
    "command_arg": true
  }
}
```

**Advanced Usage:**
- Input: `"/home/docs /tmp/cache /opt/data"`
- Volumes: 3 separate Docker volumes mounted
- Environment: Space-separated container paths

#### 2. Command Argument Injection (`command_arg`)

**Use Case**: Pass configuration directly to your application as command-line arguments.

**Developer Pattern:**
```json
{
  "config_file_path": {
    "type": "string",
    "title": "Configuration File",
    "description": "Path to application configuration file",
    "env_mapping": "CONFIG_FILE",
    "command_arg": true
  },
  "debug_mode": {
    "type": "boolean",
    "title": "Debug Mode",
    "description": "Enable debug logging",
    "command_arg": true,
    "default": false
  }
}
```

**Result:**
- Boolean true: `--debug-mode`
- String value: `--config-file-path=/path/to/config`

**Implementation in Your App:**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--config-file-path', type=str, help='Config file path')
parser.add_argument('--debug-mode', action='store_true', help='Enable debug mode')
args = parser.parse_args()
```

#### 3. Sensitive Data Handling (`sensitive`)

**Use Case**: API keys, passwords, tokens, certificates.

**Developer Best Practices:**
```json
{
  "api_credentials": {
    "type": "string",
    "title": "API Authentication Token",
    "description": "Bearer token for API access",
    "env_mapping": "API_TOKEN",
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

**Security Benefits:**
- Values masked in platform logs: `API_TOKEN=***`
- Configuration UI uses password fields
- Excluded from plain-text configuration exports

#### 4. Transport Configuration Best Practices

**Stdio Transport (Default):**
```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio"]
  }
}
```
- **Best for**: CLI tools, local development, direct integration
- **Implementation**: Use standard input/output for MCP communication

**HTTP Transport:**
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
- **Best for**: Web integration, REST APIs, remote access
- **Implementation**: FastAPI/Flask HTTP server with MCP endpoints

**Multi-Transport Support:**
```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http", "sse"],
    "port": 8080
  }
}
```
- **Benefits**: Flexibility for different deployment scenarios

#### 5. Environment Variable Mapping Patterns

**Simple Mapping:**
```json
{
  "log_level": {
    "type": "string",
    "env_mapping": "LOG_LEVEL",
    "default": "INFO"
  }
}
```

**Array with Custom Separator:**
```json
{
  "allowed_hosts": {
    "type": "array",
    "items": {"type": "string"},
    "env_mapping": "ALLOWED_HOSTS",
    "env_separator": ","
  }
}
```
- Result: `ALLOWED_HOSTS="host1.com,host2.com,host3.com"`

**Complex Object Handling:**
```json
{
  "redis_config": {
    "type": "object",
    "properties": {
      "host": {"type": "string", "default": "localhost"},
      "port": {"type": "integer", "default": 6379}
    },
    "env_mapping": "REDIS_CONFIG"
  }
}
```
- Result: `REDIS_CONFIG='{"host":"redis.example.com","port":6380}'`

### Template Development Patterns

#### 1. Comprehensive Configuration Template

```json
{
  "name": "Advanced MCP Template",
  "description": "Example template with all MCP properties",
  "version": "1.0.0",
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"]
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "data_directory": {
        "type": "string",
        "title": "Data Directory",
        "description": "Local directory for data files",
        "env_mapping": "DATA_DIR",
        "volume_mount": true
      },
      "config_file": {
        "type": "string",
        "title": "Config File",
        "description": "Application configuration file",
        "env_mapping": "CONFIG_FILE",
        "volume_mount": true,
        "command_arg": true
      },
      "api_key": {
        "type": "string",
        "title": "API Key",
        "description": "External service API key",
        "env_mapping": "API_KEY",
        "sensitive": true
      },
      "enable_features": {
        "type": "array",
        "title": "Enabled Features",
        "items": {"type": "string"},
        "env_mapping": "ENABLED_FEATURES",
        "env_separator": ",",
        "default": ["core", "analytics"]
      },
      "debug_mode": {
        "type": "boolean",
        "title": "Debug Mode",
        "description": "Enable detailed logging",
        "command_arg": true,
        "default": false
      }
    },
    "required": ["data_directory", "api_key"]
  }
}
```

#### 2. Implementing Configuration in Your MCP Server

**Python FastMCP Example:**
```python
import os
import json
from fastmcp import FastMCP

# Load configuration from environment variables
DATA_DIR = os.environ.get('DATA_DIR', '/tmp')
API_KEY = os.environ.get('API_KEY')
ENABLED_FEATURES = os.environ.get('ENABLED_FEATURES', '').split(',')

# Initialize MCP server
mcp = FastMCP("Advanced Template")

@mcp.tool("process_file")
async def process_file(file_path: str) -> dict:
    """Process a file from the configured data directory"""
    # Security: Ensure file is within allowed directory
    full_path = os.path.join(DATA_DIR, file_path)
    if not full_path.startswith(DATA_DIR):
        raise ValueError("File path outside allowed directory")

    # Use API_KEY for external service calls
    # Process file based on ENABLED_FEATURES
    return {"status": "processed", "file": full_path}
```

### Testing Your Templates

#### 1. Validate Configuration Schema

```bash
# Validate template.json syntax and schema
mcpt validate templates/my-template/template.json

# Test configuration processing
mcpt config my-template --show-mappings
```

#### 2. Test Volume Mount Behavior

```bash
# Deploy with volume mount configuration
mcpt deploy my-template --config data_directory="/tmp/test"

# Verify volume mounts
docker inspect mcp-my-template | grep -A 10 "Mounts"
```

#### 3. Test Environment Variable Mapping

```bash
# Check environment variables in container
mcpt shell my-template
env | grep -E "(DATA_DIR|API_KEY|ENABLED_FEATURES)"
```

### Common Development Patterns

#### Security-First Templates

```json
{
  "api_key": {"sensitive": true, "env_mapping": "API_KEY"},
  "allowed_paths": {
    "volume_mount": true,
    "env_mapping": "ALLOWED_PATHS",
    "command_arg": true
  },
  "read_only": {
    "type": "boolean",
    "env_mapping": "READ_ONLY_MODE",
    "default": true
  }
}
```

#### Performance-Optimized Templates

```json
{
  "cache_dir": {
    "volume_mount": true,
    "env_mapping": "CACHE_DIR",
    "default": "/tmp/cache"
  },
  "max_workers": {
    "type": "integer",
    "env_mapping": "MAX_WORKERS",
    "default": 4
  },
  "enable_cache": {
    "type": "boolean",
    "env_mapping": "ENABLE_CACHE",
    "default": true
  }
}
```

#### Multi-Service Integration Templates

```json
{
  "primary_api_key": {"sensitive": true, "env_mapping": "PRIMARY_API_KEY"},
  "secondary_api_key": {"sensitive": true, "env_mapping": "SECONDARY_API_KEY"},
  "service_endpoints": {
    "type": "array",
    "env_mapping": "SERVICE_ENDPOINTS",
    "env_separator": "|"
  }
}
```

## Verify Setup

```bash
# Check CLI works
mcpt --version
mcpt list

# Run quick tests
make test-quick

# Run code quality checks
make lint
```

## Development Commands

### Available Make Targets

Use `make help` to see all available commands:

```bash
make help
```

### Setup Commands

```bash
make install       # Install dependencies
make install-dev   # Install in development mode
make dev-setup     # Complete development setup
```

### Testing Commands

```bash
make test-quick        # Fast validation tests (< 30s)
make test-unit         # Unit tests (no Docker required)
make test-integration  # Integration tests (requires Docker)
make test-all         # Run all tests
make test             # Alias for test-all

# Template-specific testing
make test-template TEMPLATE=filesystem  # Test specific template
make test-templates   # Test all templates

# Test with coverage
make coverage        # Generate HTML coverage report
```

### Code Quality Commands

```bash
make lint           # Run code linting (flake8, bandit)
make format         # Format code (black, isort)
make type-check     # Run type checking (mypy)
```

### Development Workflow Commands

```bash
make dev-test       # Quick development tests (test-quick + lint)
make ci-quick       # Simulate CI quick tests
make ci-full        # Simulate full CI pipeline
```

### Template Management Commands

```bash
make list-templates     # List available templates
make validate-templates # Validate all templates
make deploy-test       # Deploy test template
make cleanup-test      # Clean up test deployments
```

### Documentation Commands

```bash
make docs          # Build documentation
make docs-serve    # Serve docs locally
make docs-clean    # Clean documentation build
```

### Build and Release Commands

```bash
make build         # Build package
make clean         # Clean build artifacts
make pre-release   # Run pre-release checks
make version       # Show package version
```

### Docker and Container Commands

```bash
make docker-check  # Check Docker availability
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit code
vim mcp_template/...

# Run development tests frequently
make dev-test
```

### 3. Test Your Changes

```bash
# Run appropriate tests
make test-quick      # For quick feedback
make test-unit       # For logic changes
make test-integration # For deployment changes
make test-template TEMPLATE=your-template # For template changes
```

### 4. Validate Code Quality

```bash
# Format code
make format

# Check code quality
make lint
make type-check
```

### 5. Test Locally

```bash
# Deploy and test your changes
make deploy-test

# Check logs
mcpt logs test-deployment

# Clean up
make cleanup-test
```

### 6. Run Full Test Suite

```bash
# Before committing, run full tests
make ci-full
```

### 7. Submit Pull Request

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Debugging

### Template Development

```bash
# Validate specific template
python -c "from mcp_template import TemplateDiscovery; d = TemplateDiscovery(); t = d.discover_templates(); print('your-template' in t)"

# Test template deployment
mcpt deploy your-template --show-config
```

### Testing Issues

```bash
# Run tests with verbose output
pytest tests/ -v

# Run specific test with debugging
pytest tests/test_deployment_units.py::test_specific_function -v -s

# Debug test failures
pytest tests/ --pdb
```

### Build Issues

```bash
# Clean everything and rebuild
make clean
make build

# Check for dependency conflicts
pip check
```

## Performance Optimization

### Development Speed

```bash
# Use quick tests during development
make test-quick

# Use unit tests for logic validation
make test-unit

# Only run integration tests when needed
make test-integration
```

### CI Simulation

```bash
# Quick CI check (< 5 minutes)
make ci-quick

# Full CI simulation (15-20 minutes)
make ci-full
```

## Troubleshooting

### Common Issues

**Docker not available:**
```bash
# Check Docker installation
make docker-check

# For testing without Docker
MOCK_CONTAINERS=true make test-unit
```

**Tests failing:**
```bash
# Check test environment
make validate-templates

# Reset development environment
make clean
make dev-setup
```

**Import errors:**
```bash
# Reinstall in development mode
make install-dev

# Check Python path
python -c "import mcp_template; print(mcp_template.__file__)"
```

**Make command not working:**
```bash
# Check if make is installed
which make

# Use direct commands instead
python -m pytest tests/
```
```

### 2. Make Changes

Edit code, add tests, update documentation.

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific tests
python -m pytest tests/test_specific.py

# Run with coverage
make coverage
```

### 4. Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make typecheck
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

## Makefile Commands

```bash
make install      # Install development dependencies
make test         # Run all tests
make coverage     # Run tests with coverage
make lint         # Run linting checks
make format       # Format code
make typecheck    # Run type checking
make docs         # Build documentation
make clean        # Clean build artifacts
```

## Environment Variables

Set these for development:

```bash
export MCP_DEBUG=true
export MCP_LOG_LEVEL=debug
export MCP_TEST_MODE=true
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Black Formatter
- Pylance
- Docker

### PyCharm

Configure:
- Python interpreter: `venv/bin/python`
- Code style: Black
- Test runner: pytest
