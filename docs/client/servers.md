# Server Management

MCPClient provides complete server lifecycle management, allowing you to deploy, monitor, control, and cleanup MCP server instances programmatically.

## Server Deployment

### Start a Server

```python
async with MCPClient() as client:
    # Basic server deployment
    result = await client.start_server("demo")
    
    if result["success"]:
        deployment_id = result["deployment_id"]
        print(f"Server started: {deployment_id}")
        print(f"Status: {result['status']}")
        print(f"Port: {result['port']}")
    else:
        print(f"Deployment failed: {result['error']}")
```

### Start with Configuration

```python
async with MCPClient() as client:
    # Deploy with custom configuration
    config = {
        "greeting": "Hello from API",
        "port": 8080,
        "debug": True
    }
    
    result = await client.start_server("demo", config)
    
    if result["success"]:
        print(f"Configured server started: {result['deployment_id']}")
        print(f"Applied config: {result['config']}")
```

**Parameters**:
- `template_name` (str): Name of the template to deploy
- `config_values` (Dict, optional): Configuration overrides
- `pull_image` (bool, optional): Whether to pull latest image (default: True)

**Returns**: `Dict` containing:
- `success` (bool): Whether deployment succeeded
- `deployment_id` (str): Unique identifier for the deployment
- `container_id` (str): Container identifier  
- `status` (str): Current status ("running", "failed", etc.)
- `port` (int): Assigned port number
- `config` (Dict): Applied configuration
- `error` (str): Error message if deployment failed

**CLI Equivalent**: `mcpt deploy <template> [--config key=value]`

### Advanced Deployment Options

```python
async with MCPClient() as client:
    # Deploy without pulling latest image (faster for testing)
    result = await client.start_server(
        template_name="demo",
        config_values={"env": "development"},
        pull_image=False
    )
    
    # Deploy with environment-specific configuration
    env_config = {
        "api_endpoint": "https://staging-api.example.com",
        "log_level": "DEBUG",
        "timeout": 30
    }
    
    staging_server = await client.start_server("github", env_config)
```

## Server Monitoring

### List Running Servers

```python
async with MCPClient() as client:
    servers = client.list_servers()
    
    print(f"Found {len(servers)} servers:")
    for server in servers:
        print(f"  {server['name']} ({server['template']})")
        print(f"    ID: {server['id']}")
        print(f"    Status: {server['status']}")
        print(f"    Since: {server['since']}")
        print(f"    Port: {server['port']}")
```

**Returns**: `List[Dict]` - List of server information dictionaries containing:
- `id`: Deployment identifier
- `name`: Human-readable server name
- `template`: Template name used for deployment
- `status`: Current status ("running", "stopped", "failed")
- `since`: Start time/duration
- `port`: Assigned port number

**CLI Equivalent**: `mcpt servers` or `mcpt list servers`

### Get Server Details

```python
async with MCPClient() as client:
    deployment_id = "demo-123"
    
    info = client.get_server_info(deployment_id)
    
    print(f"Server Details for {deployment_id}:")
    print(f"  Name: {info['name']}")
    print(f"  Template: {info['template']}")
    print(f"  Status: {info['status']}")
    print(f"  Image: {info['image']}")
    print(f"  Created: {info['created']}")
    print(f"  Port: {info['port']}")
    print(f"  Config: {info['config']}")
```

**Parameters**:
- `deployment_id` (str): The deployment identifier

**Returns**: `Dict` - Detailed server information

**CLI Equivalent**: `mcpt info <deployment_id>`

### Server Health Monitoring

```python
async with MCPClient() as client:
    # Monitor server health
    servers = client.list_servers()
    
    healthy_servers = [s for s in servers if s['status'] == 'running']
    failed_servers = [s for s in servers if s['status'] == 'failed']
    
    print(f"Healthy: {len(healthy_servers)}, Failed: {len(failed_servers)}")
    
    # Check specific server health
    for server in failed_servers:
        logs = client.get_server_logs(server['id'], lines=50)
        print(f"Recent logs for {server['name']}:")
        print(logs)
```

## Server Control

### Stop a Server

```python
async with MCPClient() as client:
    deployment_id = "demo-123"
    
    success = await client.stop_server(deployment_id)
    
    if success:
        print(f"Server {deployment_id} stopped successfully")
    else:
        print(f"Failed to stop server {deployment_id}")
```

**Parameters**:
- `deployment_id` (str): The deployment identifier to stop

**Returns**: `bool` - Whether the stop operation succeeded

**CLI Equivalent**: `mcpt stop <deployment_id>`

### Restart a Server

```python
async with MCPClient() as client:
    deployment_id = "demo-123"
    
    # Stop the server
    await client.stop_server(deployment_id)
    
    # Get original configuration
    server_info = client.get_server_info(deployment_id)
    template_name = server_info['template']
    config = server_info['config']
    
    # Start a new instance with the same configuration
    result = await client.start_server(template_name, config)
    print(f"Restarted as: {result['deployment_id']}")
```

### Bulk Operations

```python
async with MCPClient() as client:
    # Stop all servers of a specific template
    servers = client.list_servers()
    demo_servers = [s for s in servers if s['template'] == 'demo']
    
    for server in demo_servers:
        await client.stop_server(server['id'])
        print(f"Stopped {server['name']}")
    
    # Stop all failed servers
    failed_servers = [s for s in servers if s['status'] == 'failed']
    for server in failed_servers:
        await client.stop_server(server['id'])
        print(f"Cleaned up failed server {server['name']}")
```

## Server Logs

### Get Recent Logs

```python
async with MCPClient() as client:
    deployment_id = "demo-123"
    
    # Get last 100 lines
    logs = client.get_server_logs(deployment_id, lines=100)
    print(f"Recent logs for {deployment_id}:")
    print(logs)
```

### Monitor Logs in Real-time

```python
import asyncio

async def monitor_server_logs(client, deployment_id, interval=5):
    """Monitor server logs with periodic updates"""
    last_lines = 0
    
    while True:
        try:
            logs = client.get_server_logs(deployment_id, lines=50)
            current_lines = len(logs.split('\n'))
            
            if current_lines > last_lines:
                # New log entries
                new_logs = '\n'.join(logs.split('\n')[last_lines:])
                print(f"New logs for {deployment_id}:")
                print(new_logs)
                last_lines = current_lines
            
            await asyncio.sleep(interval)
            
        except KeyboardInterrupt:
            print("Log monitoring stopped")
            break
        except Exception as e:
            print(f"Error monitoring logs: {e}")
            await asyncio.sleep(interval)

# Usage
async with MCPClient() as client:
    await monitor_server_logs(client, "demo-123")
```

**Parameters**:
- `deployment_id` (str): The deployment identifier
- `lines` (int, optional): Number of log lines to retrieve (default: 100)

**Returns**: `str` - Log output as text

**CLI Equivalent**: `mcpt logs <deployment_id> [--lines N]`

## Server Lifecycle Patterns

### Deploy-Test-Cleanup Pattern

```python
async def deploy_test_cleanup_workflow():
    async with MCPClient() as client:
        # Deploy
        result = await client.start_server("demo", {"test_mode": True})
        
        if not result["success"]:
            raise Exception(f"Deployment failed: {result['error']}")
        
        deployment_id = result["deployment_id"]
        
        try:
            # Test
            tools = await client.list_tools("demo")
            assert len(tools) > 0, "No tools found"
            
            # Execute a test tool
            test_result = await client.call_tool("demo", "echo", {
                "message": "test"
            })
            assert test_result["success"], "Tool execution failed"
            
            print("✅ All tests passed")
            
        finally:
            # Cleanup
            await client.stop_server(deployment_id)
            print(f"🧹 Cleaned up {deployment_id}")

# Run the workflow
asyncio.run(deploy_test_cleanup_workflow())
```

### Rolling Deployment Pattern

```python
async def rolling_deployment(template_name, new_config):
    """Perform a rolling deployment with zero downtime"""
    async with MCPClient() as client:
        # Get current servers
        current_servers = [
            s for s in client.list_servers()
            if s['template'] == template_name and s['status'] == 'running'
        ]
        
        # Deploy new instance
        new_server = await client.start_server(template_name, new_config)
        
        if not new_server["success"]:
            raise Exception(f"New deployment failed: {new_server['error']}")
        
        print(f"✅ New server deployed: {new_server['deployment_id']}")
        
        # Wait for new server to be ready
        await asyncio.sleep(5)
        
        # Verify new server is working
        try:
            tools = await client.list_tools(template_name)
            print(f"✅ New server ready with {len(tools)} tools")
        except Exception as e:
            # Rollback
            await client.stop_server(new_server['deployment_id'])
            raise Exception(f"New server failed health check: {e}")
        
        # Stop old servers
        for server in current_servers:
            await client.stop_server(server['id'])
            print(f"🔄 Stopped old server: {server['name']}")
        
        print("🎉 Rolling deployment complete")

# Example usage
asyncio.run(rolling_deployment("demo", {"version": "2.0"}))
```

### Development Environment Pattern

```python
async def setup_development_environment():
    """Set up a complete development environment"""
    async with MCPClient() as client:
        services = [
            ("demo", {"env": "development", "debug": True}),
            ("filesystem", {"allowed_dirs": ["/tmp/dev"]}),
            ("github", {"api_endpoint": "https://api.github.com"})
        ]
        
        deployed_services = []
        
        try:
            for template, config in services:
                result = await client.start_server(template, config)
                
                if result["success"]:
                    deployed_services.append(result["deployment_id"])
                    print(f"✅ Deployed {template}: {result['deployment_id']}")
                else:
                    print(f"❌ Failed to deploy {template}: {result['error']}")
                    raise Exception(f"Environment setup failed at {template}")
            
            print(f"🎉 Development environment ready with {len(deployed_services)} services")
            return deployed_services
            
        except Exception as e:
            # Cleanup on failure
            for deployment_id in deployed_services:
                await client.stop_server(deployment_id)
            raise e

# Usage
deployed = asyncio.run(setup_development_environment())
```

## Error Handling

### Common Server Management Errors

```python
from mcp_template.client import MCPClient
from mcp_template.exceptions import (
    DeploymentError,
    ServerNotFoundError,
    ValidationError
)

async with MCPClient() as client:
    try:
        # Deployment errors
        result = await client.start_server("invalid-template")
    except ValidationError as e:
        print(f"Configuration error: {e}")
    except DeploymentError as e:
        print(f"Deployment failed: {e}")
    
    try:
        # Server not found
        info = client.get_server_info("nonexistent-server")
    except ServerNotFoundError as e:
        print(f"Server error: {e}")
```

### Graceful Error Recovery

```python
async def robust_deployment(template_name, config, max_retries=3):
    """Deploy with automatic retry on failure"""
    async with MCPClient() as client:
        for attempt in range(max_retries):
            try:
                result = await client.start_server(template_name, config)
                
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
        
        raise Exception(f"Failed to deploy {template_name} after {max_retries} attempts")
```
