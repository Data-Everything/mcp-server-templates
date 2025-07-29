"""
Tests for tool discovery functionality.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from mcp_template.tools import CacheManager, DockerProbe, ToolDiscovery


class TestToolDiscovery:
    """Test the ToolDiscovery class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "cache"
        self.template_dir = self.temp_dir / "templates" / "test-template"
        self.template_dir.mkdir(parents=True)

        self.discovery = ToolDiscovery(cache_dir=self.cache_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_static_tool_discovery(self):
        """Test static tool discovery from tools.json."""
        # Create a tools.json file
        tools_data = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object"},
                }
            ]
        }

        tools_file = self.template_dir / "tools.json"
        with open(tools_file, "w") as f:
            json.dump(tools_data, f)

        # Test discovery
        result = self.discovery.discover_tools(
            template_name="test-template",
            template_dir=self.template_dir,
            template_config={"tool_discovery": "static"},
        )

        assert result["discovery_method"] == "static"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"

    def test_template_json_fallback(self):
        """Test fallback to template.json tools."""
        template_config = {
            "tools": [{"name": "fallback_tool", "description": "A fallback tool"}]
        }

        result = self.discovery.discover_tools(
            template_name="test-template", template_config=template_config
        )

        assert result["discovery_method"] == "template_json"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "fallback_tool"

    @patch("requests.get")
    def test_dynamic_tool_discovery(self, mock_get):
        """Test dynamic tool discovery from live endpoints."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [{"name": "dynamic_tool", "description": "A dynamic tool"}]
        }
        mock_get.return_value = mock_response

        template_config = {
            "tool_discovery": "dynamic",
            "server_url": "http://localhost:8000",
        }

        result = self.discovery.discover_tools(
            template_name="test-template", template_config=template_config
        )

        assert result["discovery_method"] == "dynamic"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "dynamic_tool"

    def test_normalize_tools(self):
        """Test tool normalization."""
        raw_tools = [
            {
                "name": "tool1",
                "description": "First tool",
                "parameters": {"param1": "value1"},
            },
            {
                "function_name": "tool2",  # Different name field
                "summary": "Second tool",  # Different description field
                "args": {"param2": "value2"},  # Different parameters field
            },
        ]

        normalized = self.discovery._normalize_tools(raw_tools)

        assert len(normalized) == 2
        assert normalized[0]["name"] == "tool1"
        assert normalized[1]["name"] == "tool2"
        assert normalized[1]["description"] == "Second tool"

    def test_cache_integration(self):
        """Test cache integration with tool discovery."""
        # First discovery should cache the result
        template_config = {
            "tools": [{"name": "cached_tool", "description": "A cached tool"}]
        }

        result1 = self.discovery.discover_tools(
            template_name="test-template", template_config=template_config
        )

        # Second discovery should use cache
        result2 = self.discovery.discover_tools(
            template_name="test-template",
            template_config={},  # Empty config, should still get cached result
        )

        assert result1["tools"] == result2["tools"]
        assert "timestamp" in result2

    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        # Create expired cache entry
        expired_data = {
            "tools": [{"name": "expired_tool"}],
            "timestamp": time.time() - (7 * 3600),  # 7 hours ago
            "template_name": "test-template",
        }

        cache_file = self.cache_dir / "test-template.tools.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(expired_data, f)

        # Should not use expired cache
        result = self.discovery.discover_tools(
            template_name="test-template",
            template_config={"tools": [{"name": "new_tool"}]},
        )

        assert result["tools"][0]["name"] == "new_tool"


class TestCacheManager:
    """Test the CacheManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(cache_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        test_data = {"tools": [{"name": "test"}], "discovery_method": "test"}

        # Set cache
        success = self.cache_manager.set("test-key", test_data)
        assert success

        # Get cache
        cached_data = self.cache_manager.get("test-key")
        assert cached_data is not None
        assert cached_data["tools"] == test_data["tools"]
        assert "timestamp" in cached_data

    def test_cache_expiry(self):
        """Test cache expiry."""
        test_data = {"tools": [{"name": "test"}]}

        # Set cache with short max age (in seconds for precision)
        short_cache = CacheManager(
            cache_dir=self.temp_dir, max_age_hours=0.001 / 3600
        )  # About 0.0036 seconds
        short_cache.set("test-key", test_data)

        # Wait for expiry
        time.sleep(0.1)

        # Should return None for expired cache
        cached_data = short_cache.get("test-key")
        assert cached_data is None

    def test_clear_all(self):
        """Test clearing all cache."""
        # Add some cache entries
        self.cache_manager.set("key1", {"tools": []})
        self.cache_manager.set("key2", {"tools": []})

        # Clear all
        removed_count = self.cache_manager.clear_all()
        assert removed_count == 2

        # Should be empty now
        assert self.cache_manager.get("key1") is None
        assert self.cache_manager.get("key2") is None

    def test_cache_info(self):
        """Test cache information."""
        # Add some entries
        self.cache_manager.set("valid", {"tools": []})

        # Get info
        info = self.cache_manager.get_cache_info()
        assert info["total_files"] == 1
        assert info["valid_files"] == 1
        assert info["expired_files"] == 0


class TestDockerProbe:
    """Test the DockerProbe class."""

    def setup_method(self):
        """Set up test environment."""
        self.docker_probe = DockerProbe()

    @patch("subprocess.run")
    @patch("requests.get")
    def test_discover_tools_from_image_success(self, mock_get, mock_run):
        """Test successful tool discovery from Docker image."""

        # Mock Docker commands - need to return different values for each call
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if "docker run" in " ".join(cmd):
                return MagicMock(returncode=0)  # docker run success
            elif "docker inspect" in " ".join(cmd):
                return MagicMock(returncode=0, stdout="true\n")  # container is running
            elif "docker stop" in " ".join(cmd) or "docker rm" in " ".join(cmd):
                return MagicMock(returncode=0)  # cleanup success
            else:
                return MagicMock(returncode=0)

        mock_run.side_effect = mock_subprocess

        # Mock HTTP response - we need to handle multiple endpoint probes
        def mock_http_request(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")

            # Health check endpoint should succeed so container becomes ready
            if "/health" in url:
                mock_response = MagicMock()
                mock_response.status_code = 200
                return mock_response

            # Tools endpoint should succeed with proper response
            if "/tools" in url:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "tools": [{"name": "docker_tool", "description": "A Docker tool"}]
                }
                return mock_response

            # Other endpoints should return 404
            mock_response = MagicMock()
            mock_response.status_code = 404
            return mock_response

        mock_get.side_effect = mock_http_request

        result = self.docker_probe.discover_tools_from_image("test-image")

        assert result is not None
        assert result["discovery_method"] == "docker_http_probe"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "docker_tool"

    def test_generate_container_name(self):
        """Test container name generation."""
        name = self.docker_probe._generate_container_name("test/image:latest")

        assert name.startswith("mcp-tool-discovery-test-image-latest-")
        assert len(name.split("-")) >= 5  # Should have timestamp and random suffix

    @patch("socket.socket")
    def test_find_available_port(self, mock_socket):
        """Test finding available port."""
        # Mock socket to simulate available port
        mock_socket_instance = MagicMock()
        mock_socket_instance.__enter__.return_value = mock_socket_instance
        mock_socket.return_value = mock_socket_instance

        port = self.docker_probe._find_available_port()

        assert port is not None
        assert 8000 <= port < 9000


if __name__ == "__main__":
    pytest.main([__file__])
