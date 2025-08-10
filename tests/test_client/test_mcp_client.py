"""Unit tests for MCP Client functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mcp_template.client import MCPClient


@pytest.mark.unit
class TestMCPClient:
    """Test cases for the MCPClient class."""

    @pytest.fixture
    def mock_managers(self):
        """Mock the internal managers."""
        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager") as mock_tool_manager,
            patch("mcp_template.client.TemplateDiscovery") as mock_template_discovery,
        ):

            # Setup mock instances
            mock_server_mgr = Mock()
            mock_tool_mgr = Mock()
            mock_template_disc = Mock()

            mock_server_manager.return_value = mock_server_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_discovery.return_value = mock_template_disc

            yield {
                "server_manager": mock_server_mgr,
                "tool_manager": mock_tool_mgr,
                "template_discovery": mock_template_disc,
            }

    def test_client_initialization(self, mock_managers):
        """Test client initialization with default parameters."""
        client = MCPClient()

        assert client.backend_type == "docker"
        assert client.timeout == 30
        assert client._active_connections == {}

    def test_client_initialization_with_custom_params(self, mock_managers):
        """Test client initialization with custom parameters."""
        client = MCPClient(backend_type="kubernetes", timeout=60)

        assert client.backend_type == "kubernetes"
        assert client.timeout == 60

    def test_list_templates(self, mock_managers):
        """Test listing available templates."""
        client = MCPClient()

        # Mock template data
        expected_templates = {
            "demo": {"name": "Demo Template", "version": "1.0.0"},
            "filesystem": {"name": "Filesystem Template", "version": "1.0.0"},
        }
        mock_managers["server_manager"].list_available_templates.return_value = (
            expected_templates
        )

        result = client.list_templates()

        assert result == expected_templates
        mock_managers["server_manager"].list_available_templates.assert_called_once()

    def test_get_template_info(self, mock_managers):
        """Test getting template information."""
        client = MCPClient()

        expected_info = {"name": "Demo Template", "version": "1.0.0"}
        mock_managers["server_manager"].get_template_info.return_value = expected_info

        result = client.get_template_info("demo")

        assert result == expected_info
        mock_managers["server_manager"].get_template_info.assert_called_once_with(
            "demo"
        )

    def test_get_template_info_not_found(self, mock_managers):
        """Test getting template information for non-existent template."""
        client = MCPClient()

        mock_managers["server_manager"].get_template_info.return_value = None

        result = client.get_template_info("nonexistent")

        assert result is None

    def test_list_servers(self, mock_managers):
        """Test listing running servers."""
        client = MCPClient()

        expected_servers = [
            {"id": "demo-1", "template": "demo", "status": "running"},
            {"id": "filesystem-1", "template": "filesystem", "status": "running"},
        ]
        mock_managers["server_manager"].list_running_servers.return_value = (
            expected_servers
        )

        result = client.list_servers()

        assert result == expected_servers
        mock_managers["server_manager"].list_running_servers.assert_called_once()

    def test_start_server(self, mock_managers):
        """Test starting a new server."""
        client = MCPClient()

        expected_result = {
            "id": "demo-1",
            "status": "running",
            "success": True,
        }
        mock_managers["server_manager"].start_server.return_value = expected_result

        config = {"greeting": "Hello"}
        result = client.start_server("demo", config)

        assert result == expected_result
        mock_managers["server_manager"].start_server.assert_called_once_with(
            template_id="demo",
            configuration=config,
            pull_image=True,
            transport=None,
            port=None,
        )

    def test_start_server_without_config(self, mock_managers):
        """Test starting a server without configuration."""
        client = MCPClient()

        expected_result = {"id": "demo-1", "status": "running", "success": True}
        mock_managers["server_manager"].start_server.return_value = expected_result

        result = client.start_server("demo")

        assert result == expected_result
        mock_managers["server_manager"].start_server.assert_called_once_with(
            template_id="demo",
            configuration=None,
            pull_image=True,
            transport=None,
            port=None,
        )

    def test_stop_server(self, mock_managers):
        """Test stopping a server."""
        client = MCPClient()

        mock_managers["server_manager"].stop_server.return_value = True

        result = client.stop_server("demo-1")

        assert result is True
        mock_managers["server_manager"].stop_server.assert_called_once_with("demo-1")

    def test_stop_server_with_active_connection(self, mock_managers):
        """Test stopping a server with active connection."""
        client = MCPClient()

        # Create mock connection
        mock_connection = AsyncMock()
        client._active_connections["demo-1"] = mock_connection

        mock_managers["server_manager"].stop_server.return_value = True

        result = client.stop_server("demo-1")

        assert result is True
        assert "demo-1" not in client._active_connections
        mock_managers["server_manager"].stop_server.assert_called_once_with("demo-1")

    def test_get_server_info(self, mock_managers):
        """Test getting server information."""
        client = MCPClient()

        expected_info = {"id": "demo-1", "template": "demo", "status": "running"}
        mock_managers["server_manager"].get_server_info.return_value = expected_info

        result = client.get_server_info("demo-1")

        assert result == expected_info
        mock_managers["server_manager"].get_server_info.assert_called_once_with(
            "demo-1"
        )

    def test_get_server_logs(self, mock_managers):
        """Test getting server logs."""
        client = MCPClient()

        expected_logs = "Server started successfully\nProcessing requests..."
        mock_managers["server_manager"].get_server_logs.return_value = expected_logs

        result = client.get_server_logs("demo-1")

        assert result == expected_logs
        mock_managers["server_manager"].get_server_logs.assert_called_once_with(
            "demo-1", 100
        )

    def test_get_server_logs_custom_lines(self, mock_managers):
        """Test getting server logs with custom line count."""
        client = MCPClient()

        expected_logs = "Recent logs..."
        mock_managers["server_manager"].get_server_logs.return_value = expected_logs

        result = client.get_server_logs("demo-1", lines=50)

        assert result == expected_logs
        mock_managers["server_manager"].get_server_logs.assert_called_once_with(
            "demo-1", 50
        )

    def test_list_tools_cached(self, mock_managers):
        """Test listing tools with cached results."""
        client = MCPClient()

        expected_tools = [
            {"name": "echo", "description": "Echo a message"},
            {"name": "greet", "description": "Greet someone"},
        ]

        # Setup template info mock
        template_info = {"template_dir": "/path/to/template"}
        mock_managers["template_discovery"].get_template_info.return_value = (
            template_info
        )
        mock_managers["tool_manager"].discover_tools_from_template.return_value = (
            expected_tools
        )

        result = client.list_tools("demo")
        assert result == expected_tools
        mock_managers["template_discovery"].get_template_info.assert_called_once_with(
            "demo"
        )
        mock_managers[
            "tool_manager"
        ].discover_tools_from_template.assert_called_once_with(template_info, False)

    def test_list_tools_force_refresh(self, mock_managers):
        """Test listing tools with forced refresh."""
        client = MCPClient()

        # Setup mocks
        template_info = {"template_dir": "/path/to/template"}
        mock_managers["template_discovery"].get_template_info.return_value = (
            template_info
        )

        discovery_result = {
            "tools": [
                {"name": "echo", "description": "Echo a message"},
                {"name": "greet", "description": "Greet someone"},
            ]
        }
        mock_managers["tool_manager"].discover_tools_from_template.return_value = (
            discovery_result
        )

        result = client.list_tools("demo", force_refresh=True)

        assert result == discovery_result
        mock_managers["template_discovery"].get_template_info.assert_called_once_with(
            "demo"
        )
        mock_managers[
            "tool_manager"
        ].discover_tools_from_template.assert_called_once_with(template_info, True)

    def test_list_tools_template_not_found(self, mock_managers):
        """Test listing tools for non-existent template."""
        client = MCPClient()

        mock_managers["template_discovery"].get_template_info.return_value = None

        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            client.list_tools("nonexistent")

    @pytest.mark.asyncio
    async def test_connect_stdio(self, mock_managers):
        """Test creating a stdio connection."""
        client = MCPClient()

        with patch("mcp_template.client.MCPConnection") as mock_connection_class:
            mock_connection = AsyncMock()
            mock_connection.connect_stdio.return_value = True
            mock_connection_class.return_value = mock_connection

            command = ["python", "server.py"]
            result = await client.connect_stdio(command)

            assert result == "stdio_0"
            assert "stdio_0" in client._active_connections
            mock_connection.connect_stdio.assert_called_once_with(
                command=command, working_dir=None, env_vars=None
            )

    @pytest.mark.asyncio
    async def test_connect_stdio_failure(self, mock_managers):
        """Test stdio connection failure."""
        client = MCPClient()

        with patch("mcp_template.client.MCPConnection") as mock_connection_class:
            mock_connection = AsyncMock()
            mock_connection.connect_stdio.return_value = False
            mock_connection_class.return_value = mock_connection

            command = ["python", "server.py"]
            result = await client.connect_stdio(command)

            assert result is None
            assert len(client._active_connections) == 0
            mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_from_connection(self, mock_managers):
        """Test listing tools from an active connection."""
        client = MCPClient()

        # Setup mock connection
        mock_connection = AsyncMock()
        expected_tools = [{"name": "echo", "description": "Echo a message"}]
        mock_connection.list_tools.return_value = expected_tools
        client._active_connections["test_conn"] = mock_connection

        result = await client.list_tools_from_connection("test_conn")

        assert result == expected_tools
        mock_connection.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_from_connection_not_found(self, mock_managers):
        """Test listing tools from non-existent connection."""
        client = MCPClient()

        result = await client.list_tools_from_connection("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_call_tool_from_connection(self, mock_managers):
        """Test calling a tool from an active connection."""
        client = MCPClient()

        # Setup mock connection
        mock_connection = AsyncMock()
        expected_result = {"status": "success", "content": "Hello World"}
        mock_connection.call_tool.return_value = expected_result
        client._active_connections["test_conn"] = mock_connection

        result = await client.call_tool_from_connection(
            "test_conn", "echo", {"message": "Hello World"}
        )

        assert result == expected_result
        mock_connection.call_tool.assert_called_once_with(
            "echo", {"message": "Hello World"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_from_connection_not_found(self, mock_managers):
        """Test calling tool from non-existent connection."""
        client = MCPClient()

        result = await client.call_tool_from_connection(
            "nonexistent", "echo", {"message": "Hello"}
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_managers):
        """Test disconnecting from an active connection."""
        client = MCPClient()

        # Setup mock connection
        mock_connection = AsyncMock()
        client._active_connections["test_conn"] = mock_connection

        result = await client.disconnect("test_conn")

        assert result is True
        assert "test_conn" not in client._active_connections
        mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self, mock_managers):
        """Test disconnecting from non-existent connection."""
        client = MCPClient()

        result = await client.disconnect("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_managers):
        """Test cleaning up all connections."""
        client = MCPClient()

        # Setup multiple mock connections
        mock_conn1 = AsyncMock()
        mock_conn2 = AsyncMock()
        client._active_connections["conn1"] = mock_conn1
        client._active_connections["conn2"] = mock_conn2

        await client.cleanup()

        assert len(client._active_connections) == 0
        mock_conn1.disconnect.assert_called_once()
        mock_conn2.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_managers):
        """Test using client as async context manager."""
        async with MCPClient() as client:
            assert isinstance(client, MCPClient)

            # Add a mock connection to test cleanup
            mock_connection = AsyncMock()
            client._active_connections["test"] = mock_connection

        # Connection should be cleaned up automatically
        assert len(client._active_connections) == 0
