# Creating Templates

Learn how to create your own MCP server templates.

## Template Structure

A template consists of these required components:

```
templates/my-template/
├── template.json          # Template metadata
├── Dockerfile            # Container definition
├── src/                  # Source code
│   └── server.py         # MCP server implementation
├── docs/                 # Documentation
│   └── index.md          # Template documentation
├── tests/                # Test files
│   └── test_units.py     # Unit tests
└── README.md             # Usage instructions
```

## Template Metadata

The `template.json` file defines your template:

```json
{
  "id": "my-template",
  "name": "My Custom MCP Server",
  "description": "A custom MCP server template",
  "version": "1.0.0",
  "author": "Your Name",
  "requires": ["python>=3.10"],
  "ports": [8080],
  "environment": {
    "MY_VAR": "default_value"
  },
  "capabilities": ["read", "write", "tools"]
}
```

## Creating with CLI

Use the built-in template creator:

```bash
mcpt create my-template
```

This will prompt you for template details and generate the structure.

## Next Steps

- See the development guides for detailed instructions
- Check [Testing Templates](testing.md) for testing guidelines
- Review existing templates in the `templates/` directory
