## Creating New Templates

You can create new MCP server templates using the integrated CLI command:

```bash
# Interactive template creation
python -m mcp_template create

# Create with specific template ID
python -m mcp_template create my-new-template

# Create from configuration file
python -m mcp_template create --config-file template-config.json

# Non-interactive mode
python -m mcp_template create my-template --config-file config.json --non-interactive
```

### Template Configuration File Format

```json
{
  "id": "my-template",
  "name": "My Template",
  "description": "A custom MCP server template",
  "version": "1.0.0",
  "author": "Your Name",
  "docker_image": "dataeverything/mcp-my-template",
  "capabilities": [
    {
      "name": "my_tool",
      "description": "Description of the tool",
      "example": "Example usage",
      "example_args": {
        "param1": "string_value",
        "param2": 42
      },
      "example_response": "Operation completed"
    }
  ],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API key for authentication",
        "env_mapping": "MY_API_KEY"
      }
    },
    "required": ["api_key"]
  }
}
```

This will create:
- Template directory: `templates/my-template/`
- Test directory: `tests/templates/my-template/`
- Complete boilerplate code including server.py, Dockerfile, tests, and documentation
