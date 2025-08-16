#!/usr/bin/env python3
"""
Simple tests for MCP Gateway functionality (no pytest required)
"""

import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_template.gateway.registry import ServerRegistry
from mcp_template.gateway.load_balancer import LoadBalancer, HTTPLoadBalancer, StdioConnectionPool


class TestServerRegistry(unittest.TestCase):
    """Test ServerRegistry functionality."""
    
    def test_default_registry(self):
        """Test that default registry is created properly."""
        registry = ServerRegistry()
        servers = registry.list_servers()
        self.assertGreaterEqual(len(servers), 1)
        self.assertIn("demo", servers)
        
        gateway_config = registry.get_gateway_config()
        self.assertEqual(gateway_config["host"], "0.0.0.0")
        self.assertEqual(gateway_config["port"], 8000)
    
    def test_add_remove_servers(self):
        """Test adding and removing servers."""
        registry = ServerRegistry()
        
        # Add a server
        server_config = {
            "type": "http",
            "instances": [{"endpoint": "http://test:8080"}]
        }
        registry.add_server("test-server", server_config)
        
        self.assertIn("test-server", registry.list_servers())
        self.assertEqual(registry.get_server_config("test-server"), server_config)
        
        # Remove the server
        removed = registry.remove_server("test-server")
        self.assertTrue(removed)
        self.assertNotIn("test-server", registry.list_servers())
        
        # Try to remove non-existent server
        removed = registry.remove_server("non-existent")
        self.assertFalse(removed)
    
    def test_config_validation(self):
        """Test server configuration validation."""
        registry = ServerRegistry()
        
        # Valid HTTP config
        http_config = {
            "type": "http",
            "instances": [{"endpoint": "http://test:8080"}]
        }
        errors = registry.validate_server_config(http_config)
        self.assertEqual(len(errors), 0)
        
        # Invalid HTTP config (no instances)
        invalid_http = {"type": "http", "instances": []}
        errors = registry.validate_server_config(invalid_http)
        self.assertGreater(len(errors), 0)
        
        # Valid stdio config
        stdio_config = {
            "type": "stdio",
            "command": ["python", "-m", "test"]
        }
        errors = registry.validate_server_config(stdio_config)
        self.assertEqual(len(errors), 0)
        
        # Invalid stdio config (no command)
        invalid_stdio = {"type": "stdio"}
        errors = registry.validate_server_config(invalid_stdio)
        self.assertGreater(len(errors), 0)
        
        # Valid template config
        template_config = {
            "type": "template",
            "template_name": "demo"
        }
        errors = registry.validate_server_config(template_config)
        self.assertEqual(len(errors), 0)
        
        # Unknown server type
        unknown_config = {"type": "unknown"}
        errors = registry.validate_server_config(unknown_config)
        self.assertGreater(len(errors), 0)
    
    def test_save_load_registry(self):
        """Test saving and loading registry from file."""
        registry = ServerRegistry()
        
        # Add a test server
        registry.add_server("test-server", {
            "type": "stdio",
            "command": ["echo", "test"]
        })
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            registry.save(temp_path)
            
            # Load from file
            registry2 = ServerRegistry(temp_path)
            self.assertIn("test-server", registry2.list_servers())
            
            config = registry2.get_server_config("test-server")
            self.assertEqual(config["type"], "stdio")
            self.assertEqual(config["command"], ["echo", "test"])
            
        finally:
            Path(temp_path).unlink()


class TestHTTPLoadBalancer(unittest.TestCase):
    """Test HTTP load balancer functionality."""
    
    def test_round_robin_balancing(self):
        """Test round-robin load balancing."""
        instances = [
            {"endpoint": "http://server1:8080"},
            {"endpoint": "http://server2:8080"},
            {"endpoint": "http://server3:8080"}
        ]
        
        lb = HTTPLoadBalancer(instances, "round_robin")
        
        # Test multiple rounds
        selected = []
        for i in range(9):  # 3 full cycles
            instance = lb.get_next_instance()
            selected.append(instance["endpoint"])
        
        # Check that we get all instances in rotation
        self.assertEqual(selected[0], "http://server1:8080")
        self.assertEqual(selected[1], "http://server2:8080")
        self.assertEqual(selected[2], "http://server3:8080")
        self.assertEqual(selected[3], "http://server1:8080")  # Start next cycle
    
    def test_health_management(self):
        """Test marking instances as healthy/unhealthy."""
        instances = [
            {"endpoint": "http://server1:8080"},
            {"endpoint": "http://server2:8080"},
            {"endpoint": "http://server3:8080"}
        ]
        
        lb = HTTPLoadBalancer(instances)
        stats = lb.get_stats()
        self.assertEqual(stats["total_instances"], 3)
        self.assertEqual(stats["healthy_instances"], 3)
        
        # Mark one as unhealthy
        lb.mark_unhealthy("http://server2:8080")
        stats = lb.get_stats()
        self.assertEqual(stats["healthy_instances"], 2)
        
        # Get next instances - should not include unhealthy one
        selected = set()
        for i in range(10):
            instance = lb.get_next_instance()
            selected.add(instance["endpoint"])
        
        self.assertNotIn("http://server2:8080", selected)
        self.assertIn("http://server1:8080", selected)
        self.assertIn("http://server3:8080", selected)
        
        # Mark as healthy again
        lb.mark_healthy("http://server2:8080")
        stats = lb.get_stats()
        self.assertEqual(stats["healthy_instances"], 3)
    
    def test_no_healthy_instances(self):
        """Test behavior when no instances are healthy."""
        instances = [{"endpoint": "http://server1:8080"}]
        lb = HTTPLoadBalancer(instances)
        
        # Mark the only instance as unhealthy
        lb.mark_unhealthy("http://server1:8080")
        
        # Should return None when no healthy instances
        instance = lb.get_next_instance()
        self.assertIsNone(instance)


class TestLoadBalancer(unittest.TestCase):
    """Test main LoadBalancer class."""
    
    def test_get_http_balancer(self):
        """Test getting HTTP load balancer."""
        lb = LoadBalancer()
        
        instances = [{"endpoint": "http://test:8080"}]
        http_lb = lb.get_http_balancer("test-server", instances)
        
        self.assertIsNotNone(http_lb)
        self.assertIsInstance(http_lb, HTTPLoadBalancer)
        
        # Should return same instance for same server
        http_lb2 = lb.get_http_balancer("test-server", instances)
        self.assertIs(http_lb, http_lb2)
    
    def test_get_stdio_pool(self):
        """Test getting stdio connection pool."""
        lb = LoadBalancer()
        
        config = {
            "command": ["echo", "test"],
            "pool_size": 2
        }
        pool = lb.get_stdio_pool("test-server", config)
        
        self.assertIsNotNone(pool)
        self.assertIsInstance(pool, StdioConnectionPool)
        
        # Should return same instance for same server
        pool2 = lb.get_stdio_pool("test-server", config)
        self.assertIs(pool, pool2)


class TestStdioConnectionPool(unittest.TestCase):
    """Test stdio connection pool functionality."""
    
    def test_pool_creation(self):
        """Test creating a connection pool."""
        config = {
            "command": ["echo", "test"],
            "pool_size": 2
        }
        
        pool = StdioConnectionPool(config, pool_size=2)
        stats = pool.get_stats()
        
        self.assertEqual(stats["pool_size"], 2)
        self.assertEqual(stats["total_connections"], 0)
        self.assertEqual(stats["available_connections"], 0)
        self.assertEqual(stats["busy_connections"], 0)


class AsyncTestCase(unittest.TestCase):
    """Base class for async tests."""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def run_async(self, coro):
        return self.loop.run_until_complete(coro)


class TestAsyncFunctionality(AsyncTestCase):
    """Test async functionality."""
    
    def test_load_balancer_cleanup(self):
        """Test load balancer cleanup."""
        async def test_cleanup():
            lb = LoadBalancer()
            
            # Create some balancers and pools
            instances = [{"endpoint": "http://test:8080"}]
            http_lb = lb.get_http_balancer("test-http", instances)
            
            config = {"command": ["echo", "test"], "pool_size": 1}
            stdio_pool = lb.get_stdio_pool("test-stdio", config)
            
            # Cleanup should not raise errors
            await lb.cleanup()
            
            # Balancers should be cleared
            self.assertEqual(len(lb.http_balancers), 0)
            self.assertEqual(len(lb.stdio_pools), 0)
        
        self.run_async(test_cleanup())
    
    def test_stdio_pool_cleanup(self):
        """Test stdio pool cleanup."""
        async def test_cleanup():
            config = {
                "command": ["echo", "test"],
                "pool_size": 1
            }
            
            pool = StdioConnectionPool(config, pool_size=1)
            
            # Cleanup should not raise errors even with no connections
            await pool.cleanup()
            
            stats = pool.get_stats()
            self.assertEqual(stats["total_connections"], 0)
        
        self.run_async(test_cleanup())


class TestGatewayIntegration(unittest.TestCase):
    """Integration tests for gateway components."""
    
    def test_registry_and_load_balancer_integration(self):
        """Test that registry and load balancer work together."""
        # Create registry with various server types
        registry = ServerRegistry()
        
        registry.add_server("http-cluster", {
            "type": "http",
            "instances": [
                {"endpoint": "http://server1:8080"},
                {"endpoint": "http://server2:8080"}
            ],
            "load_balancing": "round_robin"
        })
        
        registry.add_server("stdio-pool", {
            "type": "stdio",
            "command": ["python", "-m", "test_server"],
            "pool_size": 3
        })
        
        # Create load balancer and configure from registry
        lb = LoadBalancer()
        
        # Get HTTP balancer
        http_config = registry.get_server_config("http-cluster")
        http_balancer = lb.get_http_balancer(
            "http-cluster", 
            http_config["instances"],
            http_config.get("load_balancing", "round_robin")
        )
        
        self.assertIsNotNone(http_balancer)
        instance = http_balancer.get_next_instance()
        self.assertIn(instance["endpoint"], ["http://server1:8080", "http://server2:8080"])
        
        # Get stdio pool
        stdio_config = registry.get_server_config("stdio-pool")
        stdio_pool = lb.get_stdio_pool("stdio-pool", stdio_config)
        
        self.assertIsNotNone(stdio_pool)
        stats = stdio_pool.get_stats()
        self.assertEqual(stats["pool_size"], 3)


def run_tests():
    """Run all tests and return success status."""
    print("Running MCP Gateway Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestServerRegistry,
        TestHTTPLoadBalancer,
        TestLoadBalancer,
        TestStdioConnectionPool,
        TestAsyncFunctionality,
        TestGatewayIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)