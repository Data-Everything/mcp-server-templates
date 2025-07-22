# MCP Server Templates

This directory contains template definitions for MCP servers that can be deployed through the platform.

## Template Structure

Each template should be defined as a JSON file with the following structure:

```json
{
  "name": "Template Name",
  "description": "Description of what this MCP server does",
  "docker_image": "registry/image-name",
  "docker_tag": "latest",
  "config_schema": {
    "type": "object",
    "properties": {
      "config_key": {
        "type": "string",
        "title": "Configuration Key",
        "description": "Description of this configuration option",
        "default": "default_value"
      }
    },
    "required": ["config_key"]
  },
  "default_config": {
    "config_key": "default_value"
  },
  "exposed_port": 8080,
  "environment_variables": {
    "ENV_VAR": "value"
  },
  "volume_mounts": [
    "/host/path:/container/path"
  ],
  "version": "1.0.0",
  "author": "Author Name",
  "documentation_url": "https://docs.example.com",
  "source_url": "https://github.com/author/repo"
}
```

## Available Templates

- `basic-mcp.json` - Basic MCP server template
- `file-server.json` - File server MCP template
- `database-connector.json` - Database connector MCP template

## Loading Templates

Templates can be loaded into the platform using the Django management command:

```bash
python manage.py load_templates templates/
```
