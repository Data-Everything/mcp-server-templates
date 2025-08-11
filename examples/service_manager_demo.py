#!/usr/bin/env python3
"""
Real-world integration example for MCP Client.

This example demonstrates how to use the MCP Client in a real application
that needs to manage MCP servers programmatically.
"""

import time
from mcp_template import MCPClient


class MCPServiceManager:
    """Example service that manages MCP servers programmatically."""
    
    def __init__(self):
        """Initialize the service with an MCP client."""
        self.client = MCPClient(backend_type="mock")  # Use mock for demo
        self.active_services = {}
    
    def start_service(self, service_name: str, template: str, config: dict = None):
        """Start an MCP service with the given configuration."""
        print(f"🚀 Starting {service_name} service using {template} template...")
        
        try:
            deployment = self.client.deploy(template, config=config or {})
            self.active_services[service_name] = {
                "template": template,
                "deployment": deployment,
                "started_at": time.time()
            }
            print(f"✅ {service_name} service started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start {service_name}: {e}")
            return False
    
    def stop_service(self, service_name: str):
        """Stop a running MCP service."""
        if service_name not in self.active_services:
            print(f"⚠️  Service {service_name} not found")
            return False
        
        try:
            template = self.active_services[service_name]["template"]
            self.client.stop(template)
            del self.active_services[service_name]
            print(f"✅ {service_name} service stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop {service_name}: {e}")
            return False
    
    def list_services(self):
        """List all active services."""
        print(f"\n📋 Active Services ({len(self.active_services)}):")
        if not self.active_services:
            print("   No active services")
            return
        
        for service_name, info in self.active_services.items():
            uptime = time.time() - info["started_at"]
            print(f"   • {service_name} ({info['template']}) - Running for {uptime:.1f}s")
    
    def get_service_tools(self, service_name: str):
        """Get available tools for a service."""
        if service_name not in self.active_services:
            print(f"⚠️  Service {service_name} not found")
            return []
        
        try:
            template = self.active_services[service_name]["template"]
            tools = self.client.discover_tools(template)
            return tools
        except Exception as e:
            print(f"⚠️  Could not discover tools for {service_name}: {e}")
            return []
    
    def call_service_tool(self, service_name: str, tool_name: str, arguments: dict):
        """Call a tool on a specific service."""
        if service_name not in self.active_services:
            print(f"⚠️  Service {service_name} not found")
            return None
        
        try:
            template = self.active_services[service_name]["template"]
            result = self.client.call_tool(template, tool_name, arguments)
            return result
        except Exception as e:
            print(f"⚠️  Could not call {tool_name} on {service_name}: {e}")
            return None
    
    def health_check(self):
        """Perform health check on all services."""
        print("\n🔍 Performing health check...")
        try:
            deployments = self.client.list_deployments()
            print(f"✅ Found {len(deployments)} active deployments")
            
            for service_name in list(self.active_services.keys()):
                # Verify service is still running
                template = self.active_services[service_name]["template"]
                try:
                    status = self.client.get_deployment_status(template)
                    print(f"✅ {service_name}: {status.get('status', 'Unknown')}")
                except Exception:
                    print(f"⚠️  {service_name}: Service may be down")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    def shutdown_all(self):
        """Shutdown all services."""
        print("\n🛑 Shutting down all services...")
        for service_name in list(self.active_services.keys()):
            self.stop_service(service_name)
        print("✅ All services stopped")


def main():
    """Demonstrate the MCP Service Manager."""
    print("🚀 MCP Service Manager Demo")
    print("=" * 40)
    
    # Initialize the service manager
    manager = MCPServiceManager()
    
    # Start some services
    print("\n1. Starting services...")
    manager.start_service("greeting_service", "demo", {
        "greeting": "Welcome to our API!",
        "log_level": "INFO"
    })
    
    manager.start_service("file_service", "filesystem", {
        "allowed_dirs": "/tmp /home/user/docs",
        "read_only": False
    })
    
    # List active services
    manager.list_services()
    
    # Health check
    manager.health_check()
    
    # Demonstrate tool discovery (would work with real deployments)
    print("\n2. Tool discovery example:")
    tools = manager.get_service_tools("greeting_service")
    if tools:
        print(f"✅ Found {len(tools)} tools in greeting_service")
        for tool in tools:
            print(f"   • {tool.get('name', 'Unknown')}")
    else:
        print("ℹ️  Tool discovery example (would work with real HTTP deployments)")
    
    # Demonstrate tool calling (would work with real deployments)
    print("\n3. Tool execution example:")
    result = manager.call_service_tool("greeting_service", "greet", {"name": "API User"})
    if result:
        print(f"✅ Tool result: {result}")
    else:
        print("ℹ️  Tool execution example (would work with real HTTP deployments)")
    
    # Shutdown
    print("\n4. Cleanup...")
    manager.shutdown_all()
    
    print("\n🎉 Demo completed!")
    print("\nThis example shows how to:")
    print("✅ Manage multiple MCP services programmatically")
    print("✅ Start/stop services with custom configurations")
    print("✅ Monitor service health")
    print("✅ Discover and execute tools")
    print("✅ Handle errors gracefully")


if __name__ == "__main__":
    main()