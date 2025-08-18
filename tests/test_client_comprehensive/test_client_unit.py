"""
Comprehensive unit tests for MCPClient.

This module contains extensive unit tests for all MCPClient methods,
including edge cases, error conditions, and integration scenarios.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.client import MCPClient


@pytest.mark.unit
@pytest.mark.docker
class TestMCPClientInitialization:
    """Test client initialization and configuration."""

    def test_default_initialization(self):
        """Test client initialization with default parameters."""
        client = MCPClient()
        assert client.backend_type == "docker"
        assert client.timeout == 30
        assert client.template_manager is not None
        assert client.deployment_manager is not None
        assert client.tool_manager is not None

    def test_custom_initialization(self):
        """Test client initialization with custom parameters."""
        client = MCPClient(backend_type="mock", timeout=60)
        assert client.backend_type == "mock"
        assert client.timeout == 60

    def test_invalid_backend_initialization(self):
        """Test client raises ValueError for invalid backend types."""
        # Should raise ValueError for unsupported backend types
        with pytest.raises(ValueError, match="Unsupported backend type: nonexistent"):
            MCPClient(backend_type="nonexistent")


@pytest.mark.unit
class TestMCPClientTemplates:
    """Test template management methods."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.client = MCPClient(backend_type="mock")
        self.mock_template_manager = Mock()
        self.client.template_manager = self.mock_template_manager

    def test_list_templates_success(self):
        """Test successful template listing."""
        expected_templates = {
            "demo": {"name": "demo", "description": "Demo template"},
            "github": {"name": "github", "description": "GitHub template"},
        }
        self.mock_template_manager.list_templates.return_value = expected_templates

        result = self.client.list_templates()

        assert result == expected_templates
        self.mock_template_manager.list_templates.assert_called_once_with(
            include_deployed_status=False
        )

    def test_list_templates_with_deployed_status(self):
        """Test template listing with deployment status."""
        expected_templates = {
            "demo": {"name": "demo", "deployed": True},
            "github": {"name": "github", "deployed": False},
        }
        self.mock_template_manager.list_templates.return_value = expected_templates

        result = self.client.list_templates(include_deployed_status=True)

        assert result == expected_templates
        self.mock_template_manager.list_templates.assert_called_once_with(
            include_deployed_status=True
        )

    def test_list_templates_error(self):
        """Test template listing error handling."""
        self.mock_template_manager.list_templates.side_effect = Exception(
            "Template error"
        )

        result = self.client.list_templates()

        assert result == {}

    def test_get_template_info_success(self):
        """Test successful template info retrieval."""
        expected_info = {"name": "demo", "description": "Demo template"}
        self.mock_template_manager.get_template_info.return_value = expected_info

        result = self.client.get_template_info("demo")

        assert result == expected_info
        self.mock_template_manager.get_template_info.assert_called_once_with("demo")

    def test_get_template_info_not_found(self):
        """Test template info retrieval for non-existent template."""
        self.mock_template_manager.get_template_info.return_value = None

        result = self.client.get_template_info("nonexistent")

        assert result is None

    def test_get_template_info_error(self):
        """Test template info retrieval error handling."""
        self.mock_template_manager.get_template_info.side_effect = Exception(
            "Info error"
        )

        result = self.client.get_template_info("demo")

        assert result is None

    def test_validate_template_success(self):
        """Test successful template validation."""
        self.mock_template_manager.validate_template.return_value = True

        result = self.client.validate_template("demo")

        assert result is True
        self.mock_template_manager.validate_template.assert_called_once_with("demo")

    def test_validate_template_invalid(self):
        """Test validation of invalid template."""
        self.mock_template_manager.validate_template.return_value = False

        result = self.client.validate_template("invalid")

        assert result is False

    def test_validate_template_error(self):
        """Test template validation error handling."""
        self.mock_template_manager.validate_template.side_effect = Exception(
            "Validation error"
        )

        result = self.client.validate_template("demo")

        assert result is False

    def test_search_templates_success(self):
        """Test successful template search."""
        expected_results = {"demo": {"name": "demo", "score": 1.0}}
        self.mock_template_manager.search_templates.return_value = expected_results

        result = self.client.search_templates("demo")

        assert result == expected_results
        self.mock_template_manager.search_templates.assert_called_once_with("demo")

    def test_search_templates_no_results(self):
        """Test template search with no results."""
        self.mock_template_manager.search_templates.return_value = {}

        result = self.client.search_templates("nonexistent")

        assert result == {}

    def test_search_templates_error(self):
        """Test template search error handling."""
        self.mock_template_manager.search_templates.side_effect = Exception(
            "Search error"
        )

        result = self.client.search_templates("demo")

        assert result == {}

    def test_get_template_info_edge_cases(self):
        """Test edge cases for template info retrieval."""
        # Configure mock to return None for edge cases
        self.mock_template_manager.get_template_info.return_value = None

        # Test None input
        result = self.client.get_template_info(None)
        assert result is None

        # Test empty string
        result = self.client.get_template_info("")
        assert result is None

        # Test very long string
        long_name = "x" * 10000
        result = self.client.get_template_info(long_name)
        assert result is None


@pytest.mark.unit
class TestMCPClientServers:
    """Test server management methods."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.client = MCPClient(backend_type="mock")
        self.mock_deployment_manager = Mock()
        self.client.deployment_manager = self.mock_deployment_manager

    def test_list_servers_success(self):
        """Test successful server listing."""
        expected_servers = [
            {"id": "server1", "template": "demo", "status": "running"},
            {"id": "server2", "template": "github", "status": "stopped"},
        ]
        self.mock_deployment_manager.find_deployments_by_criteria.return_value = (
            expected_servers
        )

        result = self.client.list_servers()

        assert result == expected_servers
        self.mock_deployment_manager.find_deployments_by_criteria.assert_called_once_with(
            template_name=None
        )

    def test_list_servers_error(self):
        """Test server listing error handling."""
        self.mock_deployment_manager.find_deployments_by_criteria.side_effect = (
            Exception("List error")
        )

        result = self.client.list_servers()

        assert result == []

    def test_list_servers_by_template_success(self):
        """Test successful server listing by template."""
        expected_servers = [{"id": "server1", "template": "demo", "status": "running"}]
        self.mock_deployment_manager.find_deployments_by_criteria.return_value = (
            expected_servers
        )

        result = self.client.list_servers_by_template("demo")

        assert result == expected_servers
        self.mock_deployment_manager.find_deployments_by_criteria.assert_called_with(
            template_name="demo"
        )

    def test_start_server_success(self):
        """Test successful server start."""
        config = {"greeting": "Hello"}
        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            "deployment_id": "server123",
            "status": "deployed",
        }
        self.mock_deployment_manager.deploy_template.return_value = mock_result

        result = self.client.start_server("demo", config)

        assert result == {"deployment_id": "server123", "status": "deployed"}

    def test_start_server_failure(self):
        """Test server start failure."""
        config = {"greeting": "Hello"}
        mock_result = Mock()
        mock_result.success = False
        self.mock_deployment_manager.deploy_template.return_value = mock_result

        result = self.client.start_server("demo", config)

        assert result is None

    def test_start_server_error(self):
        """Test server start error handling."""
        config = {"greeting": "Hello"}
        self.mock_deployment_manager.deploy_template.side_effect = Exception(
            "Deploy error"
        )

        result = self.client.start_server("demo", config)

        assert result is None

    def test_stop_server_success(self):
        """Test successful server stop."""
        expected_result = {"success": True, "message": "Stopped"}
        self.mock_deployment_manager.stop_deployment.return_value = expected_result

        result = self.client.stop_server("server123")

        assert result == expected_result
        self.mock_deployment_manager.stop_deployment.assert_called_once_with(
            "server123", 30
        )

    def test_stop_server_failure(self):
        """Test server stop failure."""
        expected_result = {"success": False, "error": "Not found"}
        self.mock_deployment_manager.stop_deployment.return_value = expected_result

        result = self.client.stop_server("invalid_server")

        assert result == expected_result

    def test_get_server_info_success(self):
        """Test successful server info retrieval."""
        expected_info = {"id": "server123", "status": "running", "template": "demo"}
        self.mock_deployment_manager.find_deployments_by_criteria.return_value = [
            expected_info
        ]

        result = self.client.get_server_info("server123")

        assert result == expected_info

    def test_get_server_info_not_found(self):
        """Test server info retrieval for non-existent server."""
        self.mock_deployment_manager.find_deployments_by_criteria.return_value = []

        result = self.client.get_server_info("nonexistent")

        assert result is None

    def test_get_server_logs_success(self):
        """Test successful server log retrieval."""
        expected_logs = "Log line 1\nLog line 2\nLog line 3"
        self.mock_deployment_manager.get_deployment_logs.return_value = {
            "success": True,
            "logs": expected_logs,
        }

        result = self.client.get_server_logs("server123")

        assert result == expected_logs
        self.mock_deployment_manager.get_deployment_logs.assert_called_once_with(
            "server123", lines=100, follow=False
        )

    def test_get_server_logs_with_params(self):
        """Test server log retrieval with custom parameters."""
        expected_logs = "Recent logs"
        self.mock_deployment_manager.get_deployment_logs.return_value = {
            "success": True,
            "logs": expected_logs,
        }

        result = self.client.get_server_logs("server123", lines=50, follow=True)

        assert result == expected_logs
        self.mock_deployment_manager.get_deployment_logs.assert_called_once_with(
            "server123", lines=50, follow=True
        )


@pytest.mark.unit
class TestMCPClientTools:
    """Test tool management methods."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.client = MCPClient(backend_type="mock")
        self.mock_tool_manager = Mock()
        self.client.tool_manager = self.mock_tool_manager

    def test_list_tools_success(self):
        """Test successful tool listing."""
        expected_tools = [
            {"name": "echo", "description": "Echo tool"},
            {"name": "hello", "description": "Hello tool"},
        ]
        # Tool manager now returns new format
        mock_response = {
            "tools": expected_tools,
            "discovery_method": "static",
            "metadata": {"hints": "Tools found in static configuration"},
        }
        self.mock_tool_manager.list_tools.return_value = mock_response

        result = self.client.list_tools("demo")

        # Client should return just the tools list for backward compatibility
        assert result == expected_tools
        self.mock_tool_manager.list_tools.assert_called_once_with(
            "demo",
            discovery_method="auto",
            force_refresh=False,
        )

    def test_list_tools_with_params(self):
        """Test tool listing with custom parameters."""
        expected_tools = [{"name": "echo", "description": "Echo tool"}]
        # Tool manager now returns new format
        mock_response = {
            "tools": expected_tools,
            "discovery_method": "static",
            "metadata": {"hints": "Tools found in static configuration"},
        }
        self.mock_tool_manager.list_tools.return_value = mock_response

        result = self.client.list_tools(
            "demo",
            discovery_method="static",
            force_refresh=True,
            force_server_discovery=True,
        )

        # Client should return just the tools list for backward compatibility
        assert result == expected_tools
        self.mock_tool_manager.list_tools.assert_called_once_with(
            "demo",
            discovery_method="static",
            force_refresh=True,
        )

    def test_list_tools_error(self):
        """Test tool listing error handling."""
        self.mock_tool_manager.list_tools.side_effect = Exception("Tool error")

        result = self.client.list_tools("demo")

        assert result == []

    def test_list_tools_with_metadata(self):
        """Test tool listing with metadata included."""
        expected_tools = [{"name": "echo", "description": "Echo tool"}]
        mock_response = {
            "tools": expected_tools,
            "discovery_method": "stdio",
            "metadata": {
                "hints": "Tools discovered via stdio communication",
                "server_status": "running",
            },
        }
        self.mock_tool_manager.list_tools.return_value = mock_response

        result = self.client.list_tools("demo", include_metadata=True)

        # Should return full metadata structure
        assert result == mock_response
        self.mock_tool_manager.list_tools.assert_called_once_with(
            "demo",
            discovery_method="auto",
            force_refresh=False,
        )

    def test_call_tool_success(self):
        """Test successful tool calling."""
        expected_result = {"success": True, "result": {"output": "Hello World"}}
        self.mock_tool_manager.call_tool.return_value = expected_result

        result = self.client.call_tool("demo", "echo", {"message": "Hello World"})

        assert result == expected_result
        self.mock_tool_manager.call_tool.assert_called_once_with(
            "demo", "echo", {"message": "Hello World"}, 30
        )

    def test_call_tool_error(self):
        """Test tool calling error handling."""
        self.mock_tool_manager.call_tool.side_effect = Exception("Call error")

        result = self.client.call_tool("demo", "echo", {"message": "Hello"})

        assert result is None

    def test_call_tool_with_defaults(self):
        """Test tool calling with default arguments."""
        expected_result = {"success": True, "result": {}}
        self.mock_tool_manager.call_tool.return_value = expected_result

        result = self.client.call_tool("demo", "hello")

        assert result == expected_result
        self.mock_tool_manager.call_tool.assert_called_once_with(
            "demo", "hello", {}, 30
        )


@pytest.mark.unit
class TestMCPClientConnections:
    """Test connection management methods."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.client = MCPClient(backend_type="mock")
        # The client has _active_connections, not connections
        self.client._active_connections = {}

    @pytest.mark.asyncio
    async def test_connect_stdio_success(self):
        """Test successful stdio connection."""
        mock_connection = AsyncMock()

        with patch("mcp_template.client.MCPConnection") as mock_conn_class:
            mock_conn_class.return_value = mock_connection
            mock_connection.connect_stdio.return_value = True

            result = await self.client.connect_stdio(["echo", "test"])

            # The connection_id is auto-generated as stdio_0 for first connection
            assert result == "stdio_0"
            assert "stdio_0" in self.client._active_connections

    @pytest.mark.asyncio
    async def test_connect_stdio_failure(self):
        """Test stdio connection failure."""
        mock_connection = AsyncMock()

        with patch("mcp_template.client.MCPConnection") as mock_conn_class:
            mock_conn_class.return_value = mock_connection
            mock_connection.connect_stdio.return_value = False

            result = await self.client.connect_stdio(["invalid_command"])

            assert result is None

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        """Test successful disconnection."""
        mock_connection = AsyncMock()
        self.client._active_connections["conn123"] = mock_connection

        result = await self.client.disconnect("conn123")

        assert result is True
        assert "conn123" not in self.client._active_connections
        mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self):
        """Test disconnection of non-existent connection."""
        result = await self.client.disconnect("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_tools_from_connection_success(self):
        """Test successful tool listing from connection."""
        mock_connection = AsyncMock()
        mock_connection.list_tools.return_value = [{"name": "test_tool"}]
        self.client._active_connections["conn123"] = mock_connection

        result = await self.client.list_tools_from_connection("conn123")

        assert result == [{"name": "test_tool"}]

    @pytest.mark.asyncio
    async def test_list_tools_from_connection_not_found(self):
        """Test tool listing from non-existent connection."""
        result = await self.client.list_tools_from_connection("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_call_tool_from_connection_success(self):
        """Test successful tool calling from connection."""
        mock_connection = AsyncMock()
        mock_connection.call_tool.return_value = {"result": "success"}
        self.client._active_connections["conn123"] = mock_connection

        result = await self.client.call_tool_from_connection(
            "conn123", "test_tool", {"arg": "value"}
        )

        assert result == {"result": "success"}
        mock_connection.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_from_connection_not_found(self):
        """Test tool calling from non-existent connection."""
        result = await self.client.call_tool_from_connection("nonexistent", "tool", {})

        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_connections(self):
        """Test connection cleanup."""
        mock_conn1 = AsyncMock()
        mock_conn2 = AsyncMock()
        self.client._active_connections = {"conn1": mock_conn1, "conn2": mock_conn2}

        await self.client.cleanup()

        assert len(self.client._active_connections) == 0
        mock_conn1.disconnect.assert_called_once()
        mock_conn2.disconnect.assert_called_once()


@pytest.mark.unit
class TestMCPClientContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """Test successful context manager usage."""
        async with MCPClient(backend_type="mock") as client:
            assert isinstance(client, MCPClient)
            assert client.backend_type == "mock"

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test context manager cleanup."""
        client = MCPClient(backend_type="mock")

        # Add a mock connection
        mock_connection = AsyncMock()
        client._active_connections["test"] = mock_connection

        async with client:
            assert "test" in client._active_connections

        # Should be cleaned up after exiting context
        assert len(client._active_connections) == 0
        mock_connection.disconnect.assert_called_once()


@pytest.mark.unit
class TestMCPClientEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test client."""
        self.client = MCPClient(backend_type="mock")
        # Mock the template manager for consistent edge case testing
        self.mock_template_manager = Mock()
        self.client.template_manager = self.mock_template_manager

        # Configure mocks to return None/empty for edge cases
        self.mock_template_manager.get_template_info.return_value = None
        self.mock_template_manager.validate_template.return_value = False
        self.mock_template_manager.search_templates.return_value = {}

    def test_none_inputs(self):
        """Test handling of None inputs."""
        # Most methods should handle None gracefully
        assert self.client.get_template_info(None) is None
        assert self.client.validate_template(None) is False
        assert self.client.search_templates(None) == {}

    def test_empty_string_inputs(self):
        """Test handling of empty string inputs."""
        assert self.client.get_template_info("") is None
        assert self.client.validate_template("") is False
        assert self.client.search_templates("") == {}

    def test_very_long_inputs(self):
        """Test handling of very long string inputs."""
        long_string = "x" * 10000
        assert self.client.get_template_info(long_string) is None
        assert self.client.validate_template(long_string) is False

    def test_special_character_inputs(self):
        """Test handling of special character inputs."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        assert self.client.get_template_info(special_chars) is None
        assert self.client.validate_template(special_chars) is False

    def test_clear_caches(self):
        """Test cache clearing functionality."""
        mock_tool_manager = Mock()
        self.client.tool_manager = mock_tool_manager

        self.client.clear_caches()

        mock_tool_manager.clear_cache.assert_called_once()


@pytest.mark.unit
@pytest.mark.integration
class TestMCPClientIntegration:
    """Integration tests for client functionality."""

    def test_complete_workflow(self):
        """Test a complete workflow using the client."""
        client = MCPClient(backend_type="mock")

        # Mock all managers
        client.template_manager = Mock()
        client.deployment_manager = Mock()
        client.tool_manager = Mock()

        # Set up mock responses
        client.template_manager.list_templates.return_value = {"demo": {"name": "demo"}}
        client.template_manager.get_template_info.return_value = {
            "name": "demo",
            "description": "Demo",
        }
        client.template_manager.validate_template.return_value = True

        mock_deploy_result = Mock()
        mock_deploy_result.success = True
        mock_deploy_result.to_dict.return_value = {
            "deployment_id": "demo123",
            "status": "deployed",
        }
        client.deployment_manager.deploy_template.return_value = mock_deploy_result

        client.tool_manager.list_tools.return_value = {
            "tools": [{"name": "echo", "description": "Echo tool"}],
            "discovery_method": "static",
            "metadata": {"hints": "Tools found in static configuration"},
        }
        client.tool_manager.call_tool.return_value = {
            "success": True,
            "result": {"output": "Hello"},
        }

        # Mock stop_deployment to return a dictionary directly
        client.deployment_manager.stop_deployment.return_value = {
            "success": True,
            "message": "Stopped",
        }

        # Execute workflow
        templates = client.list_templates()
        assert "demo" in templates

        template_info = client.get_template_info("demo")
        assert template_info["name"] == "demo"

        is_valid = client.validate_template("demo")
        assert is_valid is True

        server_result = client.start_server("demo", {"greeting": "Test"})
        assert server_result["deployment_id"] == "demo123"

        tools = client.list_tools("demo")
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"

        tool_result = client.call_tool("demo", "echo", {"message": "Hello"})
        assert tool_result["success"] is True
        assert tool_result["result"]["output"] == "Hello"

        stop_result = client.stop_server("demo123")
        assert stop_result["success"] is True


@pytest.mark.unit
class TestMCPClientConfigurationHandling:
    """Test the new configuration handling features in MCPClient."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.client = MCPClient(backend_type="mock")

    @patch("mcp_template.client.DeploymentManager")
    def test_deploy_template_with_config_precedence(
        self, mock_deployment_manager_class
    ):
        """Test that deploy_template handles config precedence correctly."""
        # Setup mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        # Test config precedence
        result = self.client.deploy_template(
            template_id="demo",
            config_file="/path/to/config.json",
            config={"key1": "from_cli", "key2": "cli_value"},
            env_vars={"key1": "from_env"},  # Should override CLI config
        )

        assert result is not None
        assert result["success"] is True

        # Verify deployment manager was called with correct config sources
        mock_deployment_manager.deploy_template.assert_called_once()
        call_args = mock_deployment_manager.deploy_template.call_args[0]

        template_id = call_args[0]
        config_sources = call_args[1]

        assert template_id == "demo"
        assert "config_file" in config_sources
        assert "config_values" in config_sources
        assert "env_vars" in config_sources
        assert config_sources["config_file"] == "/path/to/config.json"
        assert config_sources["config_values"]["key1"] == "from_cli"
        assert config_sources["env_vars"]["key1"] == "from_env"

    @patch("mcp_template.client.DeploymentManager")
    def test_deploy_template_with_volumes_dict(self, mock_deployment_manager_class):
        """Test that deploy_template handles volume dict correctly."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        volumes = {"./host/path": "/container/path", "./data": "/app/data"}

        result = self.client.deploy_template(template_id="demo", volumes=volumes)

        assert result is not None
        mock_deployment_manager.deploy_template.assert_called_once()

        call_args = mock_deployment_manager.deploy_template.call_args[0]
        config_sources = call_args[1]

        assert "config_values" in config_sources
        assert "VOLUMES" in config_sources["config_values"]
        assert config_sources["config_values"]["VOLUMES"] == volumes

    @patch("mcp_template.client.DeploymentManager")
    def test_deploy_template_with_volumes_json_object(
        self, mock_deployment_manager_class
    ):
        """Test that deploy_template handles JSON object volumes correctly."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        volumes_json = '{"./host": "/container", "./data": "/app/data"}'

        result = self.client.deploy_template(template_id="demo", volumes=volumes_json)

        assert result is not None

        call_args = mock_deployment_manager.deploy_template.call_args[0]
        config_sources = call_args[1]

        assert "config_values" in config_sources
        assert "VOLUMES" in config_sources["config_values"]
        volumes = config_sources["config_values"]["VOLUMES"]
        assert volumes["./host"] == "/container"
        assert volumes["./data"] == "/app/data"

    @patch("mcp_template.client.DeploymentManager")
    def test_deploy_template_with_volumes_json_array(
        self, mock_deployment_manager_class
    ):
        """Test that deploy_template handles JSON array volumes correctly."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        volumes_json = '["/host/path1", "/host/path2"]'

        result = self.client.deploy_template(template_id="demo", volumes=volumes_json)

        assert result is not None

        call_args = mock_deployment_manager.deploy_template.call_args[0]
        config_sources = call_args[1]

        volumes = config_sources["config_values"]["VOLUMES"]
        # Array format maps paths to themselves
        assert volumes["/host/path1"] == "/host/path1"
        assert volumes["/host/path2"] == "/host/path2"

    @patch("mcp_template.client.DeploymentManager")
    def test_deploy_template_with_invalid_volumes_json(
        self, mock_deployment_manager_class
    ):
        """Test that deploy_template handles invalid JSON volumes gracefully."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        result = self.client.deploy_template(
            template_id="demo", volumes='{"invalid": json}'  # Invalid JSON
        )

        # Should return None on failure
        assert result is None

    @patch("mcp_template.client.DeploymentManager")
    def test_start_server_backward_compatibility(self, mock_deployment_manager_class):
        """Test that start_server maintains backward compatibility."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        # Test old interface still works
        result = self.client.start_server(
            template_id="demo",
            configuration={"key": "value"},
            pull_image=False,
            transport="http",
        )

        assert result is not None
        assert result["success"] is True

        # Verify backward compatibility - old configuration parameter should work
        call_args = mock_deployment_manager.deploy_template.call_args[0]
        config_sources = call_args[1]

        assert "config_values" in config_sources
        assert config_sources["config_values"]["key"] == "value"

    @patch("mcp_template.client.DeploymentManager")
    def test_start_server_with_all_new_features(self, mock_deployment_manager_class):
        """Test start_server with all new configuration features."""
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"deployment_id": "test123", "success": True}
        mock_deployment_manager.deploy_template.return_value = mock_result

        result = self.client.start_server(
            template_id="demo",
            configuration={"cli_key": "cli_value"},
            config_file="/path/to/config.json",
            env_vars={"ENV_KEY": "env_value"},
            volumes={"./host": "/container"},
            transport="http",
            pull_image=True,
            name="custom-deployment",
        )

        assert result is not None

        call_args = mock_deployment_manager.deploy_template.call_args[0]
        config_sources = call_args[1]
        deployment_options = call_args[2]

        # Verify all config sources are present
        assert config_sources["config_file"] == "/path/to/config.json"
        assert config_sources["config_values"]["cli_key"] == "cli_value"
        assert config_sources["env_vars"]["ENV_KEY"] == "env_value"
        assert config_sources["config_values"]["VOLUMES"]["./host"] == "/container"

        # Verify deployment options
        assert deployment_options.name == "custom-deployment"
        assert deployment_options.transport == "http"
        assert deployment_options.pull_image is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
