# Command Documentation: list_tools

## Command Name
`list_tools` - List available tools

## Purpose
Lists all available tools from MCP servers, either from running deployments or by discovering tools from Docker images. This allows users to see what functionality is available before calling specific tools.

## Expected Output

### CLI Output
```
🔧 Available Tools for demo:

┌─────────────────┬──────────────────────────────────────────────────────────┬─────────────────┐
│ Tool Name       │ Description                                              │ Parameters      │
├─────────────────┼──────────────────────────────────────────────────────────┼─────────────────┤
│ say_hello       │ Say hello with customizable greeting                    │ name (optional) │
│ echo_message    │ Echo back a message                                     │ message         │
│ get_server_info │ Get information about the server                        │ None            │
└─────────────────┴──────────────────────────────────────────────────────────┴─────────────────┘

💡 Use 'call say_hello name="World"' to call a tool
💡 Use 'call say_hello --help' for detailed parameter information
```

### MCPClient Output
```python
[
    {
        "name": "say_hello",
        "description": "Say hello with customizable greeting",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet",
                    "default": "World"
                }
            }
        }
    },
    {
        "name": "echo_message",
        "description": "Echo back a message",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back"
                }
            },
            "required": ["message"]
        }
    }
]
```

## Current CLI Flow

### CLI Implementation (cli.py)
1. Enhanced CLI handles `tools` command (deprecated, redirects to interactive)
2. Interactive CLI implements tool listing:
   - Uses ToolDiscovery for static discovery
   - Uses ToolCaller for runtime tool discovery
   - Uses DockerProbe for image-based discovery
   - Formats output with Rich tables

3. Static discovery path:
   - Loads tools from template.json or tools.json
   - Parses tool definitions and schemas

4. Dynamic discovery path:
   - Connects to running MCP server
   - Calls list_tools MCP method
   - Retrieves live tool information

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.list_tools(template_or_id, force_refresh=False)`
2. MCPClient internally:
   - Uses ToolManager for tool operations
   - Handles both static and dynamic discovery
   - Can connect to running servers or discover from images
   - Returns structured tool data
   - Implements caching for performance

## Common Functionality

### Shared Core Logic (To Extract)
1. **Static Tool Discovery**:
   - Load tools from template.json
   - Load tools from dedicated tools.json files
   - Parse tool definition schemas
   - Validate tool structure

2. **Dynamic Tool Discovery**:
   - Connect to running MCP servers
   - Call MCP list_tools protocol method
   - Handle connection errors and timeouts
   - Parse MCP tool responses

3. **Image-Based Tool Discovery**:
   - Probe Docker images for tool information
   - Run temporary containers for discovery
   - Extract tool definitions from running servers
   - Cache discovery results

4. **Tool Information Processing**:
   - Normalize tool schemas from different sources
   - Extract parameter information
   - Handle optional vs required parameters
   - Process tool descriptions and metadata

5. **Caching and Performance**:
   - Cache tool discoveries per template/image
   - Invalidate cache on template changes
   - Handle cache refresh requests

### Connection Management:
   - Establish MCP connections for discovery
   - Handle different transport protocols
   - Manage connection timeouts and retries
   - Clean up connections after discovery

## Specific Functionality

### CLI-Specific Logic
1. **Output Formatting**:
   - Rich table creation with tool information
   - Color coding for different tool types
   - Parameter formatting and display
   - Help text and usage examples

2. **Interactive Features**:
   - Real-time tool discovery
   - Error message display
   - Progress indicators for slow operations

3. **Discovery Options**:
   - Static vs dynamic discovery selection
   - Image-based discovery options
   - Force refresh capabilities

### MCPClient-Specific Logic
1. **Programmatic Interface**:
   - Structured tool data return
   - Consistent schema normalization
   - Error handling and exception types

2. **Caching Strategy**:
   - Intelligent cache management
   - Cache invalidation logic
   - Performance optimization

3. **Async Support**:
   - Async tool discovery operations
   - Concurrent discovery from multiple sources
   - Background cache updates

## Proposed Refactor Plan

### New Common Module: `mcp_template/common/tool_manager.py`
```python
class ToolManager:
    def __init__(self, backend_type: str = "docker"):
        self.tool_discovery = ToolDiscovery()
        self.tool_caller = ToolCaller()
        self.backend = get_backend(backend_type)
        self._cache = {}

    def list_tools(self,
                   template_or_id: str,
                   discovery_method: str = "auto",  # static, dynamic, image, auto
                   force_refresh: bool = False,
                   timeout: int = 30) -> List[Dict[str, Any]]:
        """Core tool listing logic with caching"""

    def discover_tools_static(self, template_id: str) -> List[Dict]:
        """Discover tools from template files"""

    def discover_tools_dynamic(self, deployment_id: str, timeout: int) -> List[Dict]:
        """Discover tools from running server"""

    def discover_tools_from_image(self, image: str, timeout: int) -> List[Dict]:
        """Discover tools by probing Docker image"""

    def normalize_tool_schema(self, tool_data: Dict, source: str) -> Dict:
        """Normalize tool schemas from different sources"""

    def validate_tool_definition(self, tool: Dict) -> bool:
        """Validate tool definition structure"""
```

### Updated CLI Logic
```python
def handle_tools_command(args):
    manager = ToolManager()

    discovery_method = determine_discovery_method(args)
    tools = manager.list_tools(
        args.template,
        discovery_method=discovery_method,
        force_refresh=args.force_refresh
    )

    # CLI-specific formatting and display
    format_and_display_tools(tools)
```

### Updated MCPClient Logic
```python
def list_tools(self, template_or_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
    manager = ToolManager(self.backend_type)
    return manager.list_tools(template_or_id, force_refresh=force_refresh)
```

## Implementation Plan

1. **Create ToolManager class** in `mcp_template/common/tool_manager.py`
2. **Extract tool discovery logic** from ToolDiscovery, ToolCaller, DockerProbe
3. **Consolidate caching logic** from various components
4. **Move schema normalization** to common module
5. **Update CLI** to use ToolManager with formatting layer
6. **Update MCPClient** to use ToolManager directly
7. **Remove duplicate tool discovery code**

## Unit Test Plan

### Tests Location: `tests/test_common/test_tool_manager.py`

### Test Categories:
```python
@pytest.mark.unit
class TestToolManager:
    def test_list_tools_static()
    def test_list_tools_dynamic()
    def test_list_tools_from_image()
    def test_discover_tools_static()
    def test_discover_tools_dynamic()
    def test_discover_tools_from_image()
    def test_normalize_tool_schema()
    def test_validate_tool_definition()
    def test_caching_behavior()
    def test_cache_invalidation()

@pytest.mark.integration
class TestToolManagerIntegration:
    def test_tool_discovery_with_real_server()
    def test_tool_discovery_with_docker_image()
    def test_tool_manager_with_multiple_sources()
```

### Mock Requirements:
- Mock ToolDiscovery
- Mock ToolCaller and MCP connections
- Mock DockerProbe and container operations
- Mock file system for template loading
- Mock network operations for server connections

## Dependencies / Risks

### Dependencies:
- ToolDiscovery for static discovery
- ToolCaller for MCP connections
- DockerProbe for image-based discovery
- MCP protocol implementation
- Docker runtime for image probing
- File system access for template files

### Risks:
1. **Discovery method complexity** - Multiple discovery paths with different behaviors
2. **MCP protocol compatibility** - Different server implementations
3. **Docker image probing reliability** - Container startup and discovery timeouts
4. **Caching invalidation** - Stale cache issues
5. **Performance with large tool sets** - Discovery speed and memory usage
6. **Network connectivity issues** - Server connection failures

### Mitigation:
1. Clear discovery method selection and fallback logic
2. MCP protocol version detection and compatibility handling
3. Robust timeout and error handling for image probing
4. Smart cache invalidation based on template changes
5. Lazy loading and pagination for large tool sets
6. Connection retry logic and graceful degradation
7. Comprehensive error handling and user feedback
