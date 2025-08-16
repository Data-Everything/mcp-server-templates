"""
Tests for MCP Gateway functionality
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_template.gateway.registry import ServerRegistry
from mcp_template.gateway.load_balancer import LoadBalancer, HTTPLoadBalancer, StdioConnectionPool


class TestServerRegistry:
    """Test ServerRegistry functionality."""
    
    def test_default_registry(self):
        """Test that default registry is created properly."""
        registry = ServerRegistry()
        servers = registry.list_servers()
        assert len(servers) >= 1
        assert "demo" in servers
        
        gateway_config = registry.get_gateway_config()
        assert gateway_config["host"] == "0.0.0.0"
        assert gateway_config["port"] == 8000
    
    def test_add_remove_servers(self):
        """Test adding and removing servers."""
        registry = ServerRegistry()
        
        # Add a server
        server_config = {
            "type": "http",
            "instances": [{"endpoint": "http://test:8080"}]
        }
        registry.add_server("test-server", server_config)
        
        assert "test-server" in registry.list_servers()
        assert registry.get_server_config("test-server") == server_config
        
        # Remove the server
        removed = registry.remove_server("test-server")
        assert removed is True
        assert "test-server" not in registry.list_servers()
        
        # Try to remove non-existent server
        removed = registry.remove_server("non-existent")
        assert removed is False
    
    def test_config_validation(self):
        """Test server configuration validation."""
        registry = ServerRegistry()
        
        # Valid HTTP config
        http_config = {
            "type": "http",
            "instances": [{"endpoint": "http://test:8080"}]
        }
        errors = registry.validate_server_config(http_config)
        assert len(errors) == 0
        
        # Invalid HTTP config (no instances)
        invalid_http = {"type": "http", "instances": []}
        errors = registry.validate_server_config(invalid_http)
        assert len(errors) > 0
        
        # Valid stdio config
        stdio_config = {
            "type": "stdio",
            "command": ["python", "-m", "test"]
        }
        errors = registry.validate_server_config(stdio_config)
        assert len(errors) == 0
        
        # Invalid stdio config (no command)
        invalid_stdio = {"type": "stdio"}
        errors = registry.validate_server_config(invalid_stdio)
        assert len(errors) > 0
        
        # Valid template config
        template_config = {
            "type": "template",
            "template_name": "demo"
        }
        errors = registry.validate_server_config(template_config)
        assert len(errors) == 0
        
        # Unknown server type
        unknown_config = {"type": "unknown"}
        errors = registry.validate_server_config(unknown_config)
        assert len(errors) > 0
    
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
            assert "test-server" in registry2.list_servers()
            
            config = registry2.get_server_config("test-server")
            assert config["type"] == "stdio"
            assert config["command"] == ["echo", "test"]
            
        finally:
            Path(temp_path).unlink()


class TestHTTPLoadBalancer:
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
        assert selected[0] == "http://server1:8080"
        assert selected[1] == "http://server2:8080"
        assert selected[2] == "http://server3:8080"
        assert selected[3] == "http://server1:8080"  # Start next cycle
    
    def test_random_balancing(self):
        """Test random load balancing."""
        instances = [
            {"endpoint": "http://server1:8080"},
            {"endpoint": "http://server2:8080"},
            {"endpoint": "http://server3:8080"}
        ]
        
        lb = HTTPLoadBalancer(instances, "random")
        
        # Get several instances - should include variety
        selected = set()
        for i in range(20):
            instance = lb.get_next_instance()
            selected.add(instance["endpoint"])
        
        # Should see all instances over many requests
        assert len(selected) >= 2  # At least some variety
    
    def test_health_management(self):
        """Test marking instances as healthy/unhealthy."""
        instances = [
            {"endpoint": "http://server1:8080"},
            {"endpoint": "http://server2:8080"},
            {"endpoint": "http://server3:8080"}
        ]
        
        lb = HTTPLoadBalancer(instances)
        stats = lb.get_stats()
        assert stats["total_instances"] == 3
        assert stats["healthy_instances"] == 3
        
        # Mark one as unhealthy
        lb.mark_unhealthy("http://server2:8080")
        stats = lb.get_stats()
        assert stats["healthy_instances"] == 2
        
        # Get next instances - should not include unhealthy one
        selected = set()
        for i in range(10):
            instance = lb.get_next_instance()
            selected.add(instance["endpoint"])
        
        assert "http://server2:8080" not in selected
        assert "http://server1:8080" in selected
        assert "http://server3:8080" in selected
        
        # Mark as healthy again
        lb.mark_healthy("http://server2:8080")
        stats = lb.get_stats()
        assert stats["healthy_instances"] == 3
    
    def test_no_healthy_instances(self):
        """Test behavior when no instances are healthy."""
        instances = [{"endpoint": "http://server1:8080"}]
        lb = HTTPLoadBalancer(instances)
        
        # Mark the only instance as unhealthy
        lb.mark_unhealthy("http://server1:8080")
        
        # Should return None when no healthy instances
        instance = lb.get_next_instance()
        assert instance is None
    
    def test_update_instances(self):
        """Test updating the instance list."""
        initial_instances = [{"endpoint": "http://server1:8080"}]
        lb = HTTPLoadBalancer(initial_instances)
        
        # Update with more instances
        new_instances = [
            {"endpoint": "http://server1:8080"},
            {"endpoint": "http://server2:8080"},
            {"endpoint": "http://server3:8080"}
        ]
        lb.update_instances(new_instances)
        
        stats = lb.get_stats()
        assert stats["total_instances"] == 3
        assert stats["healthy_instances"] == 3


class TestLoadBalancer:
    """Test main LoadBalancer class."""
    
    def test_get_http_balancer(self):
        """Test getting HTTP load balancer."""
        lb = LoadBalancer()
        
        instances = [{"endpoint": "http://test:8080"}]
        http_lb = lb.get_http_balancer("test-server", instances)
        
        assert http_lb is not None
        assert isinstance(http_lb, HTTPLoadBalancer)
        
        # Should return same instance for same server
        http_lb2 = lb.get_http_balancer("test-server", instances)
        assert http_lb is http_lb2
    
    def test_get_stdio_pool(self):
        """Test getting stdio connection pool."""
        lb = LoadBalancer()
        
        config = {
            "command": ["echo", "test"],
            "pool_size": 2
        }
        pool = lb.get_stdio_pool("test-server", config)
        
        assert pool is not None
        assert isinstance(pool, StdioConnectionPool)
        
        # Should return same instance for same server
        pool2 = lb.get_stdio_pool("test-server", config)
        assert pool is pool2
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test load balancer cleanup."""
        lb = LoadBalancer()
        
        # Create some balancers and pools
        instances = [{"endpoint": "http://test:8080"}]
        http_lb = lb.get_http_balancer("test-http", instances)
        
        config = {"command": ["echo", "test"], "pool_size": 1}
        stdio_pool = lb.get_stdio_pool("test-stdio", config)
        
        # Cleanup should not raise errors
        await lb.cleanup()
        
        # Balancers should be cleared
        assert len(lb.http_balancers) == 0
        assert len(lb.stdio_pools) == 0


class TestStdioConnectionPool:
    """Test stdio connection pool functionality."""
    
    @pytest.mark.asyncio
    async def test_pool_creation(self):
        """Test creating a connection pool."""
        config = {
            "command": ["echo", "test"],
            "pool_size": 2
        }
        
        pool = StdioConnectionPool(config, pool_size=2)
        stats = pool.get_stats()
        
        assert stats["pool_size"] == 2
        assert stats["total_connections"] == 0
        assert stats["available_connections"] == 0
        assert stats["busy_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_pool_cleanup(self):
        """Test pool cleanup."""
        config = {
            "command": ["echo", "test"],
            "pool_size": 1
        }
        
        pool = StdioConnectionPool(config, pool_size=1)
        
        # Cleanup should not raise errors even with no connections
        await pool.cleanup()
        
        stats = pool.get_stats()
        assert stats["total_connections"] == 0


class TestGatewayIntegration:
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
        
        assert http_balancer is not None
        instance = http_balancer.get_next_instance()
        assert instance["endpoint"] in ["http://server1:8080", "http://server2:8080"]
        
        # Get stdio pool
        stdio_config = registry.get_server_config("stdio-pool")
        stdio_pool = lb.get_stdio_pool("stdio-pool", stdio_config)
        
        assert stdio_pool is not None
        stats = stdio_pool.get_stats()
        assert stats["pool_size"] == 3
    
    def test_comprehensive_registry_example(self):
        """Test a comprehensive registry configuration."""
        registry = ServerRegistry()
        
        # Configure gateway settings
        registry.update_gateway_config({
            "host": "0.0.0.0",
            "port": 8080,
            "reload_registry": True,
            "health_check_interval": 60
        })
        
        # Add production-like servers
        registry.add_server("auth-service", {
            "type": "http",
            "instances": [
                {"endpoint": "http://auth-1:8080"},
                {"endpoint": "http://auth-2:8080"},
                {"endpoint": "http://auth-3:8080"}
            ],
            "load_balancing": "round_robin",
            "health_check": "/health"
        })
        
        registry.add_server("file-processor", {
            "type": "stdio",
            "command": ["python", "-m", "file_processor"],
            "pool_size": 5,
            "working_dir": "/data",
            "env_vars": {
                "LOG_LEVEL": "info",
                "MAX_WORKERS": "4"
            }
        })
        
        registry.add_server("ai-assistant", {
            "type": "template",
            "template_name": "demo",
            "instances": 2,
            "config": {
                "hello_from": "Production Gateway",
                "log_level": "warning"
            }
        })
        
        # Validate all configurations
        for server_id in registry.list_servers():
            config = registry.get_server_config(server_id)
            errors = registry.validate_server_config(config)
            assert len(errors) == 0, f"Server {server_id} has validation errors: {errors}"
        
        # Test gateway config
        gateway_config = registry.get_gateway_config()
        assert gateway_config["port"] == 8080
        assert gateway_config["health_check_interval"] == 60


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])