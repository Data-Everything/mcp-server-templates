"""
Unit tests for ToolManager in the common module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.common.tool_manager import ToolManager
from tests.test_fixtures.sample_data import SAMPLE_TEMPLATE_DATA, SAMPLE_TOOL_DATA


@pytest.mark.unit
class TestToolManagerCore:
    """Core functionality tests for ToolManager."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        manager = ToolManager()
        assert manager.backend_type == "docker"
        assert manager.tool_discovery is not None
        assert manager.docker_probe is not None
        assert isinstance(manager._cache, dict)

    def test_init_custom_backend(self):
        """Test initialization with custom backend type."""
        manager = ToolManager(backend_type="kubernetes")
        assert manager.backend_type == "kubernetes"

    def test_cache_initialization(self):
        """Test cache is properly initialized."""
        manager = ToolManager()
        assert manager._cache == {}
        assert manager.get_cache_stats()["cache_size"] == 0

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        manager = ToolManager()
        manager._cache["test_key"] = "test_value"

        manager.clear_cache()

        assert manager._cache == {}
        assert manager.get_cache_stats()["cache_size"] == 0


@pytest.mark.unit
class TestToolManagerDiscovery:
    """Test tool discovery functionality."""

    @patch("mcp_template.common.tool_manager.ToolDiscovery")
    def test_discover_tools_static_success(self, mock_tool_discovery_class):
        """Test successful static tool discovery."""
        mock_discovery = Mock()
        mock_tool_discovery_class.return_value = mock_discovery
        mock_discovery.discover_tools.return_value = {
            "tools": SAMPLE_TOOL_DATA["filesystem"]["tools"],
            "source_file": "template.json",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="filesystem",
            template_config=SAMPLE_TEMPLATE_DATA["filesystem"],
            discovery_method="static",
        )

        assert result["discovery_method"] == "static"
        assert len(result["tools"]) == 2
        assert result["tools"][0]["name"] == "read_file"
        assert result["source"] == "template.json"

    @patch("mcp_template.common.tool_manager.ToolDiscovery")
    def test_discover_tools_dynamic_success(self, mock_tool_discovery_class):
        """Test successful dynamic tool discovery."""
        mock_discovery = Mock()
        mock_tool_discovery_class.return_value = mock_discovery
        mock_discovery.discover_tools.return_value = {
            "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
            "source_endpoint": "mcp_server",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="demo",
            template_config=SAMPLE_TEMPLATE_DATA["demo"],
            discovery_method="dynamic",
        )

        assert result["discovery_method"] == "dynamic"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "echo"
        assert result["source"] == "mcp_server"

    @patch("mcp_template.common.tool_manager.DockerProbe")
    def test_discover_tools_docker_success(self, mock_docker_probe_class):
        """Test successful Docker tool discovery."""
        mock_probe = Mock()
        mock_docker_probe_class.return_value = mock_probe
        mock_probe.discover_tools_from_image.return_value = {
            "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
            "timestamp": "2024-01-01T00:00:00Z",
        }

        template_config = {
            "docker_image": "demo-image",
            "docker_tag": "latest",
            "env_vars": {"DEBUG": "true"},
        }

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="demo",
            template_config=template_config,
            discovery_method="docker",
        )

        assert result["discovery_method"] == "docker"
        assert len(result["tools"]) == 1
        assert result["source"] == "Docker image: demo-image:latest"
        mock_probe.discover_tools_from_image.assert_called_once()

    def test_discover_tools_docker_no_image(self):
        """Test Docker discovery when no image is specified."""
        template_config = {}  # No docker_image

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="demo",
            template_config=template_config,
            discovery_method="docker",
        )

        assert result["discovery_method"] == "docker"
        assert result["tools"] == []
        assert "No Docker image specified" in result["error"]

    @patch("mcp_template.common.tool_manager.ToolDiscovery")
    def test_discover_tools_auto_fallback(self, mock_tool_discovery_class):
        """Test auto discovery with fallback behavior."""
        mock_discovery = Mock()
        mock_tool_discovery_class.return_value = mock_discovery

        # Static discovery returns empty
        mock_discovery.discover_tools.side_effect = [
            {"tools": []},  # Static
            {"tools": SAMPLE_TOOL_DATA["demo"]["tools"]},  # Dynamic
        ]

        template_config = {"tool_discovery": "dynamic", "docker_image": "demo-image"}

        manager = ToolManager()
        with patch.object(manager, "_discover_tools_from_docker") as mock_docker:
            mock_docker.return_value = {"tools": [], "discovery_method": "docker"}

            result = manager.discover_tools(
                template_name="demo",
                template_config=template_config,
                discovery_method="auto",
            )

            # Should use dynamic discovery result
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "echo"

    def test_discover_tools_caching(self):
        """Test tool discovery caching functionality."""
        template_config = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "_discover_tools_static") as mock_static:
            mock_static.return_value = {
                "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
                "discovery_method": "static",
            }

            manager = ToolManager()

            # First call
            result1 = manager.discover_tools(
                template_name="demo",
                template_config=template_config,
                discovery_method="static",
                use_cache=True,
            )

            # Second call should use cache
            result2 = manager.discover_tools(
                template_name="demo",
                template_config=template_config,
                discovery_method="static",
                use_cache=True,
            )

            # Should only call the discovery method once
            mock_static.assert_called_once()
            assert result1 == result2

    def test_discover_tools_force_refresh(self):
        """Test force refresh bypasses cache."""
        template_config = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "_discover_tools_static") as mock_static:
            mock_static.return_value = {
                "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
                "discovery_method": "static",
            }

            manager = ToolManager()

            # First call
            manager.discover_tools(
                template_name="demo",
                template_config=template_config,
                discovery_method="static",
                use_cache=True,
            )

            # Second call with force refresh
            manager.discover_tools(
                template_name="demo",
                template_config=template_config,
                discovery_method="static",
                use_cache=True,
                force_refresh=True,
            )

            # Should call discovery method twice
            assert mock_static.call_count == 2

    def test_discover_tools_unknown_method(self):
        """Test discovery with unknown method."""
        manager = ToolManager()
        result = manager.discover_tools(
            template_name="demo", template_config={}, discovery_method="unknown"
        )

        assert result["tools"] == []
        assert result["discovery_method"] == "unknown"
        assert "Unknown discovery method" in result["error"]

    def test_discover_tools_exception_handling(self):
        """Test exception handling in discovery."""
        with patch.object(ToolManager, "_discover_tools_static") as mock_static:
            mock_static.side_effect = Exception("Discovery failed")

            manager = ToolManager()
            result = manager.discover_tools(
                template_name="demo", template_config={}, discovery_method="static"
            )

            assert result["tools"] == []
            assert result["discovery_method"] == "static"
            assert "Discovery failed" in result["error"]


@pytest.mark.unit
class TestToolManagerListTools:
    """Test tool listing functionality."""

    @patch("mcp_template.common.template_manager.TemplateManager")
    def test_list_tools_success(self, mock_template_manager_class):
        """Test successful tool listing."""
        mock_template_manager = Mock()
        mock_template_manager_class.return_value = mock_template_manager
        mock_template_manager.get_template.return_value = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "discover_tools") as mock_discover:
            mock_discover.return_value = {"tools": SAMPLE_TOOL_DATA["demo"]["tools"]}

            manager = ToolManager()
            tools = manager.list_tools("demo")

            assert len(tools) == 1
            assert tools[0]["name"] == "echo"

    @patch("mcp_template.common.template_manager.TemplateManager")
    def test_list_tools_template_not_found(self, mock_template_manager_class):
        """Test tool listing when template is not found."""
        mock_template_manager = Mock()
        mock_template_manager_class.return_value = mock_template_manager
        mock_template_manager.get_template.return_value = None

        manager = ToolManager()
        tools = manager.list_tools("nonexistent")

        assert tools == []

    @patch("mcp_template.common.template_manager.TemplateManager")
    def test_list_tools_exception_handling(self, mock_template_manager_class):
        """Test exception handling in list_tools."""
        mock_template_manager_class.side_effect = Exception("Template manager error")

        manager = ToolManager()
        tools = manager.list_tools("demo")

        assert tools == []


@pytest.mark.unit
class TestToolManagerValidation:
    """Test tool validation functionality."""

    def test_validate_tool_call_success(self):
        """Test successful tool call validation."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]
        tool_args = {"message": "Hello, world!"}

        manager = ToolManager()
        result = manager.validate_tool_call("echo", tool_args, tools)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_tool_call_tool_not_found(self):
        """Test validation when tool is not found."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]

        manager = ToolManager()
        result = manager.validate_tool_call("nonexistent", {}, tools)

        assert result["valid"] is False
        assert "Tool 'nonexistent' not found" in result["errors"]

    def test_validate_tool_call_missing_required_args(self):
        """Test validation with missing required arguments."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]
        tool_args = {}  # Missing required 'message' argument

        manager = ToolManager()
        result = manager.validate_tool_call("echo", tool_args, tools)

        assert result["valid"] is False
        assert any("Missing required argument" in error for error in result["errors"])

    def test_validate_tool_call_invalid_arg_type(self):
        """Test validation with invalid argument types."""
        tools = SAMPLE_TOOL_DATA["filesystem"]["tools"]
        tool_args = {"path": 123}  # Should be string

        manager = ToolManager()
        result = manager.validate_tool_call("read_file", tool_args, tools)

        assert result["valid"] is False
        assert any("must be a string" in error for error in result["errors"])

    def test_validate_tool_call_unknown_args(self):
        """Test validation with unknown arguments."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]
        tool_args = {"message": "Hello", "unknown_arg": "value"}

        manager = ToolManager()
        result = manager.validate_tool_call("echo", tool_args, tools)

        assert result["valid"] is True  # Still valid, just warning
        assert "Unknown argument: unknown_arg" in result["warnings"]

    def test_validate_tool_argument_string(self):
        """Test string argument validation."""
        manager = ToolManager()
        schema = {"type": "string"}

        # Valid string
        error = manager._validate_tool_argument("name", "test", schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("name", 123, schema)
        assert "must be a string" in error

    def test_validate_tool_argument_integer(self):
        """Test integer argument validation."""
        manager = ToolManager()
        schema = {"type": "integer"}

        # Valid integer
        error = manager._validate_tool_argument("count", 5, schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("count", "5", schema)
        assert "must be an integer" in error

    def test_validate_tool_argument_number(self):
        """Test number argument validation."""
        manager = ToolManager()
        schema = {"type": "number"}

        # Valid integer
        error = manager._validate_tool_argument("value", 5, schema)
        assert error is None

        # Valid float
        error = manager._validate_tool_argument("value", 5.5, schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("value", "5.5", schema)
        assert "must be a number" in error

    def test_validate_tool_argument_boolean(self):
        """Test boolean argument validation."""
        manager = ToolManager()
        schema = {"type": "boolean"}

        # Valid boolean
        error = manager._validate_tool_argument("enabled", True, schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("enabled", "true", schema)
        assert "must be a boolean" in error

    def test_validate_tool_argument_array(self):
        """Test array argument validation."""
        manager = ToolManager()
        schema = {"type": "array"}

        # Valid array
        error = manager._validate_tool_argument("items", [1, 2, 3], schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("items", "not_array", schema)
        assert "must be an array" in error

    def test_validate_tool_argument_object(self):
        """Test object argument validation."""
        manager = ToolManager()
        schema = {"type": "object"}

        # Valid object
        error = manager._validate_tool_argument("config", {"key": "value"}, schema)
        assert error is None

        # Invalid type
        error = manager._validate_tool_argument("config", "not_object", schema)
        assert "must be an object" in error


@pytest.mark.unit
class TestToolManagerToolCalling:
    """Test tool calling functionality."""

    @patch("mcp_template.common.template_manager.TemplateManager")
    def test_call_tool_success(self, mock_template_manager_class):
        """Test successful tool calling."""
        mock_template_manager = Mock()
        mock_template_manager_class.return_value = mock_template_manager
        mock_template_manager.get_template.return_value = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "discover_tools") as mock_discover:
            mock_discover.return_value = {"tools": SAMPLE_TOOL_DATA["demo"]["tools"]}

            with patch.object(ToolManager, "validate_tool_call") as mock_validate:
                mock_validate.return_value = {"valid": True, "errors": []}

                manager = ToolManager()
                result = manager.call_tool(
                    template_name="demo",
                    tool_name="echo",
                    tool_args={"message": "Hello"},
                )

                assert result["success"] is True

    @patch("mcp_template.common.template_manager.TemplateManager")
    def test_call_tool_template_not_found(self, mock_template_manager_class):
        """Test tool calling when template is not found."""
        mock_template_manager = Mock()
        mock_template_manager_class.return_value = mock_template_manager
        mock_template_manager.get_template.return_value = None

        manager = ToolManager()
        result = manager.call_tool(
            template_name="nonexistent", tool_name="echo", tool_args={}
        )

        assert result["success"] is False
        assert "Template 'nonexistent' not found" in result["error"]

    def test_call_tool_with_provided_config(self):
        """Test tool calling with provided template config."""
        template_config = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "discover_tools") as mock_discover:
            mock_discover.return_value = {"tools": SAMPLE_TOOL_DATA["demo"]["tools"]}

            with patch.object(ToolManager, "validate_tool_call") as mock_validate:
                mock_validate.return_value = {"valid": True, "errors": []}

                manager = ToolManager()
                result = manager.call_tool(
                    template_name="demo",
                    tool_name="echo",
                    tool_args={"message": "Hello"},
                    template_config=template_config,
                )

                assert result["success"] is True

    def test_call_tool_validation_failure(self):
        """Test tool calling with validation failure."""
        template_config = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "discover_tools") as mock_discover:
            mock_discover.return_value = {"tools": SAMPLE_TOOL_DATA["demo"]["tools"]}

            with patch.object(ToolManager, "validate_tool_call") as mock_validate:
                mock_validate.return_value = {
                    "valid": False,
                    "errors": ["Missing required argument: message"],
                }

                manager = ToolManager()
                result = manager.call_tool(
                    template_name="demo",
                    tool_name="echo",
                    tool_args={},
                    template_config=template_config,
                )

                assert result["success"] is False
                assert result["error"] == "Validation failed"
                assert "Missing required argument" in result["validation_errors"][0]

    def test_call_tool_exception_handling(self):
        """Test exception handling in tool calling."""
        with patch.object(ToolManager, "discover_tools") as mock_discover:
            mock_discover.side_effect = Exception("Discovery failed")

            manager = ToolManager()
            result = manager.call_tool(
                template_name="demo", tool_name="echo", tool_args={}, template_config={}
            )

            assert result["success"] is False
            assert "Discovery failed" in result["error"]


@pytest.mark.unit
class TestToolManagerUtilities:
    """Test utility methods of ToolManager."""

    def test_get_tool_schema_found(self):
        """Test getting tool schema when tool exists."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]

        manager = ToolManager()
        schema = manager.get_tool_schema("echo", tools)

        assert schema is not None
        assert "properties" in schema
        assert "message" in schema["properties"]

    def test_get_tool_schema_not_found(self):
        """Test getting tool schema when tool doesn't exist."""
        tools = SAMPLE_TOOL_DATA["demo"]["tools"]

        manager = ToolManager()
        schema = manager.get_tool_schema("nonexistent", tools)

        assert schema is None

    def test_format_tool_for_display_complete(self):
        """Test formatting tool with complete information."""
        tool = SAMPLE_TOOL_DATA["demo"]["tools"][0]

        manager = ToolManager()
        formatted = manager.format_tool_for_display(tool)

        assert formatted["name"] == "echo"
        assert "Echo back" in formatted["description"]
        assert "1 parameters (1 required)" in formatted["parameters"]
        assert formatted["category"] == "utility"

    def test_format_tool_for_display_minimal(self):
        """Test formatting tool with minimal information."""
        tool = {"name": "simple_tool"}

        manager = ToolManager()
        formatted = manager.format_tool_for_display(tool)

        assert formatted["name"] == "simple_tool"
        assert formatted["description"] == "No description"
        assert formatted["parameters"] == "No parameters"
        assert formatted["category"] == "general"

    def test_format_tool_for_display_no_required_params(self):
        """Test formatting tool with optional parameters only."""
        tool = {
            "name": "optional_tool",
            "inputSchema": {
                "properties": {"opt1": {"type": "string"}, "opt2": {"type": "integer"}}
            },
        }

        manager = ToolManager()
        formatted = manager.format_tool_for_display(tool)

        assert "2 parameters" in formatted["parameters"]
        assert "required" not in formatted["parameters"]

    def test_get_cache_stats_empty(self):
        """Test cache stats when cache is empty."""
        manager = ToolManager()
        stats = manager.get_cache_stats()

        assert stats["cache_size"] == 0
        assert stats["cached_templates"] == []

    def test_get_cache_stats_with_data(self):
        """Test cache stats with cached data."""
        manager = ToolManager()
        manager._cache["demo_static_123"] = {"tools": []}
        manager._cache["filesystem_docker_456"] = {"tools": []}

        stats = manager.get_cache_stats()

        assert stats["cache_size"] == 2
        assert set(stats["cached_templates"]) == {"demo", "filesystem"}


@pytest.mark.integration
class TestToolManagerIntegration:
    """Integration tests for ToolManager."""

    def test_full_discovery_workflow(self):
        """Test complete tool discovery workflow."""
        template_config = {
            "name": "test-template",
            "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
        }

        with patch(
            "mcp_template.common.template_manager.TemplateManager"
        ) as mock_tm_class:
            mock_tm = Mock()
            mock_tm_class.return_value = mock_tm
            mock_tm.get_template.return_value = template_config

            with patch.object(ToolManager, "_discover_tools_static") as mock_static:
                mock_static.return_value = {
                    "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
                    "discovery_method": "static",
                }

                manager = ToolManager()

                # Discover tools
                discovery_result = manager.discover_tools(
                    template_name="test-template",
                    template_config=template_config,
                    discovery_method="static",
                )

                # List tools
                tools = manager.list_tools("test-template")

                # Validate tool call
                validation = manager.validate_tool_call(
                    "echo", {"message": "test"}, tools
                )

                # Call tool
                call_result = manager.call_tool(
                    template_name="test-template",
                    tool_name="echo",
                    tool_args={"message": "test"},
                    template_config=template_config,
                )

                # Assertions
                assert len(discovery_result["tools"]) == 1
                assert len(tools) == 1
                assert validation["valid"] is True
                assert call_result["success"] is True

    def test_error_recovery_workflow(self):
        """Test error recovery in tool operations."""
        manager = ToolManager()

        # Test discovery error recovery
        with patch.object(manager, "_discover_tools_static") as mock_static:
            mock_static.side_effect = Exception("Static discovery failed")

            result = manager.discover_tools(
                template_name="test", template_config={}, discovery_method="static"
            )

            assert result["tools"] == []
            assert "error" in result

        # Test list tools error recovery
        with patch(
            "mcp_template.common.template_manager.TemplateManager"
        ) as mock_tm_class:
            mock_tm_class.side_effect = Exception("Template manager failed")

            tools = manager.list_tools("test")
            assert tools == []


@pytest.mark.docker
class TestToolManagerDockerIntegration:
    """Docker-specific integration tests."""

    @patch("mcp_template.common.tool_manager.DockerProbe")
    def test_docker_discovery_with_env_vars(self, mock_docker_probe_class):
        """Test Docker discovery with environment variables."""
        mock_probe = Mock()
        mock_docker_probe_class.return_value = mock_probe
        mock_probe.discover_tools_from_image.return_value = {
            "tools": SAMPLE_TOOL_DATA["demo"]["tools"]
        }

        template_config = {
            "docker_image": "test-image",
            "docker_tag": "v1.0",
            "env_vars": {"API_KEY": "secret", "DEBUG": "true"},
        }

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="test",
            template_config=template_config,
            discovery_method="docker",
        )

        # Verify Docker probe was called with correct arguments
        mock_probe.discover_tools_from_image.assert_called_once_with(
            "test-image:v1.0", ["--env", "API_KEY=secret", "--env", "DEBUG=true"]
        )

        assert result["discovery_method"] == "docker"
        assert len(result["tools"]) == 1

    @patch("mcp_template.common.tool_manager.DockerProbe")
    def test_docker_discovery_failure_handling(self, mock_docker_probe_class):
        """Test Docker discovery failure handling."""
        mock_probe = Mock()
        mock_docker_probe_class.return_value = mock_probe
        mock_probe.discover_tools_from_image.return_value = None

        template_config = {"docker_image": "nonexistent-image", "docker_tag": "latest"}

        manager = ToolManager()
        result = manager.discover_tools(
            template_name="test",
            template_config=template_config,
            discovery_method="docker",
        )

        assert result["discovery_method"] == "docker"
        assert result["tools"] == []
        assert "Failed to discover tools" in result["error"]


@pytest.mark.slow
class TestToolManagerPerformance:
    """Performance tests for ToolManager."""

    def test_large_tool_list_validation(self):
        """Test validation performance with large tool lists."""
        import time

        # Create large tool list
        large_tool_list = []
        for i in range(100):
            large_tool_list.append(
                {
                    "name": f"tool_{i}",
                    "description": f"Tool number {i}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string"},
                            "param2": {"type": "integer"},
                        },
                        "required": ["param1"],
                    },
                }
            )

        manager = ToolManager()

        start_time = time.time()
        result = manager.validate_tool_call(
            "tool_50", {"param1": "test"}, large_tool_list
        )
        elapsed_time = time.time() - start_time

        assert result["valid"] is True
        assert elapsed_time < 1.0  # Should complete within 1 second

    def test_cache_performance(self):
        """Test cache performance with multiple discoveries."""
        import time

        template_config = SAMPLE_TEMPLATE_DATA["demo"]

        with patch.object(ToolManager, "_discover_tools_static") as mock_static:
            mock_static.return_value = {
                "tools": SAMPLE_TOOL_DATA["demo"]["tools"],
                "discovery_method": "static",
            }

            manager = ToolManager()

            # Time multiple discoveries with cache
            start_time = time.time()
            for i in range(10):
                manager.discover_tools(
                    template_name="demo",
                    template_config=template_config,
                    discovery_method="static",
                    use_cache=True,
                )
            elapsed_time = time.time() - start_time

            # Should only call the actual discovery once
            mock_static.assert_called_once()
            assert elapsed_time < 0.1  # Should be very fast due to caching
