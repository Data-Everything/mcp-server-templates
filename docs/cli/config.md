# config

**Display comprehensive configuration options for MCP server templates with examples and usage patterns.**

## Synopsis

```bash
mcp-template config TEMPLATE [OPTIONS]
```

## Description

The `config` command displays all available configuration options for a specific template, including parameter types, default values, environment variable mappings, and usage examples. It supports multiple notation formats and provides comprehensive documentation for template customization.

## Arguments

| Argument | Description |
|----------|-------------|
| `TEMPLATE` | Name of the template to show configuration for |

## Configuration Display

The command shows configuration information in a structured table format:

### Configuration Table Columns
- **Property**: Configuration parameter name
- **Type**: Data type (string, integer, boolean, array, object)
- **CLI Options**: Various ways to set the parameter
- **Environment Variable**: Corresponding environment variable
- **Default**: Default value if not specified
- **Required**: Whether parameter is mandatory
- **Description**: Detailed explanation of the parameter

## Examples

### Basic Usage

```bash
# Show configuration for demo template
mcp-template config demo

# Example output:
╭─────────────────────────────────────────────────────────────╮
│           📋 Configuration Options for demo                 │
╰─────────────────────────────────────────────────────────────╯

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property             ┃ CLI Options                                                                        ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ hello_from           │ --config hello_from=value                                                         │
│                      │ --env MCP_HELLO_FROM=value                                                        │
│                      │ --config demo__hello_from=value                                                   │
│ debug_mode           │ --config debug_mode=true                                                          │
│                      │ --env MCP_DEBUG=true                                                              │
│                      │ --config demo__debug_mode=true                                                    │
│ port                 │ --config port=8080                                                                │
│                      │ --env MCP_PORT=8080                                                               │
│                      │ --config demo__port=8080                                                          │
└──────────────────────┴────────────────────────────────────────────────────────────────────────────────┘

💡 Usage Examples:
  # Basic configuration:
  mcp-template deploy demo --config hello_from="Custom Server" --config debug_mode=true

  # Double-underscore notation:
  mcp-template deploy demo --config demo__hello_from="Custom Server"

  # Configuration file:
  mcp-template deploy demo --config-file config.json
```

### File Server Configuration

```bash
# Show file server configuration options
mcp-template config file-server

# Example output shows comprehensive security and performance options:
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property             ┃ Type            ┃ CLI Options                                                                        ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ allowed_directories  │ array           │ --config allowed_directories='["/data","/workspace"]'                             │
│                      │                 │ --env MCP_ALLOWED_DIRS='["/data","/workspace"]'                                   │
│                      │                 │ --config file-server__security__allowed_dirs='["/data","/workspace"]'            │
│ read_only_mode       │ boolean         │ --config read_only_mode=false                                                     │
│                      │                 │ --env MCP_READ_ONLY=false                                                         │
│                      │                 │ --config file-server__security__read_only=false                                   │
│ max_file_size        │ integer         │ --config max_file_size=100                                                        │
│                      │                 │ --env MCP_MAX_FILE_SIZE=100                                                       │
│                      │                 │ --config file-server__security__max_file_size=100                                │
│ log_level            │ string          │ --config log_level=info                                                           │
│                      │                 │ --env MCP_LOG_LEVEL=info                                                          │
│                      │                 │ --config file-server__logging__level=info                                        │
└──────────────────────┴─────────────────┴────────────────────────────────────────────────────────────────────────────────┘
```

## Configuration Formats

The `config` command demonstrates three configuration notation formats:

### 1. Direct Property Names
```bash
--config property_name=value
```
Most straightforward approach using exact property names from the schema.

### 2. Environment Variable Mapping
```bash
--env MCP_PROPERTY_NAME=value
```
Uses predefined environment variable mappings defined in the template schema.

### 3. Double-Underscore Notation
```bash
--config template__section__property=value
```
Hierarchical configuration using double underscores to represent nested structure.

## Usage Examples Section

Each config display includes practical usage examples:

### Basic Examples
```bash
# Simple configuration
mcp-template deploy file-server \
  --config read_only_mode=true \
  --config max_file_size=50

# Environment variables
mcp-template deploy file-server \
  --env MCP_READ_ONLY=true \
  --env MCP_MAX_FILE_SIZE=50
```

### Advanced Examples
```bash
# Nested configuration
mcp-template deploy file-server \
  --config security__read_only=true \
  --config security__max_file_size=50 \
  --config logging__level=debug \
  --config performance__max_concurrent=20

# Mixed configuration sources
mcp-template deploy file-server \
  --config-file base-config.json \
  --config log_level=warning \
  --env MCP_READ_ONLY=true
```

### Configuration File Examples
```bash
# JSON configuration file
mcp-template deploy file-server --config-file config.json
```

## Configuration Schema Types

The command displays detailed type information:

### Basic Types
- **string**: Text values (quoted in JSON)
- **integer**: Numeric values without decimals
- **boolean**: `true` or `false` values
- **number**: Numeric values (including decimals)

### Complex Types
- **array**: List of values, shown as JSON array syntax
- **object**: Nested configuration objects
- **enum**: Fixed set of allowed values

### Type-Specific Examples
```bash
# String values
--config server_name="My MCP Server"

# Integer values
--config port=8080
--config max_connections=100

# Boolean values
--config debug_mode=true
--config read_only=false

# Array values (JSON format)
--config allowed_dirs='["/data", "/workspace", "/tmp"]'

# Object values (JSON format)
--config security='{"read_only": true, "max_file_size": 100}'
```

## Required vs Optional Parameters

The display clearly indicates which parameters are required:

### Required Parameters (✓)
Must be provided either through configuration, environment variables, or have defaults.

### Optional Parameters
Have sensible defaults and can be omitted for basic usage.

### Example with Requirements
```bash
# Template with required API key
mcp-template config api-server

# Shows:
# api_key (string) ✓ Required - API authentication key
# base_url (string) - Default: https://api.example.com
# timeout (integer) - Default: 30
```

## Environment Variable Mapping

Templates define custom environment variable mappings:

### Standard Patterns
- `MCP_PROPERTY_NAME`: Direct mapping
- `SERVICE_SPECIFIC_VAR`: Service-specific variables
- `NESTED_SECTION_PROPERTY`: Flattened nested properties

### Example Mappings
```bash
# File server mappings
MCP_ALLOWED_DIRS -> allowed_directories
MCP_READ_ONLY -> read_only_mode
MCP_LOG_LEVEL -> log_level

# Database server mappings
DB_HOST -> database.host
DB_PORT -> database.port
DB_PASSWORD -> database.password
```

## Configuration File Templates

The command provides configuration file templates:

### JSON Template
```json
{
  "security": {
    "allowed_dirs": ["/data", "/workspace"],
    "read_only": false,
    "max_file_size": 100
  },
  "logging": {
    "level": "info",
    "enable_audit": true
  },
  "performance": {
    "max_concurrent_operations": 10,
    "timeout_ms": 30000
  }
}
```

### YAML Template
```yaml
security:
  allowed_dirs:
    - "/data"
    - "/workspace"
  read_only: false
  max_file_size: 100

logging:
  level: info
  enable_audit: true

performance:
  max_concurrent_operations: 10
  timeout_ms: 30000
```

## Error Handling

### Template Not Found
```bash
❌ Template 'nonexistent' not found
Available templates: demo, file-server, postgres-server
```

### No Configuration Schema
```bash
⚠️  No configuration options available for template 'basic-template'
This template uses default settings only.
```

### Invalid Template Schema
```bash
❌ Template configuration schema is invalid
Please check template.json for syntax errors
```

## See Also

- [deploy](deploy.md) - Deploy templates with configuration
- [list](list.md) - List available templates
- [create](create.md) - Create new templates with configuration schemas
- [Template Development Guide](../guides/creating-templates.md) - Create custom configuration schemas
