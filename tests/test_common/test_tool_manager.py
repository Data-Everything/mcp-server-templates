"""
Unit tests for ToolManager.

Tests the tool discovery, management, and operations
provided by the ToolManager common module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from mcp_template.common.tool_manager import ToolManager


@pytest.mark.unit
class TestToolManager:
    """Unit tests for ToolManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_manager = ToolManager(backend_type="mock")

    def test_list_tools_static(self):
        """Test static tool discovery."""
        mock_tools = [
            {
                "name": "say_hello",
                "description": "Say hello",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    }
                }
            }
        ]
        
        with patch.object(self.tool_manager, 'discover_tools_static', return_value=mock_tools):
            tools = self.tool_manager.list_tools("demo", discovery_method="static")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "say_hello"
        assert tools[0]["source"] == "static"

    def test_list_tools_dynamic(self):
        """Test dynamic tool discovery."""
        mock_tools = [
            {
                "name": "echo_message",
                "description": "Echo a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"]
                }
            }
        ]
        
        with patch.object(self.tool_manager, 'discover_tools_dynamic', return_value=mock_tools):
            tools = self.tool_manager.list_tools("demo-123", discovery_method="dynamic")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "echo_message"
        assert tools[0]["source"] == "dynamic"

    def test_list_tools_from_image(self):
        """Test image-based tool discovery."""
        mock_tools = [
            {
                "name": "file_read",
                "description": "Read a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    }
                }
            }
        ]
        
        with patch.object(self.tool_manager, 'discover_tools_from_image', return_value=mock_tools):
            tools = self.tool_manager.list_tools("demo:latest", discovery_method="image")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "file_read"
        assert tools[0]["source"] == "image"

    def test_list_tools_auto_discovery(self):
        """Test automatic tool discovery method selection."""
        # Mock different discovery methods to return different results
        dynamic_tools = [{"name": "dynamic_tool", "description": "From running server"}]
        static_tools = [{"name": "static_tool", "description": "From template files"}]
        
        with patch.object(self.tool_manager, 'discover_tools_dynamic', return_value=dynamic_tools):
            with patch.object(self.tool_manager, 'discover_tools_static', return_value=static_tools):
                # Auto should try dynamic first and succeed
                tools = self.tool_manager.list_tools("demo", discovery_method="auto")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "dynamic_tool"

    def test_list_tools_auto_fallback(self):
        """Test auto discovery fallback to static when dynamic fails."""
        static_tools = [{"name": "static_tool", "description": "From template files"}]
        
        with patch.object(self.tool_manager, 'discover_tools_dynamic', side_effect=Exception("Connection failed")):
            with patch.object(self.tool_manager, 'discover_tools_static', return_value=static_tools):
                tools = self.tool_manager.list_tools("demo", discovery_method="auto")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "static_tool"

    def test_discover_tools_static(self):
        """Test static tool discovery from template files."""
        mock_template_tools = [
            {
                "name": "template_tool",
                "description": "Tool from template.json"
            }
        ]
        
        mock_file_tools = [
            {
                "name": "file_tool",
                "description": "Tool from tools.json"
            }
        ]
        
        with patch.object(self.tool_manager.template_manager, 'get_template_tools', return_value=mock_template_tools):
            with patch.object(self.tool_manager.template_manager, 'get_template_path') as mock_get_path:
                mock_path = Mock()
                mock_path.__truediv__ = Mock(return_value=Mock())
                mock_get_path.return_value = mock_path
                
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open_read_json(mock_file_tools)):
                        tools = self.tool_manager.discover_tools_static("demo")
        
        assert len(tools) == 2  # From both template and file
        tool_names = [tool["name"] for tool in tools]
        assert "template_tool" in tool_names
        assert "file_tool" in tool_names

    def test_discover_tools_dynamic(self):
        """Test dynamic tool discovery from running server."""
        mock_deployment_info = {
            "endpoint": "http://localhost:7071",
            "transport": "http"
        }
        
        mock_tools = [
            {
                "name": "live_tool",
                "description": "Tool from running server"
            }
        ]
        
        with patch.object(self.tool_manager.backend, 'get_deployment_status', return_value=mock_deployment_info):
            with patch('mcp_template.core.tool_caller.ToolCaller') as MockToolCaller:
                mock_caller = MockToolCaller.return_value
                mock_caller.list_tools_from_server.return_value = mock_tools
                
                tools = self.tool_manager.discover_tools_dynamic("demo-123", timeout=30)
        
        assert len(tools) == 1
        assert tools[0]["name"] == "live_tool"

    def test_discover_tools_dynamic_no_deployment(self):
        """Test dynamic discovery with no deployment found."""
        with patch.object(self.tool_manager.backend, 'get_deployment_status', side_effect=ValueError("Not found")):
            tools = self.tool_manager.discover_tools_dynamic("nonexistent", timeout=30)
        
        assert len(tools) == 0

    def test_discover_tools_from_image(self):
        """Test tool discovery from Docker image."""
        mock_tools = [
            {
                "name": "image_tool",
                "description": "Tool discovered from image"
            }
        ]
        
        with patch('mcp_template.tools.DockerProbe') as MockDockerProbe:
            mock_probe = MockDockerProbe.return_value
            mock_probe.discover_tools_from_image.return_value = mock_tools
            
            tools = self.tool_manager.discover_tools_from_image("demo:latest", timeout=60)
        
        assert len(tools) == 1
        assert tools[0]["name"] == "image_tool"

    def test_normalize_tool_schema(self):
        """Test tool schema normalization."""
        raw_tool = {
            "name": "test_tool",
            "description": "Test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "required_param": {
                        "type": "string",
                        "description": "Required parameter"
                    },
                    "optional_param": {
                        "type": "number",
                        "description": "Optional parameter"
                    }
                },
                "required": ["required_param"]
            },
            "custom_field": "custom_value"
        }
        
        normalized = self.tool_manager.normalize_tool_schema(raw_tool, "static")
        
        assert normalized["name"] == "test_tool"
        assert normalized["source"] == "static"
        assert "inputSchema" in normalized
        assert "parameters" in normalized
        assert len(normalized["parameters"]) == 2
        
        # Check parameter normalization
        params = {p["name"]: p for p in normalized["parameters"]}
        assert params["required_param"]["required"] is True
        assert params["optional_param"]["required"] is False
        assert "custom_value" in str(normalized["custom_field"])

    def test_normalize_tool_schema_minimal(self):
        """Test normalization of minimal tool definition."""
        raw_tool = {
            "name": "minimal_tool"
        }
        
        normalized = self.tool_manager.normalize_tool_schema(raw_tool, "static")
        
        assert normalized["name"] == "minimal_tool"
        assert normalized["description"] == ""
        assert normalized["inputSchema"] == {}
        assert normalized["parameters"] == []

    def test_validate_tool_definition(self):
        """Test tool definition validation."""
        valid_tool = {
            "name": "valid_tool",
            "description": "A valid tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        }
        
        assert self.tool_manager.validate_tool_definition(valid_tool) is True

    def test_validate_tool_definition_invalid(self):
        """Test validation of invalid tool definitions."""
        # Missing name
        invalid_tool = {
            "description": "Tool without name"
        }
        assert self.tool_manager.validate_tool_definition(invalid_tool) is False
        
        # Invalid input schema
        invalid_tool = {
            "name": "invalid_tool",
            "inputSchema": "not_an_object"
        }
        assert self.tool_manager.validate_tool_definition(invalid_tool) is False

    def test_call_tool(self):
        """Test calling a tool on a running server."""
        mock_deployment_info = {
            "endpoint": "http://localhost:7071",
            "transport": "http"
        }
        
        mock_result = {
            "success": True,
            "result": "Hello, World!"
        }
        
        with patch.object(self.tool_manager.backend, 'get_deployment_status', return_value=mock_deployment_info):
            with patch('mcp_template.core.tool_caller.ToolCaller') as MockToolCaller:
                mock_caller = MockToolCaller.return_value
                mock_caller.call_tool.return_value = mock_result
                
                result = self.tool_manager.call_tool(
                    "demo-123", "say_hello", {"name": "World"}, timeout=30
                )
        
        assert result["success"] is True
        assert result["result"] == "Hello, World!"

    def test_call_tool_no_deployment(self):
        """Test calling tool with no deployment found."""
        with patch.object(self.tool_manager.backend, 'get_deployment_status', side_effect=ValueError("Not found")):
            result = self.tool_manager.call_tool("nonexistent", "tool", {})
        
        assert result["success"] is False
        assert "No deployment found" in result["error"]

    def test_caching_behavior(self):
        """Test tool discovery caching."""
        mock_tools = [{"name": "cached_tool", "description": "Tool for caching test"}]
        
        with patch.object(self.tool_manager, 'discover_tools_static', return_value=mock_tools) as mock_discover:
            # First call should discover tools
            tools1 = self.tool_manager.list_tools("demo", discovery_method="static")
            
            # Second call should use cache
            tools2 = self.tool_manager.list_tools("demo", discovery_method="static")
            
            # Third call with force_refresh should discover again
            tools3 = self.tool_manager.list_tools("demo", discovery_method="static", force_refresh=True)
        
        assert tools1 == tools2 == tools3
        assert mock_discover.call_count == 2  # Initial call + force refresh

    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        mock_tools = [{"name": "test_tool"}]
        
        with patch.object(self.tool_manager, 'discover_tools_static', return_value=mock_tools):
            # Populate cache
            self.tool_manager.list_tools("demo", discovery_method="static")
            
            # Check cache is populated
            cached = self.tool_manager.get_cached_tools("demo", "static")
            assert cached is not None
            
            # Clear cache
            self.tool_manager.clear_cache()
            
            # Check cache is cleared
            cached = self.tool_manager.get_cached_tools("demo", "static")
            assert cached is None

    def test_get_cached_tools(self):
        """Test getting cached tools."""
        mock_tools = [{"name": "cached_tool"}]
        
        # Initially no cache
        cached = self.tool_manager.get_cached_tools("demo", "static")
        assert cached is None
        
        # After discovery, cache should be populated
        with patch.object(self.tool_manager, 'discover_tools_static', return_value=mock_tools):
            tools = self.tool_manager.list_tools("demo", discovery_method="static")
            
        cached = self.tool_manager.get_cached_tools("demo", "static")
        assert cached is not None
        assert len(cached) == 1


@pytest.mark.integration
class TestToolManagerIntegration:
    """Integration tests for ToolManager."""

    def test_tool_discovery_with_real_template(self):
        """Test tool discovery with actual template files."""
        tool_manager = ToolManager(backend_type="mock")
        
        # Should be able to discover tools without errors
        tools = tool_manager.list_tools("demo", discovery_method="static")
        assert isinstance(tools, list)

    def test_tool_manager_with_multiple_sources(self):
        """Test tool manager with multiple discovery sources."""
        tool_manager = ToolManager(backend_type="mock")
        
        # Test that auto discovery doesn't crash
        tools = tool_manager.list_tools("demo", discovery_method="auto")
        assert isinstance(tools, list)

    def test_tool_normalization_integration(self):
        """Test tool normalization in integration context."""
        tool_manager = ToolManager(backend_type="mock")
        
        raw_tools = [
            {
                "name": "integration_tool",
                "description": "Integration test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "test_param": {"type": "string"}
                    }
                }
            }
        ]
        
        with patch.object(tool_manager, 'discover_tools_static', return_value=raw_tools):
            tools = tool_manager.list_tools("demo", discovery_method="static")
        
        assert len(tools) == 1
        assert "parameters" in tools[0]
        assert tools[0]["source"] == "static"


def mock_open_read_json(json_data):
    """Helper to mock opening and reading JSON files."""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(json_data))
