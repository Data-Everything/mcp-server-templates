# Demo Template Configuration Patterns

The demo template demonstrates two key configuration patterns for MCP server templates:

## Pattern 1: Standard Configuration (config_schema)

Standard configuration uses the `config_schema` in `template.json` and provides:
- Type validation
- Default values
- Environment variable mapping
- Structured configuration management

### Usage Examples:
```bash
# Via CLI config argument
mcpt deploy demo --config hello_from="My Server"
mcpt deploy demo --config log_level=debug

# Via environment variables
MCP_HELLO_FROM="My Server" mcpt deploy demo
```

### In Server Code:
```python
# Access via config_data
hello_from = self.config_data.get('hello_from', 'Default')
log_level = self.config_data.get('log_level', 'info')
```

## Pattern 2: Template Data Overrides (Double Underscore Notation)

Double underscore notation allows overriding ANY part of the template.json structure:
- Modify server metadata
- Customize tool definitions
- Add custom fields
- Override nested properties

### Usage Examples:
```bash
# Override template-level properties
mcpt deploy demo --name="Custom Server Name"
mcpt deploy demo --description="Modified description"

# Override nested tool properties
mcpt deploy demo --tools__0__greeting_style=formal
mcpt deploy demo --tools__0__custom_prefix="Hey there!"

# Add custom fields
mcpt deploy demo --custom_field="any value"
```

### In Server Code:
```python
# Access via template_data (potentially modified by double underscore)
server_name = self.template_data.get("name", "Default Server")
tools = self.template_data.get('tools', [])
say_hello_tool = next((t for t in tools if t.get('name') == 'say_hello'), {})
greeting_style = say_hello_tool.get('greeting_style', 'casual')
```

## When to Use Each Pattern

### Use Standard Configuration (Pattern 1) for:
- Values that need validation
- Configuration with clear defaults
- Settings that map to environment variables
- Core server functionality

### Use Template Overrides (Pattern 2) for:
- Customizing tool behavior
- Adding metadata or custom fields
- Modifying template structure
- Advanced customization scenarios

## Demo Tools

The demo server includes a `demonstrate_overrides` tool that shows both patterns in action and provides usage examples.

```bash
# Deploy demo and call the demonstration tool
mcpt deploy demo
curl -X POST http://localhost:7071/call -H 'Content-Type: application/json' \
  -d '{"method": "demonstrate_overrides", "params": {}}'
```

This returns examples and current configuration for both patterns.
