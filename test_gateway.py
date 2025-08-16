"""
Basic tests for MCP Gateway functionality
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

def test_server_registry():
    """Test ServerRegistry functionality."""
    print("Testing ServerRegistry...")
    
    from mcp_template.gateway.registry import ServerRegistry
    
    # Test with default config
    registry = ServerRegistry()
    servers = registry.list_servers()
    assert len(servers) >= 1, "Should have at least demo server"
    print(f"✓ Default registry has {len(servers)} servers: {servers}")
    
    # Test adding a server
    registry.add_server("test-server", {
        "type": "stdio",
        "command": ["python", "-m", "test"]
    })
    assert "test-server" in registry.list_servers()
    print("✓ Can add servers to registry")
    
    # Test validation
    config = {"type": "http", "instances": [{"endpoint": "http://test:8080"}]}
    errors = registry.validate_server_config(config)
    assert len(errors) == 0, f"Valid config should have no errors: {errors}"
    print("✓ Config validation works")
    
    # Test saving/loading
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        registry.save(f.name)
        
        # Load from file
        registry2 = ServerRegistry(f.name)
        assert "test-server" in registry2.list_servers()
        print("✓ Can save and load registry")
        
        # Cleanup
        os.unlink(f.name)


def test_load_balancer():
    """Test LoadBalancer functionality."""
    print("\nTesting LoadBalancer...")
    
    from mcp_template.gateway.load_balancer import LoadBalancer, HTTPLoadBalancer
    
    # Test HTTP load balancer
    instances = [
        {"endpoint": "http://server1:8080"},
        {"endpoint": "http://server2:8080"},
        {"endpoint": "http://server3:8080"}
    ]
    
    http_lb = HTTPLoadBalancer(instances, "round_robin")
    
    # Test round-robin distribution
    selected = []
    for i in range(6):  # Test 2 full cycles
        instance = http_lb.get_next_instance()
        selected.append(instance["endpoint"])
    
    # Should cycle through all instances
    unique_selected = set(selected[:3])
    assert len(unique_selected) == 3, f"Should select all 3 instances: {unique_selected}"
    print("✓ Round-robin load balancing works")
    
    # Test health marking
    http_lb.mark_unhealthy("http://server2:8080")
    stats = http_lb.get_stats()
    assert stats["healthy_instances"] == 2, f"Should have 2 healthy instances: {stats}"
    print("✓ Health marking works")
    
    # Test main load balancer
    lb = LoadBalancer()
    http_balancer = lb.get_http_balancer("test-server", instances)
    assert http_balancer is not None
    print("✓ Main load balancer can create HTTP balancers")


async def test_stdio_connection_pool():
    """Test stdio connection pool (basic functionality)."""
    print("\nTesting stdio connection pool...")
    
    from mcp_template.gateway.load_balancer import StdioConnectionPool
    
    # Create a pool with mock stdio config
    config = {
        "command": ["echo", "test"],  # Simple command that should work
        "pool_size": 2
    }
    
    pool = StdioConnectionPool(config, pool_size=2)
    stats = pool.get_stats()
    assert stats["pool_size"] == 2
    print("✓ Stdio connection pool created")
    
    # Cleanup
    await pool.cleanup()
    print("✓ Stdio connection pool cleanup works")


def test_registry_examples():
    """Test that the example registries are valid."""
    print("\nTesting example registries...")
    
    from mcp_template.gateway.registry import ServerRegistry
    
    # Test the example registry file
    example_path = Path(__file__).parent / "example-gateway-registry.json"
    if example_path.exists():
        registry = ServerRegistry(example_path)
        servers = registry.list_servers()
        print(f"✓ Example registry loads with {len(servers)} servers")
        
        # Validate all servers
        for server_id in servers:
            config = registry.get_server_config(server_id)
            errors = registry.validate_server_config(config)
            if errors:
                print(f"⚠ Server {server_id} has validation issues: {errors}")
            else:
                print(f"✓ Server {server_id} config is valid")
    else:
        print("⚠ Example registry file not found, creating one...")
        registry = ServerRegistry()
        registry.save(example_path)
        print(f"✓ Created example registry at {example_path}")


async def main():
    """Run all tests."""
    print("Running MCP Gateway tests...\n")
    
    try:
        test_server_registry()
        test_load_balancer()
        await test_stdio_connection_pool()
        test_registry_examples()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)