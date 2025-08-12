# Tool Execution

MCPClient provides comprehensive tool management, allowing you to discover, inspect, and execute tools from MCP servers programmatically.

## Tool Discovery

### List Tools from Template

```python
async with MCPClient() as client:
    # Discover tools from a template (static discovery)
    tools = await client.list_tools("demo")
    
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  {tool['name']}: {tool.get('description', 'No description')}")
        
        # Show tool schema
        if 'input_schema' in tool:
            required = tool['input_schema'].get('required', [])
            properties = tool['input_schema'].get('properties', {})
            print(f"    Required parameters: {', '.join(required)}")
```

### Dynamic Tool Discovery

```python
async with MCPClient() as client:
    # First deploy a server to get dynamic tools
    server = await client.start_server("demo", {"api_key": "test"})
    
    if server["success"]:
        deployment_id = server["deployment_id"]
        
        # Discover tools from running server (dynamic discovery)
        tools = await client.list_tools("demo", force_refresh=True)
        
        print("Dynamic tools discovered:")
        for tool in tools:
            print(f"  {tool['name']}")
            
        # Cleanup
        await client.stop_server(deployment_id)
```

**Parameters**:
- `template_name` (str): Name of the template
- `force_refresh` (bool, optional): Force refresh of tool cache (default: False)

**Returns**: `List[Dict]` - List of tool definitions containing:
- `name`: Tool name
- `description`: Tool description  
- `input_schema`: JSON schema for tool parameters
- `output_schema`: JSON schema for tool output (if available)

**CLI Equivalent**: `mcpt tools <template>` or (interactive) `tools <template>`

### Tool Inspection

```python
async with MCPClient() as client:
    tools = await client.list_tools("github")
    
    # Find a specific tool
    search_tool = next((t for t in tools if t['name'] == 'search_repositories'), None)
    
    if search_tool:
        print(f"Tool: {search_tool['name']}")
        print(f"Description: {search_tool['description']}")
        
        # Analyze input schema
        schema = search_tool.get('input_schema', {})
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        print("Parameters:")
        for param_name, param_info in properties.items():
            required_str = " (required)" if param_name in required else ""
            param_type = param_info.get('type', 'unknown')
            description = param_info.get('description', 'No description')
            print(f"  {param_name} ({param_type}){required_str}: {description}")
```

## Tool Execution

### Basic Tool Execution

```python
async with MCPClient() as client:
    # Execute a simple tool
    result = await client.call_tool("demo", "echo", {
        "message": "Hello World"
    })
    
    if result["success"]:
        print(f"Tool output: {result['output']}")
        print(f"Execution time: {result['duration']}s")
    else:
        print(f"Tool failed: {result['error']}")
```

### Advanced Tool Execution

```python
async with MCPClient() as client:
    # Execute with complex parameters
    search_params = {
        "query": "machine learning",
        "language": "python",
        "sort": "stars",
        "per_page": 10
    }
    
    result = await client.call_tool("github", "search_repositories", search_params)
    
    if result["success"]:
        repositories = result["output"]
        print(f"Found {len(repositories)} repositories:")
        
        for repo in repositories[:5]:  # Show top 5
            print(f"  {repo['name']}: {repo['description']}")
            print(f"    Stars: {repo['stars']}, Language: {repo['language']}")
```

**Parameters**:
- `template_name` (str): Name of the template containing the tool
- `tool_name` (str): Name of the tool to execute
- `arguments` (Dict): Tool parameters as dictionary
- `config_values` (Dict, optional): Configuration overrides for the tool execution

**Returns**: `Dict` containing:
- `success` (bool): Whether the tool execution succeeded
- `output` (Any): Tool output data (structure depends on tool)
- `error` (str): Error message if execution failed
- `duration` (float): Execution time in seconds
- `logs` (str): Tool execution logs (if available)

**CLI Equivalent**: `mcpt run <template> <tool> '{"param":"value"}'`

### Tool Execution with Configuration

```python
async with MCPClient() as client:
    # Override configuration for specific tool execution
    config_override = {
        "api_endpoint": "https://custom-api.example.com",
        "timeout": 60,
        "debug": True
    }
    
    result = await client.call_tool(
        template_name="github",
        tool_name="create_repository", 
        arguments={
            "name": "my-new-repo",
            "description": "Created via API",
            "private": False
        },
        config_values=config_override
    )
    
    if result["success"]:
        repo_info = result["output"]
        print(f"Created repository: {repo_info['html_url']}")
```

## Tool Workflows

### Sequential Tool Execution

```python
async def github_workflow():
    """Execute a sequence of GitHub operations"""
    async with MCPClient() as client:
        # 1. Search for repositories
        search_result = await client.call_tool("github", "search_repositories", {
            "query": "fastapi",
            "language": "python",
            "per_page": 5
        })
        
        if not search_result["success"]:
            print(f"Search failed: {search_result['error']}")
            return
        
        repositories = search_result["output"]
        print(f"Found {len(repositories)} repositories")
        
        # 2. Get detailed info for the first repository
        if repositories:
            first_repo = repositories[0]
            detail_result = await client.call_tool("github", "get_repository", {
                "owner": first_repo["owner"],
                "repo": first_repo["name"]
            })
            
            if detail_result["success"]:
                repo_details = detail_result["output"]
                print(f"Repository details: {repo_details['description']}")
                print(f"Issues: {repo_details['open_issues_count']}")
                print(f"Forks: {repo_details['forks_count']}")

asyncio.run(github_workflow())
```

### Parallel Tool Execution

```python
import asyncio

async def parallel_tool_execution():
    """Execute multiple tools in parallel"""
    async with MCPClient() as client:
        # Define multiple tool calls
        tool_calls = [
            client.call_tool("demo", "echo", {"message": "Task 1"}),
            client.call_tool("demo", "echo", {"message": "Task 2"}),
            client.call_tool("demo", "echo", {"message": "Task 3"})
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tool_calls, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1} failed: {result}")
            elif result["success"]:
                print(f"Task {i+1} succeeded: {result['output']}")
            else:
                print(f"Task {i+1} failed: {result['error']}")

asyncio.run(parallel_tool_execution())
```

### Tool Chaining

```python
async def file_processing_chain():
    """Chain file operations together"""
    async with MCPClient() as client:
        file_path = "/tmp/test.txt"
        
        # 1. Create a file
        create_result = await client.call_tool("filesystem", "write_file", {
            "path": file_path,
            "content": "Hello, World!\nThis is a test file."
        })
        
        if not create_result["success"]:
            print(f"Failed to create file: {create_result['error']}")
            return
        
        print("✅ File created")
        
        # 2. Read the file back
        read_result = await client.call_tool("filesystem", "read_file", {
            "path": file_path
        })
        
        if read_result["success"]:
            content = read_result["output"]
            print(f"📄 File content: {content}")
            
            # 3. Get file stats
            stat_result = await client.call_tool("filesystem", "get_file_info", {
                "path": file_path
            })
            
            if stat_result["success"]:
                stats = stat_result["output"]
                print(f"📊 File size: {stats['size']} bytes")
                print(f"📅 Modified: {stats['modified']}")

asyncio.run(file_processing_chain())
```

## Tool Validation

### Parameter Validation

```python
async def validate_tool_parameters(template_name, tool_name, params):
    """Validate tool parameters before execution"""
    async with MCPClient() as client:
        # Get tool schema
        tools = await client.list_tools(template_name)
        tool_schema = next((t for t in tools if t['name'] == tool_name), None)
        
        if not tool_schema:
            raise Exception(f"Tool {tool_name} not found in {template_name}")
        
        input_schema = tool_schema.get('input_schema', {})
        required_params = input_schema.get('required', [])
        properties = input_schema.get('properties', {})
        
        # Check required parameters
        missing = [p for p in required_params if p not in params]
        if missing:
            raise Exception(f"Missing required parameters: {missing}")
        
        # Check parameter types
        for param_name, param_value in params.items():
            if param_name in properties:
                expected_type = properties[param_name].get('type')
                if expected_type == 'string' and not isinstance(param_value, str):
                    raise Exception(f"Parameter {param_name} must be a string")
                elif expected_type == 'integer' and not isinstance(param_value, int):
                    raise Exception(f"Parameter {param_name} must be an integer")
                elif expected_type == 'boolean' and not isinstance(param_value, bool):
                    raise Exception(f"Parameter {param_name} must be a boolean")
        
        print("✅ Parameters validated successfully")
        
        # Execute the tool
        return await client.call_tool(template_name, tool_name, params)

# Usage with validation
result = await validate_tool_parameters("github", "search_repositories", {
    "query": "python",
    "per_page": 10
})
```

### Tool Availability Check

```python
async def ensure_tool_available(template_name, tool_name):
    """Ensure a tool is available before execution"""
    async with MCPClient() as client:
        try:
            tools = await client.list_tools(template_name)
            available_tools = [t['name'] for t in tools]
            
            if tool_name not in available_tools:
                print(f"Tool {tool_name} not available")
                print(f"Available tools: {', '.join(available_tools)}")
                return False
            
            print(f"✅ Tool {tool_name} is available")
            return True
            
        except Exception as e:
            print(f"Failed to check tool availability: {e}")
            return False

# Usage
if await ensure_tool_available("demo", "echo"):
    result = await client.call_tool("demo", "echo", {"message": "test"})
```

## Direct Server Connections

### STDIO Tool Execution

```python
async with MCPClient() as client:
    # Connect directly to a server via STDIO
    connection_id = await client.connect_stdio([
        "python", "path/to/custom_server.py"
    ])
    
    if connection_id:
        # List tools from the direct connection
        tools = await client.list_tools_from_connection(connection_id)
        print(f"Tools from STDIO connection: {[t['name'] for t in tools]}")
        
        # Execute tool via direct connection
        result = await client.call_tool_from_connection(
            connection_id,
            "custom_tool",
            {"param": "value"}
        )
        
        if result["success"]:
            print(f"Direct tool result: {result['output']}")
        
        # Clean up connection
        await client.disconnect(connection_id)
```

### Connection Management

```python
async with MCPClient() as client:
    connections = []
    
    try:
        # Create multiple connections
        for i in range(3):
            conn_id = await client.connect_stdio([
                "python", f"server_{i}.py"
            ])
            if conn_id:
                connections.append(conn_id)
        
        # Use connections for parallel tool execution
        tasks = []
        for conn_id in connections:
            task = client.call_tool_from_connection(
                conn_id, "process_data", {"batch": i}
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(results):
            print(f"Connection {i} result: {result}")
    
    finally:
        # Clean up all connections
        for conn_id in connections:
            await client.disconnect(conn_id)
```

## Error Handling

### Tool Execution Errors

```python
from mcp_template.client import MCPClient
from mcp_template.exceptions import ToolCallError, ToolNotFoundError

async with MCPClient() as client:
    try:
        # Tool not found
        result = await client.call_tool("demo", "nonexistent_tool", {})
    except ToolNotFoundError as e:
        print(f"Tool error: {e}")
    
    try:
        # Invalid parameters
        result = await client.call_tool("demo", "echo", {
            "invalid_param": "value"
        })
    except ToolCallError as e:
        print(f"Execution error: {e}")
    
    # Graceful error handling with result checking
    result = await client.call_tool("demo", "echo", {"message": "test"})
    if not result["success"]:
        print(f"Tool failed gracefully: {result['error']}")
```

### Retry Logic

```python
async def execute_tool_with_retry(client, template, tool, params, max_retries=3):
    """Execute tool with automatic retry on failure"""
    for attempt in range(max_retries):
        try:
            result = await client.call_tool(template, tool, params)
            
            if result["success"]:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result['error']}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
    
    raise Exception(f"Tool execution failed after {max_retries} attempts")

# Usage
async with MCPClient() as client:
    result = await execute_tool_with_retry(
        client, "github", "search_repositories",
        {"query": "python", "per_page": 10}
    )
```
