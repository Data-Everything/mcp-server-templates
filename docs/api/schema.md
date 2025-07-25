# Template Schema

JSON schema definition for MCP server templates.

## template.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "name", "description", "version"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9-]*$",
      "description": "Unique template identifier"
    },
    "name": {
      "type": "string",
      "description": "Human-readable template name"
    },
    "description": {
      "type": "string",
      "description": "Template description"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version"
    },
    "author": {
      "type": "string",
      "description": "Template author"
    },
    "requires": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Runtime requirements"
    },
    "ports": {
      "type": "array",
      "items": {"type": "integer"},
      "description": "Required ports"
    },
    "environment": {
      "type": "object",
      "patternProperties": {
        "^[A-Z][A-Z0-9_]*$": {"type": "string"}
      },
      "description": "Default environment variables"
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["read", "write", "tools", "resources", "prompts"]
      },
      "description": "MCP capabilities"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Template tags"
    }
  }
}
```

## Field Descriptions

### Required Fields

**id**: Unique identifier for the template
- Must start with lowercase letter
- Can contain lowercase letters, numbers, and hyphens
- Used in URLs and commands

**name**: Display name for the template
- Human-readable string
- Used in listings and UI

**description**: Brief description of what the template does
- Should be 1-2 sentences
- Explains the template's purpose

**version**: Semantic version number
- Format: MAJOR.MINOR.PATCH
- Updated when template changes

### Optional Fields

**author**: Template creator
- Individual or organization name
- Used for attribution

**requires**: Runtime requirements
- Array of dependency specifications
- Examples: `["python>=3.10", "docker>=20.0"]`

**ports**: Network ports used by the template
- Array of port numbers
- Used for port mapping in deployments

**environment**: Default environment variables
- Object with variable names and default values
- Variable names should be UPPERCASE

**capabilities**: MCP protocol capabilities
- Array of supported MCP capabilities
- Helps users understand what the server can do

**tags**: Classification tags
- Array of descriptive tags
- Used for filtering and organization

## Examples

### Minimal Template

```json
{
  "id": "hello",
  "name": "Hello World",
  "description": "Simple greeting server",
  "version": "1.0.0"
}
```

### Full Template

```json
{
  "id": "database-connector",
  "name": "Database Connector MCP",
  "description": "Connect to various databases via MCP protocol",
  "version": "2.1.0",
  "author": "Data Everything",
  "requires": ["python>=3.10", "docker>=20.0"],
  "ports": [5432, 8080],
  "environment": {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "LOG_LEVEL": "info"
  },
  "capabilities": ["read", "write", "tools"],
  "tags": ["database", "sql", "connector"]
}
```
