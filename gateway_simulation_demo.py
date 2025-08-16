#!/usr/bin/env python3
"""
Standalone MCP Gateway Demo

This script demonstrates the MCP Gateway functionality by creating a simple
mock MCP server and routing requests through the gateway.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_template.gateway.registry import ServerRegistry
from mcp_template.gateway.load_balancer import LoadBalancer


class MockMCPServer:
    """Mock MCP server for demonstration."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = [
            {
                "name": "greet",
                "description": f"Greet someone from {name}",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "status",
                "description": f"Get status of {name}",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
    
    async def list_tools(self):
        """List available tools."""
        return {"tools": self.tools}
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool with arguments."""
        if tool_name == "greet":
            name = arguments.get("name", "World")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Hello {name}! Greetings from {self.name}"
                    }
                ]
            }
        elif tool_name == "status":
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Server {self.name} is running and healthy"
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


class GatewaySimulator:
    """Simulates gateway routing without HTTP server."""
    
    def __init__(self):
        self.registry = ServerRegistry()
        self.load_balancer = LoadBalancer()
        self.mock_servers = {}
        self._setup_mock_servers()
    
    def _setup_mock_servers(self):
        """Set up mock servers for demonstration."""
        # Create mock HTTP servers (simulated)
        self.mock_servers["web-service-1"] = MockMCPServer("WebService-1")
        self.mock_servers["web-service-2"] = MockMCPServer("WebService-2") 
        self.mock_servers["web-service-3"] = MockMCPServer("WebService-3")
        
        # Create mock stdio server
        self.mock_servers["worker-service"] = MockMCPServer("WorkerService")
        
        # Register servers in gateway
        self.registry.add_server("web-cluster", {
            "type": "http",
            "instances": [
                {"endpoint": "http://web-service-1:8080"},
                {"endpoint": "http://web-service-2:8080"},
                {"endpoint": "http://web-service-3:8080"}
            ],
            "load_balancing": "round_robin"
        })
        
        self.registry.add_server("worker-pool", {
            "type": "stdio",
            "command": ["python", "-m", "worker_service"],
            "pool_size": 2
        })
        
        print("✓ Set up mock servers:")
        print("  - web-cluster: 3 HTTP instances with load balancing")
        print("  - worker-pool: stdio server with connection pooling")
    
    async def simulate_request(self, server_id: str, action: str, **kwargs):
        """Simulate a request through the gateway."""
        print(f"\n🔀 Gateway routing: {server_id}/{action}")
        
        # Get server config
        config = self.registry.get_server_config(server_id)
        if not config:
            return {"error": f"Server '{server_id}' not found"}
        
        server_type = config.get("type")
        
        if server_type == "http":
            return await self._route_http_request(server_id, config, action, **kwargs)
        elif server_type == "stdio":
            return await self._route_stdio_request(server_id, config, action, **kwargs)
        else:
            return {"error": f"Unsupported server type: {server_type}"}
    
    async def _route_http_request(self, server_id: str, config: dict, action: str, **kwargs):
        """Simulate HTTP request routing."""
        instances = config.get("instances", [])
        balancer = self.load_balancer.get_http_balancer(server_id, instances)
        
        instance = balancer.get_next_instance()
        if not instance:
            return {"error": "No healthy instances available"}
        
        endpoint = instance["endpoint"]
        print(f"  → Routing to: {endpoint}")
        
        # Map endpoint to mock server
        server_name = endpoint.split("//")[1].split(":")[0]  # Extract server name
        mock_server = self.mock_servers.get(server_name)
        
        if not mock_server:
            return {"error": f"Mock server not found: {server_name}"}
        
        # Execute action
        if action == "list_tools":
            return await mock_server.list_tools()
        elif action == "call_tool":
            tool_name = kwargs.get("tool_name")
            arguments = kwargs.get("arguments", {})
            return await mock_server.call_tool(tool_name, arguments)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def _route_stdio_request(self, server_id: str, config: dict, action: str, **kwargs):
        """Simulate stdio request routing."""
        pool = self.load_balancer.get_stdio_pool(server_id, config)
        
        print(f"  → Using stdio connection pool (size: {config.get('pool_size', 1)})")
        
        # Simulate getting connection from pool
        mock_server = self.mock_servers.get("worker-service")
        if not mock_server:
            return {"error": "Worker service not available"}
        
        # Execute action
        if action == "list_tools":
            return await mock_server.list_tools()
        elif action == "call_tool":
            tool_name = kwargs.get("tool_name")
            arguments = kwargs.get("arguments", {})
            return await mock_server.call_tool(tool_name, arguments)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def show_load_balancer_stats(self):
        """Show current load balancer statistics."""
        print("\n📊 Load Balancer Statistics:")
        
        for server_id, balancer in self.load_balancer.http_balancers.items():
            stats = balancer.get_stats()
            print(f"  {server_id} (HTTP):")
            print(f"    Total instances: {stats['total_instances']}")
            print(f"    Healthy instances: {stats['healthy_instances']}")
            print(f"    Strategy: {stats['strategy']}")
            print(f"    Endpoints: {stats['instance_endpoints']}")
        
        for server_id, pool in self.load_balancer.stdio_pools.items():
            stats = pool.get_stats()
            print(f"  {server_id} (stdio):")
            print(f"    Pool size: {stats['pool_size']}")
            print(f"    Active connections: {stats['total_connections']}")
    
    async def run_demo(self):
        """Run the complete demonstration."""
        print("🚀 MCP Gateway Simulation Demo")
        print("=" * 50)
        
        # Show available servers
        print("\n📋 Available Servers:")
        for server_id in self.registry.list_servers():
            config = self.registry.get_server_config(server_id)
            print(f"  {server_id}: {config.get('type')} server")
        
        # Simulate various requests
        print("\n🌐 Simulating HTTP Load Balancing:")
        
        # Make several requests to see load balancing
        for i in range(6):
            result = await self.simulate_request("web-cluster", "call_tool", 
                                               tool_name="greet", 
                                               arguments={"name": f"User{i+1}"})
            if "content" in result:
                message = result["content"][0]["text"]
                print(f"  Request {i+1}: {message}")
        
        # Show HTTP load balancer stats
        print("\n📊 HTTP Load Balancer Distribution:")
        balancer = self.load_balancer.http_balancers.get("web-cluster")
        if balancer:
            stats = balancer.get_stats()
            print(f"  Distributed across {stats['healthy_instances']} instances")
        
        # Simulate health issue
        print("\n🏥 Simulating Health Management:")
        if balancer:
            balancer.mark_unhealthy("http://web-service-2:8080")
            print("  Marked web-service-2 as unhealthy")
            
            # Make more requests
            for i in range(4):
                result = await self.simulate_request("web-cluster", "call_tool",
                                                   tool_name="status")
                if "content" in result:
                    message = result["content"][0]["text"]
                    print(f"  Health check {i+1}: {message}")
        
        # Simulate stdio requests
        print("\n🔧 Simulating stdio Connection Pooling:")
        
        for i in range(3):
            result = await self.simulate_request("worker-pool", "call_tool",
                                               tool_name="greet",
                                               arguments={"name": f"Worker{i+1}"})
            if "content" in result:
                message = result["content"][0]["text"]
                print(f"  Worker request {i+1}: {message}")
        
        # List tools from different servers
        print("\n🛠️  Tool Discovery:")
        
        for server_id in ["web-cluster", "worker-pool"]:
            result = await self.simulate_request(server_id, "list_tools")
            if "tools" in result:
                tools = [tool["name"] for tool in result["tools"]]
                print(f"  {server_id} tools: {', '.join(tools)}")
        
        # Show final statistics
        self.show_load_balancer_stats()
        
        print("\n🎯 Gateway Features Demonstrated:")
        print("  ✓ HTTP server load balancing (round-robin)")
        print("  ✓ Health management (unhealthy instance removal)")
        print("  ✓ stdio server connection pooling")
        print("  ✓ Unified tool discovery across server types")
        print("  ✓ Transparent request routing")
        
        print(f"\n📖 What this would look like with a real gateway:")
        print(f"  GET  http://localhost:8000/web-cluster/tools")
        print(f"  POST http://localhost:8000/web-cluster/tools/greet")
        print(f"  GET  http://localhost:8000/worker-pool/tools")
        print(f"  POST http://localhost:8000/worker-pool/tools/status")


async def main():
    """Run the gateway simulation demo."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    try:
        simulator = GatewaySimulator()
        await simulator.run_demo()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"\nTo run a real gateway:")
        print(f"1. Install dependencies: pip install fastapi uvicorn aiohttp")
        print(f"2. Create configuration: mcpt gateway example --output gateway.json")
        print(f"3. Start gateway: mcpt gateway start --registry gateway.json")
        print(f"4. Access at: http://localhost:8000")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)