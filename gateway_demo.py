#!/usr/bin/env python3
"""
Demo script for MCP Gateway

This script demonstrates the gateway functionality without requiring external dependencies.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_template.gateway.registry import ServerRegistry
from mcp_template.gateway.load_balancer import LoadBalancer


def demo_registry():
    """Demonstrate registry functionality."""
    print("🔧 Registry Demo")
    print("=" * 50)
    
    # Create registry
    registry = ServerRegistry()
    print(f"✓ Created registry with {len(registry.list_servers())} default servers")
    
    # Add some demo servers
    registry.add_server("test-http", {
        "type": "http",
        "instances": [
            {"endpoint": "http://localhost:8080"},
            {"endpoint": "http://localhost:8081"}
        ],
        "load_balancing": "round_robin"
    })
    
    registry.add_server("test-stdio", {
        "type": "stdio",
        "command": ["python", "-c", "print('Hello from stdio')"],
        "pool_size": 2
    })
    
    print(f"✓ Added servers, now have: {registry.list_servers()}")
    
    # Show validation
    for server_id in registry.list_servers():
        config = registry.get_server_config(server_id)
        errors = registry.validate_server_config(config)
        status = "✓ Valid" if not errors else f"❌ Errors: {errors}"
        print(f"  {server_id}: {status}")
    
    return registry


def demo_load_balancer():
    """Demonstrate load balancer functionality."""
    print("\n⚖️  Load Balancer Demo")
    print("=" * 50)
    
    lb = LoadBalancer()
    
    # Test HTTP load balancing
    instances = [
        {"endpoint": "http://server1:8080"},
        {"endpoint": "http://server2:8080"},
        {"endpoint": "http://server3:8080"}
    ]
    
    http_lb = lb.get_http_balancer("demo-http", instances)
    
    print("Round-robin distribution:")
    for i in range(6):
        instance = http_lb.get_next_instance()
        print(f"  Request {i+1}: {instance['endpoint']}")
    
    # Test health management
    print("\nMarking server2 as unhealthy...")
    http_lb.mark_unhealthy("http://server2:8080")
    
    print("Distribution after health change:")
    for i in range(4):
        instance = http_lb.get_next_instance()
        print(f"  Request {i+1}: {instance['endpoint']}")
    
    stats = http_lb.get_stats()
    print(f"\nLoad balancer stats: {json.dumps(stats, indent=2)}")
    
    return lb


async def demo_gateway_routing():
    """Demonstrate gateway routing logic."""
    print("\n🌉 Gateway Routing Demo")
    print("=" * 50)
    
    registry = ServerRegistry()
    
    # Add various server types
    registry.add_server("http-service", {
        "type": "http",
        "instances": [{"endpoint": "http://example.com:8080"}],
        "load_balancing": "round_robin"
    })
    
    registry.add_server("stdio-service", {
        "type": "stdio", 
        "command": ["echo", "stdio response"],
        "pool_size": 1
    })
    
    registry.add_server("template-service", {
        "type": "template",
        "template_name": "demo",
        "instances": 1,
        "config": {"hello_from": "Gateway Demo"}
    })
    
    print("Available servers and their routing:")
    for server_id in registry.list_servers():
        config = registry.get_server_config(server_id)
        server_type = config.get("type")
        
        if server_type == "http":
            instances = config.get("instances", [])
            endpoints = [inst.get("endpoint") for inst in instances]
            print(f"  {server_id} (HTTP): Routes to {endpoints}")
            
        elif server_type == "stdio":
            command = config.get("command", [])
            print(f"  {server_id} (stdio): Runs {' '.join(command)}")
            
        elif server_type == "template":
            template_name = config.get("template_name")
            print(f"  {server_id} (template): Uses template '{template_name}'")
    
    print("\nGateway URL mapping:")
    print("  GET  /http-service/tools        → List tools from HTTP service")
    print("  POST /http-service/tools/mytool → Call mytool on HTTP service")
    print("  GET  /stdio-service/tools       → List tools from stdio service")
    print("  POST /stdio-service/tools/echo  → Call echo on stdio service")
    print("  GET  /template-service/tools    → List tools from template service")


def demo_configuration():
    """Demonstrate configuration options."""
    print("\n⚙️  Configuration Demo")
    print("=" * 50)
    
    # Create a comprehensive registry configuration
    registry = ServerRegistry()
    
    # Update gateway settings
    registry.update_gateway_config({
        "host": "0.0.0.0",
        "port": 8000,
        "reload_registry": True,
        "health_check_interval": 30
    })
    
    # Add production-like server configurations
    registry.add_server("github-prod", {
        "type": "http",
        "instances": [
            {"endpoint": "http://github-server-1:8080"},
            {"endpoint": "http://github-server-2:8080"},
            {"endpoint": "http://github-server-3:8080"}
        ],
        "load_balancing": "round_robin",
        "health_check": "/health"
    })
    
    registry.add_server("filesystem-pool", {
        "type": "stdio",
        "command": ["python", "-m", "mcp_filesystem"],
        "pool_size": 5,
        "working_dir": "/data",
        "env_vars": {
            "LOG_LEVEL": "info",
            "MAX_FILE_SIZE": "10MB"
        }
    })
    
    registry.add_server("ai-assistant", {
        "type": "template",
        "template_name": "demo",
        "instances": 2,
        "config": {
            "hello_from": "Production Gateway",
            "log_level": "info"
        }
    })
    
    # Save configuration example
    config_file = "demo-gateway-config.json"
    registry.save(config_file)
    
    print(f"✓ Created production-like configuration: {config_file}")
    print(f"✓ Gateway will run on: {registry.get_gateway_config()['host']}:{registry.get_gateway_config()['port']}")
    print(f"✓ Configured {len(registry.list_servers())} servers")
    
    # Show the configuration
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    print("\nGenerated configuration preview:")
    print(json.dumps(config_data, indent=2)[:500] + "...")
    
    return config_file


async def main():
    """Run the complete demo."""
    print("🚀 MCP Gateway Demo")
    print("=" * 50)
    print("This demo shows the gateway functionality without external dependencies.\n")
    
    try:
        # Run demos
        registry = demo_registry()
        lb = demo_load_balancer()
        await demo_gateway_routing()
        config_file = demo_configuration()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Install dependencies: pip install fastapi uvicorn aiohttp")
        print(f"2. Start gateway: python -m mcp_template.gateway.server --registry {config_file}")
        print(f"3. Or use CLI: mcpt gateway start --registry {config_file}")
        print(f"4. Test with: curl http://localhost:8000/servers")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = asyncio.run(main())
    sys.exit(0 if success else 1)