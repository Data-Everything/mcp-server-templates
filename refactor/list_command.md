# Command Documentation: list

## Command Name
`list` - List available templates

## Purpose
Lists all available MCP server templates with their metadata. The command serves as the primary discovery mechanism for users to see what templates are available for deployment.

## Expected Output

### CLI Output
```
📋 Available Templates:

┌──────────────┬─────────┬──────────────────────────────────────┬────────────────┐
│ Template     │ Version │ Description                          │ Docker Image   │
├──────────────┼─────────┼──────────────────────────────────────┼────────────────┤
│ demo         │ 1.0.0   │ Demo MCP server with example tools   │ demo:latest    │
│ filesystem   │ 1.2.0   │ File system operations server        │ fs:latest      │
└──────────────┴─────────┴──────────────────────────────────────┴────────────────┘

💡 Use 'mcpt deploy <template>' to deploy a template
💡 Use 'mcpt config <template>' to see configuration options
```

### MCPClient Output
```python
{
    "demo": {
        "name": "Demo Server",
        "version": "1.0.0",
        "description": "Demo MCP server with example tools",
        "docker_image": "demo:latest",
        "tools": [...],
        "config_schema": {...}
    },
    "filesystem": {
        "name": "File System Server",
        "version": "1.2.0",
        "description": "File system operations server",
        "docker_image": "fs:latest",
        "tools": [...],
        "config_schema": {...}
    }
}
```

## Current CLI Flow

### CLI Implementation (cli.py / __init__.py)
1. Parse `list` command with optional `--deployed` flag
2. Create MCPDeployer instance
3. Call `deployer.list_templates(deployed_only=args.deployed)`
4. MCPDeployer internally:
   - Uses TemplateDiscovery to find templates
   - Uses backend service to check deployment status
   - Formats output with Rich tables and panels
   - Displays directly to console

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.list_templates()`
2. MCPClient internally:
   - Uses ServerManager to get template info
   - ServerManager calls `list_available_templates()`
   - Returns raw dictionary of template data
   - No formatting - just structured data

## Common Functionality

### Shared Logic (To Extract)
1. **Template Discovery**:
   - Scanning template directories
   - Loading template.json files
   - Validating template structure
   - Building template metadata

2. **Template Information Assembly**:
   - Extracting name, version, description
   - Reading docker image information
   - Loading tool definitions
   - Processing config schemas

3. **Deployment Status Checking** (for --deployed flag):
   - Querying backend services
   - Checking container/deployment status
   - Mapping deployments to templates

### Template Filtering Logic:
   - Filter by deployment status
   - Sort templates by name/version
   - Include/exclude based on criteria

## Specific Functionality

### CLI-Specific Logic
1. **Argument Parsing**:
   - Handle `--deployed` flag
   - Validate command arguments

2. **Output Formatting**:
   - Rich table creation with columns
   - Color coding for status
   - Help text and usage tips
   - Error message display

3. **Console Interaction**:
   - Direct console output
   - Terminal width detection
   - Interactive features

### MCPClient-Specific Logic
1. **Data Structure Assembly**:
   - Return structured dictionaries
   - Ensure consistent data format
   - Handle missing/optional fields

2. **Error Handling**:
   - Return None/empty dict on errors
   - Raise appropriate exceptions
   - Provide error context

## Proposed Refactor Plan

### New Common Module: `mcp_template/common/template_manager.py`
```python
class TemplateManager:
    def __init__(self, backend_type: str = "docker"):
        self.template_discovery = TemplateDiscovery()
        self.backend = get_backend(backend_type)

    def list_templates(self,
                      include_deployed_status: bool = False,
                      filter_deployed_only: bool = False) -> Dict[str, Dict]:
        """Core template listing logic"""
        # Discovery logic
        # Status checking logic
        # Filtering logic
        # Return structured data

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """Get detailed template information"""

    def validate_template(self, template_id: str) -> bool:
        """Validate template exists and is valid"""
```

### Updated CLI Logic
```python
def handle_list_command(args):
    manager = TemplateManager()
    templates = manager.list_templates(
        include_deployed_status=True,
        filter_deployed_only=args.deployed
    )

    # CLI-specific formatting and display
    format_and_display_templates(templates, args.deployed)
```

### Updated MCPClient Logic
```python
def list_templates(self) -> Dict[str, Dict[str, Any]]:
    manager = TemplateManager(self.backend_type)
    return manager.list_templates(include_deployed_status=False)
```

## Implementation Plan

1. **Create TemplateManager class** in `mcp_template/common/template_manager.py`
2. **Extract template discovery logic** from existing implementations
3. **Move shared template operations** to TemplateManager
4. **Update CLI** to use TemplateManager with formatting layer
5. **Update MCPClient** to use TemplateManager directly
6. **Remove duplicate logic** from deployer and server_manager

## Unit Test Plan

### Tests Location: `tests/test_common/test_template_manager.py`

### Test Categories:
```python
@pytest.mark.unit
class TestTemplateManager:
    def test_list_templates_basic()
    def test_list_templates_with_deployment_status()
    def test_list_templates_filter_deployed_only()
    def test_get_template_info_existing()
    def test_get_template_info_nonexistent()
    def test_validate_template_valid()
    def test_validate_template_invalid()

@pytest.mark.integration
class TestTemplateManagerIntegration:
    def test_template_manager_with_real_templates()
    def test_template_manager_with_mock_backend()
```

### Mock Requirements:
- Mock TemplateDiscovery
- Mock backend services
- Mock file system for template loading
- Mock Docker/container status checks

## Dependencies / Risks

### Dependencies:
- TemplateDiscovery class (existing)
- Backend services (docker, kubernetes, mock)
- File system access for template directories
- Container runtime for deployment status

### Risks:
1. **Breaking existing CLI behavior** - Rich formatting and console output
2. **MCPClient API changes** - Return value structure modifications
3. **Template discovery performance** - Multiple scans during refactor
4. **Backend abstraction complexity** - Different backends may have different status APIs

### Mitigation:
1. Maintain exact CLI output format during transition
2. Keep MCPClient API backward compatible
3. Cache template discovery results
4. Use adapter pattern for backend differences
5. Comprehensive integration tests during transition
