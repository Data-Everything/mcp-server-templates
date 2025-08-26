"""Unit tests for MCP Client functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.client import MCPClient


@pytest.mark.unit
class TestMCPClient:
    """Test cases for the MCPClient class."""

    @pytest.fixture
    def mock_managers(self):
        """Mock the internal managers."""
        with (
            patch("mcp_template.core.DeploymentManager") as mock_deployment_manager,
            patch("mcp_template.core.ToolManager") as mock_tool_manager,
            patch("mcp_template.core.TemplateManager") as mock_template_manager,
        ):

            # Setup mock instances
            mock_deploy_mgr = Mock()
            mock_tool_mgr = Mock()
            mock_template_mgr = Mock()

            mock_deployment_manager.return_value = mock_deploy_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_manager.return_value = mock_template_mgr

            yield {
                "deployment_manager": mock_deploy_mgr,
                "tool_manager": mock_tool_mgr,
                "template_manager": mock_template_mgr,
            }

    def test_client_initialization(self, mock_managers):
        """Test client initialization with default parameters."""
        client = MCPClient()

        assert client.backend_type == "docker"
        assert client.timeout == 30
        assert client._active_connections == {}

    def test_client_initialization_with_custom_params(self, mock_managers):
        """Test client initialization with custom parameters."""
        client = MCPClient(backend_type="mock", timeout=60)

        assert client.backend_type == "mock"
        assert client.timeout == 60

    def test_list_templates(self):
        """Test listing available templates."""
        client = MCPClient()

        # Use real template manager to get actual template data
        templates = client.list_templates()

        # Verify we get actual templates from discovery
        assert isinstance(templates, dict)
        assert "demo" in templates

        # Check demo template has expected structure
        demo_template = templates["demo"]
        assert "name" in demo_template
        assert "transport" in demo_template

    def test_get_template_info(self):
        """Test getting template information."""
        client = MCPClient()

        # Test getting info for demo template
        result = client.get_template_info("demo")

        # Verify we get actual template info
        assert result is not None
        assert isinstance(result, dict)
        assert "name" in result

        # Test getting info for non-existent template
        non_existent = client.get_template_info("nonexistent")
        assert non_existent is None

    def test_list_servers(self, mock_managers):
        """Test listing running servers."""
        client = MCPClient()

        expected_servers = [
            {"id": "demo-1", "template": "demo", "status": "running"},
            {"id": "filesystem-1", "template": "filesystem", "status": "running"},
        ]
        mock_managers[
            "deployment_manager"
        ].find_deployments_by_criteria.return_value = expected_servers

        result = client.list_servers()

        assert result == expected_servers
        mock_managers[
            "deployment_manager"
        ].find_deployments_by_criteria.assert_called_once_with(template_name=None)

    def test_start_server(self, mock_managers):
        """Test starting a new server."""
        client = MCPClient()

        # Mock a successful DeploymentResult
        from mcp_template.core.deployment_manager import DeploymentResult

        mock_deployment_result = DeploymentResult(
            success=True, deployment_id="demo-1", template="demo", status="running"
        )

        mock_managers["deployment_manager"].deploy_template.return_value = (
            mock_deployment_result
        )

        config = {"greeting": "Hello"}
        result = client.start_server("demo", config)

        assert result["deployment_id"] == "demo-1"
        assert result["status"] == "running"
        assert result["success"] is True
        mock_managers["deployment_manager"].deploy_template.assert_called_once()

    def test_start_server_without_config(self, mock_managers):
        """Test starting a server without configuration."""
        client = MCPClient()

        # Mock a successful DeploymentResult
        from mcp_template.core.deployment_manager import DeploymentResult

        mock_deployment_result = DeploymentResult(
            success=True, deployment_id="demo-1", template="demo", status="running"
        )

        mock_managers["deployment_manager"].deploy_template.return_value = (
            mock_deployment_result
        )

        result = client.start_server("demo")

        assert result["deployment_id"] == "demo-1"
        assert result["status"] == "running"
        assert result["success"] is True
        mock_managers["deployment_manager"].deploy_template.assert_called_once()

    def test_stop_server(self, mock_managers):
        """Test stopping a server."""
        client = MCPClient()

        mock_stop_result = {"success": True, "deployment_id": "demo-1"}
        mock_managers["deployment_manager"].stop_deployment.return_value = (
            mock_stop_result
        )

        result = client.stop_server("demo-1")

        assert result["success"] is True
        assert result["deployment_id"] == "demo-1"
        mock_managers["deployment_manager"].stop_deployment.assert_called_once_with(
            "demo-1", 30
        )

    def test_stop_server_with_active_connection(self, mock_managers):
        """Test stopping a server with active connection."""
        client = MCPClient()

        # Create mock connection
        mock_connection = AsyncMock()
        client._active_connections["demo-1"] = mock_connection

        mock_stop_result = {"success": True, "deployment_id": "demo-1"}
        mock_managers["deployment_manager"].stop_deployment.return_value = (
            mock_stop_result
        )

        result = client.stop_server("demo-1")

        assert result["success"] is True
        assert "demo-1" not in client._active_connections
        mock_managers["deployment_manager"].stop_deployment.assert_called_once_with(
            "demo-1", 30
        )

    def test_get_server_info(self, mock_managers):
        """Test getting server information."""
        client = MCPClient()

        expected_info = [{"id": "demo-1", "template": "demo", "status": "running"}]
        mock_managers[
            "deployment_manager"
        ].find_deployments_by_criteria.return_value = expected_info

        result = client.get_server_info("demo-1")

        assert result == expected_info[0]
        mock_managers[
            "deployment_manager"
        ].find_deployments_by_criteria.assert_called_once_with(deployment_id="demo-1")

    def test_get_server_logs(self, mock_managers):
        """Test getting server logs."""
        client = MCPClient()

        expected_logs = "Server started successfully\nProcessing requests..."
        log_result = {"success": True, "logs": expected_logs}
        mock_managers["deployment_manager"].get_deployment_logs.return_value = (
            log_result
        )

        result = client.get_server_logs("demo-1")

        assert result == expected_logs
        mock_managers["deployment_manager"].get_deployment_logs.assert_called_once_with(
            "demo-1", lines=100, follow=False
        )

    def test_get_server_logs_custom_lines(self, mock_managers):
        """Test getting server logs with custom line count."""
        client = MCPClient()

        expected_logs = "Recent logs..."
        log_result = {"success": True, "logs": expected_logs}
        mock_managers["deployment_manager"].get_deployment_logs.return_value = (
            log_result
        )

        result = client.get_server_logs("demo-1", lines=50)

        assert result == expected_logs
        mock_managers["deployment_manager"].get_deployment_logs.assert_called_once_with(
            "demo-1", lines=50, follow=False
        )

    def test_list_tools_cached(self, mock_managers):
        """Test listing tools with cached results."""
        client = MCPClient()

        expected_tools = [
            {"name": "echo", "description": "Echo a message"},
            {"name": "greet", "description": "Greet someone"},
        ]

        mock_managers["tool_manager"].list_tools.return_value = {
            "tools": expected_tools,
            "discovery_method": "auto",
            "metadata": {},
        }

        result = client.list_tools("demo")
        assert result == expected_tools
        mock_managers["tool_manager"].list_tools.assert_called_once_with(
            "demo", discovery_method="auto", force_refresh=False
        )

    def test_list_tools_force_refresh(self, mock_managers):
        """Test listing tools with forced refresh."""
        client = MCPClient()

        expected_tools = [
            {"name": "echo", "description": "Echo a message"},
            {"name": "greet", "description": "Greet someone"},
        ]

        mock_managers["tool_manager"].list_tools.return_value = {
            "tools": expected_tools,
            "discovery_method": "auto",
            "metadata": {},
        }

        result = client.list_tools("demo", force_refresh=True)

        assert result == expected_tools
        mock_managers["tool_manager"].clear_cache.assert_called_once_with(
            template_name="demo"
        )
        mock_managers["tool_manager"].list_tools.assert_called_once_with(
            "demo", discovery_method="auto", force_refresh=True
        )

    def test_list_tools_template_not_found(self, mock_managers):
        """Test listing tools for non-existent template."""
        client = MCPClient()

        mock_managers["tool_manager"].list_tools.return_value = []

        result = client.list_tools("nonexistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_connect_stdio(self, mock_managers):
        """Test creating a stdio connection."""
        client = MCPClient()

        with patch("mcp_template.core.MCPConnection") as mock_connection_class:
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

        with patch("mcp_template.core.MCPConnection") as mock_connection_class:
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
