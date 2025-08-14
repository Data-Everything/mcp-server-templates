# Template Operations

MCPClient provides comprehensive template management functionality, allowing you to discover, inspect, and work with MCP server templates programmatically.

## Template Discovery

### List All Templates

```python
async with MCPClient() as client:
    templates = client.list_templates()
    
    for name, template in templates.items():
        print(f"Template: {name}")
        print(f"  Description: {template.get('description', 'N/A')}")
        print(f"  Category: {template.get('category', 'General')}")
        print(f"  Docker Image: {template.get('docker_image', 'N/A')}")
```

**Returns**: `Dict[str, Dict]` - Dictionary mapping template names to template metadata

**CLI Equivalent**: `mcpt list` or `mcpt templates`

### Get Template Details

```python
async with MCPClient() as client:
    # Get detailed information about a specific template
    template_info = client.get_template_info("demo")
    
    print(f"Name: {template_info['name']}")
    print(f"Version: {template_info.get('version', 'unknown')}")
    print(f"Description: {template_info.get('description')}")
    print(f"Config Schema: {template_info.get('config_schema', {})}")
    print(f"Capabilities: {template_info.get('capabilities', [])}")
```

**Parameters**:
- `template_name` (str): Name of the template to inspect

**Returns**: `Dict` - Complete template metadata including:
- `name`: Template display name
- `description`: Template description  
- `version`: Template version
- `config_schema`: JSON schema for configuration
- `capabilities`: List of template capabilities
- `docker_image`: Docker image identifier
- `transport`: Transport configuration (http/stdio)

**CLI Equivalent**: `mcpt info <template>`

### Template Filtering

```python
async with MCPClient() as client:
    # Get only templates with active deployments
    templates = client.list_templates(deployed_only=True)
    
    # Filter by category
    ml_templates = {
        name: template for name, template in templates.items()
        if template.get('category') == 'Machine Learning'
    }
    
    # Filter by transport support
    http_templates = {
        name: template for name, template in templates.items()
        if 'http' in template.get('transport', {}).get('supported', [])
    }
```

## Template Validation

### Check Template Exists

```python
async with MCPClient() as client:
    template_name = "my-template"
    
    try:
        template_info = client.get_template_info(template_name)
        print(f"Template {template_name} is available")
    except TemplateNotFoundError:
        print(f"Template {template_name} not found")
```

### Validate Configuration

```python
from mcp_template.client import MCPClient
from mcp_template.exceptions import ValidationError

async with MCPClient() as client:
    config_values = {
        "api_key": "secret-key",
        "endpoint": "https://api.example.com"
    }
    
    try:
        # The start_server method validates config automatically
        result = await client.start_server("demo", config_values)
        if not result["success"]:
            print(f"Validation failed: {result.get('error')}")
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
```

## Template Metadata

### Understanding Template Structure

Templates contain rich metadata that helps with programmatic usage:

```python
async with MCPClient() as client:
    template = client.get_template_info("demo")
    
    # Configuration schema for validation
    schema = template.get("config_schema", {})
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    print("Required configuration:")
    for field in required_fields:
        field_info = properties.get(field, {})
        print(f"  {field}: {field_info.get('description', 'No description')}")
    
    # Transport configuration
    transport = template.get("transport", {})
    default_transport = transport.get("default", "http")
    supported_transports = transport.get("supported", ["http"])
    
    print(f"Default transport: {default_transport}")
    print(f"Supported transports: {supported_transports}")
    
    # Capabilities for feature detection
    capabilities = template.get("capabilities", [])
    for capability in capabilities:
        print(f"Capability: {capability.get('name')}")
        print(f"  Description: {capability.get('description')}")
```

### Template Categories

Templates are organized by categories for easier discovery:

```python
async with MCPClient() as client:
    templates = client.list_templates()
    
    # Group templates by category
    by_category = {}
    for name, template in templates.items():
        category = template.get("category", "General")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(name)
    
    for category, template_names in by_category.items():
        print(f"{category}: {', '.join(template_names)}")
```

Common categories include:
- **General**: Basic utility templates
- **Development**: Development and debugging tools
- **Data**: Data processing and analysis
- **AI/ML**: Artificial intelligence and machine learning
- **Integration**: Third-party service integrations

## Template Sources

Templates can come from different sources:

### Built-in Templates

```python
async with MCPClient() as client:
    templates = client.list_templates()
    
    # Built-in templates are always available
    builtin_templates = [
        name for name, template in templates.items()
        if template.get("source") == "builtin"
    ]
```

### Custom Templates

```python
# Custom templates can be added to the template directory
# They follow the same structure as built-in templates

async with MCPClient() as client:
    # Custom templates appear alongside built-in ones
    all_templates = client.list_templates()
    
    # Check if a custom template is available
    if "my-custom-template" in all_templates:
        print("Custom template is available")
```

## Error Handling

### Common Template Errors

```python
from mcp_template.client import MCPClient
from mcp_template.exceptions import TemplateNotFoundError, ValidationError

async with MCPClient() as client:
    try:
        # Template not found
        template = client.get_template_info("nonexistent-template")
    except TemplateNotFoundError as e:
        print(f"Template error: {e}")
    
    try:
        # Invalid configuration
        result = await client.start_server("demo", {
            "invalid_field": "value"
        })
    except ValidationError as e:
        print(f"Configuration error: {e}")
```

## Advanced Usage

### Dynamic Template Discovery

```python
async with MCPClient() as client:
    # Discover templates that support specific features
    def find_templates_with_capability(capability_name):
        templates = client.list_templates()
        matching = []
        
        for name, template in templates.items():
            capabilities = template.get("capabilities", [])
            if any(cap.get("name") == capability_name for cap in capabilities):
                matching.append(name)
        
        return matching
    
    # Find templates that support file operations
    file_templates = find_templates_with_capability("file_operations")
    print(f"Templates with file operations: {file_templates}")
```

### Template Comparison

```python
async with MCPClient() as client:
    def compare_templates(template1, template2):
        t1 = client.get_template_info(template1)
        t2 = client.get_template_info(template2)
        
        print(f"Comparing {template1} vs {template2}:")
        print(f"  Category: {t1.get('category')} vs {t2.get('category')}")
        print(f"  Transport: {t1.get('transport', {}).get('default')} vs {t2.get('transport', {}).get('default')}")
        
        # Compare capabilities
        caps1 = {cap.get('name') for cap in t1.get('capabilities', [])}
        caps2 = {cap.get('name') for cap in t2.get('capabilities', [])}
        
        common = caps1 & caps2
        unique1 = caps1 - caps2
        unique2 = caps2 - caps1
        
        if common:
            print(f"  Common capabilities: {', '.join(common)}")
        if unique1:
            print(f"  {template1} unique: {', '.join(unique1)}")
        if unique2:
            print(f"  {template2} unique: {', '.join(unique2)}")
    
    compare_templates("demo", "filesystem")
```
