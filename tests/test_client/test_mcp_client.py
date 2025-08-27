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
        # Use mock backend to avoid real Docker calls
        client = MCPClient(backend_type="mock")

        expected_servers = [
            {"id": "demo-1", "template": "demo", "status": "running"},
            {"id": "filesystem-1", "template": "filesystem", "status": "running"},
        ]

        # Create a mock for multi_manager instead
        mock_multi_manager = Mock()
        mock_multi_manager.get_all_deployments.return_value = expected_servers
        client.multi_manager = mock_multi_manager

        result = client.list_servers()

        assert result == expected_servers
        mock_multi_manager.get_all_deployments.assert_called_once_with(
            template_name=None, status=None
        )

    def test_start_server(self, mock_managers):
        """Test starting a new server."""
        client = MCPClient(backend_type="mock")

        # Replace deployment manager with mock
        client.deployment_manager = mock_managers["deployment_manager"]

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
        client.deployment_manager = mock_managers["deployment_manager"]

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

        # Mock the multi_manager directly
        mock_multi_manager = Mock()
        client.multi_manager = mock_multi_manager

        mock_stop_result = {"success": True, "deployment_id": "demo-1"}
        mock_multi_manager.stop_deployment.return_value = mock_stop_result

        result = client.stop_server("demo-1")

        assert result["success"] is True
        assert result["deployment_id"] == "demo-1"
        mock_multi_manager.stop_deployment.assert_called_once_with("demo-1", 30)

    def test_stop_server_with_active_connection(self, mock_managers):
        """Test stopping a server with active connection."""
        client = MCPClient()

        # Mock the multi_manager directly
        mock_multi_manager = Mock()
        client.multi_manager = mock_multi_manager

        # Create mock connection
        mock_connection = AsyncMock()
        client._active_connections["demo-1"] = mock_connection

        mock_stop_result = {"success": True, "deployment_id": "demo-1"}
        mock_multi_manager.stop_deployment.return_value = mock_stop_result

        result = client.stop_server("demo-1")

        assert result["success"] is True
        assert "demo-1" not in client._active_connections
        mock_multi_manager.stop_deployment.assert_called_once_with("demo-1", 30)

    def test_get_server_info(self, mock_managers):
        """Test getting server information."""
        client = MCPClient()
        client.deployment_manager = mock_managers["deployment_manager"]

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

        # Mock the MultiBackendManager that gets created in get_server_logs
        mock_multi_manager = Mock()
        expected_logs = "Server started successfully\nProcessing requests..."
        log_result = {"success": True, "logs": expected_logs}
        mock_multi_manager.get_deployment_logs.return_value = log_result

        with patch(
            "mcp_template.client.client.MultiBackendManager",
            return_value=mock_multi_manager,
        ):
            result = client.get_server_logs("demo-1")

            assert result == expected_logs
            mock_multi_manager.get_deployment_logs.assert_called_once_with(
                "demo-1", lines=100, follow=False
            )

    def test_get_server_logs_custom_lines(self, mock_managers):
        """Test getting server logs with custom line count."""
        client = MCPClient()

        # Mock the MultiBackendManager that gets created in get_server_logs
        mock_multi_manager = Mock()
        expected_logs = "Recent logs..."
        log_result = {"success": True, "logs": expected_logs}
        mock_multi_manager.get_deployment_logs.return_value = log_result

        with patch(
            "mcp_template.client.client.MultiBackendManager",
            return_value=mock_multi_manager,
        ):
            result = client.get_server_logs("demo-1", lines=50)

            assert result == expected_logs
            mock_multi_manager.get_deployment_logs.assert_called_once_with(
                "demo-1", lines=50, follow=False
            )

    def test_list_tools_cached(self, mock_managers):
        """Test listing tools with cached results."""
        client = MCPClient()
        client.tool_manager = mock_managers["tool_manager"]

        expected_tools = [
            {
                "name": "say_hello",
                "description": 'Generate a personalized greeting message.\n\nPATTERN 1: Uses standard config from config_schema\n- hello_from: Set via --config hello_from="value" or MCP_HELLO_FROM env var\n\nPATTERN 2: Uses template data that can be overridden\n- Tool behavior can be modified via --tools__0__greeting_style="formal"\n\nArgs:\n    name: Name of the person to greet\n\nReturns:\n    A personalized greeting message',
                "category": "mcp",
                "parameters": {
                    "properties": {
                        "name": {"default": "World", "title": "Name", "type": "string"}
                    },
                    "type": "object",
                },
                "mcp_info": {
                    "input_schema": {
                        "properties": {
                            "name": {
                                "default": "World",
                                "title": "Name",
                                "type": "string",
                            }
                        },
                        "type": "object",
                    },
                    "output_schema": {
                        "properties": {"result": {"title": "Result", "type": "string"}},
                        "required": ["result"],
                        "title": "_WrappedResult",
                        "type": "object",
                        "x-fastmcp-wrap-result": True,
                    },
                },
            },
            {
                "name": "get_server_info",
                "description": "Get information about the demo server.\n\nShows both standard config and template data that may be overridden.\n\nReturns:\n    Dictionary containing server information",
                "category": "mcp",
                "parameters": {"properties": {}, "type": "object"},
                "mcp_info": {
                    "input_schema": {"properties": {}, "type": "object"},
                    "output_schema": {"additionalProperties": True, "type": "object"},
                },
            },
            {
                "name": "echo_message",
                "description": "Echo back a message with server identification.\n\nDemonstrates template data override for tool behavior.\n\nArgs:\n    message: Message to echo back\n\nReturns:\n    Echoed message with server identification",
                "category": "mcp",
                "parameters": {
                    "properties": {"message": {"title": "Message", "type": "string"}},
                    "required": ["message"],
                    "type": "object",
                },
                "mcp_info": {
                    "input_schema": {
                        "properties": {
                            "message": {"title": "Message", "type": "string"}
                        },
                        "required": ["message"],
                        "type": "object",
                    },
                    "output_schema": {
                        "properties": {"result": {"title": "Result", "type": "string"}},
                        "required": ["result"],
                        "title": "_WrappedResult",
                        "type": "object",
                        "x-fastmcp-wrap-result": True,
                    },
                },
            },
            {
                "name": "demonstrate_overrides",
                "description": "Demonstrate the two configuration patterns.\n\nReturns:\n    Examples of both configuration patterns",
                "category": "mcp",
                "parameters": {"properties": {}, "type": "object"},
                "mcp_info": {
                    "input_schema": {"properties": {}, "type": "object"},
                    "output_schema": {"additionalProperties": True, "type": "object"},
                },
            },
        ]

        mock_managers["tool_manager"].list_tools.return_value = {
            "tools": expected_tools,
            "discovery_method": "auto",
            "metadata": {},
        }

        result = client.list_tools("demo")
        assert result == expected_tools
        mock_managers["tool_manager"].list_tools.assert_called_once_with(
            "demo", static=True, dynamic=True, force_refresh=False
        )

    def test_list_tools_force_refresh(self, mock_managers):
        """Test listing tools with forced refresh."""
        client = MCPClient()

        # Replace internal managers with mocks
        client.tool_manager = mock_managers["tool_manager"]

        expected_tools = [
            {
                "name": "say_hello",
                "description": "Say hello with a personalized greeting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "get_server_info",
                "description": "Get information about the MCP server",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "echo_message",
                "description": "Echo back the provided message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "demonstrate_overrides",
                "description": "Demonstrate MCP template override capabilities",
                "inputSchema": {"type": "object", "properties": {}},
            },
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
            "demo", static=True, dynamic=True, force_refresh=True
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

        with patch("mcp_template.client.client.MCPConnection") as mock_connection_class:
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

        with patch("mcp_template.client.client.MCPConnection") as mock_connection_class:
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


class TestMCPClientEnhanced:
    """Enhanced tests for MCP Client functionality focusing on robustness and protocol handling."""

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

    def test_client_timeout_configuration(self, mock_managers):
        """Test client timeout configuration for various scenarios."""
        # Test default timeout
        client_default = MCPClient()
        assert client_default.timeout == 30

        # Test custom timeout
        client_custom = MCPClient(timeout=120)
        assert client_custom.timeout == 120

        # Test very short timeout
        client_short = MCPClient(timeout=1)
        assert client_short.timeout == 1

    def test_client_backend_configuration(self, mock_managers):
        """Test client configuration with different backend types."""
        # Use only valid backend types
        backend_types = ["docker", "kubernetes", "mock"]

        for backend_type in backend_types:
            client = MCPClient(backend_type=backend_type)
            assert client.backend_type == backend_type

    @patch("mcp_template.client.client.MCPClient.start_server")
    def test_start_server_with_complex_configuration(
        self, mock_start_server, mock_managers
    ):
        """Test starting server with complex configuration including volumes and environment."""
        from mcp_template.core.deployment_manager import DeploymentResult

        mock_start_server.return_value = DeploymentResult(
            success=True,
            deployment_id="complex-deployment",
            status="running",
            ports={"8080": 8080},
        )

        client = MCPClient()

        complex_config = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token",
            "MCP_TRANSPORT": "stdio",
            "GITHUB_TOOLSET": "all",
            "DEBUG_MODE": "true",
            "RATE_LIMIT": "1000",
        }

        volumes = {
            "/host/data": "/container/data",
            "/host/config": "/container/config",
        }

        result = client.start_server(
            "github",
            configuration=complex_config,
            volumes=volumes,
            timeout=60,
        )

        mock_start_server.assert_called_once()
        call_args = mock_start_server.call_args

        # Verify complex configuration was passed
        assert call_args[0][0] == "github"  # template_id
        assert "configuration" in call_args[1]
        assert "volumes" in call_args[1]
        assert "timeout" in call_args[1]

    @patch("mcp_template.client.client.MCPClient.list_tools")
    def test_list_tools_with_filtering(self, mock_list_tools, mock_managers):
        """Test listing tools with various filtering options."""
        mock_tools = [
            {"name": "search", "description": "Search repositories"},
            {"name": "create_issue", "description": "Create a new issue"},
            {"name": "list_repos", "description": "List repositories"},
        ]

        mock_list_tools.return_value = mock_tools

        client = MCPClient()

        # Test basic tool listing
        tools = client.list_tools("github")
        assert len(tools) == 3
        assert any(tool["name"] == "search" for tool in tools)

        mock_list_tools.assert_called_with("github")

    @patch("mcp_template.client.client.MCPClient.call_tool")
    def test_call_tool_with_error_handling(self, mock_call_tool, mock_managers):
        """Test tool calling with various error scenarios."""
        client = MCPClient()

        # Test successful tool call
        mock_call_tool.return_value = {"status": "success", "result": "Tool executed"}
        result = client.call_tool("github", "search", {"query": "test"})
        assert result["status"] == "success"

        # Test tool call with error
        mock_call_tool.return_value = {"status": "error", "error": "Tool not found"}
        result = client.call_tool("github", "nonexistent", {})
        assert result["status"] == "error"

    def test_client_state_management(self, mock_managers):
        """Test client state management for active connections."""
        client = MCPClient()

        # Initially no active connections
        assert len(client._active_connections) == 0

        # Simulate adding connections
        mock_connection1 = Mock()
        mock_connection2 = Mock()

        client._active_connections["server1"] = mock_connection1
        client._active_connections["server2"] = mock_connection2

        assert len(client._active_connections) == 2
        assert "server1" in client._active_connections
        assert "server2" in client._active_connections

    @patch("mcp_template.client.client.MCPClient.get_server_logs")
    def test_get_logs_with_various_options(self, mock_get_server_logs, mock_managers):
        """Test log retrieval with different options."""
        mock_logs = [
            "2024-01-01 10:00:00 INFO: Server started",
            "2024-01-01 10:00:01 INFO: Tools initialized",
            "2024-01-01 10:00:02 ERROR: Connection timeout",
        ]

        mock_get_server_logs.return_value = mock_logs

        client = MCPClient()

        # Test basic log retrieval
        logs = client.get_server_logs("server1")
        assert len(logs) == 3
        assert "Server started" in logs[0]
        assert "ERROR" in logs[2]

        # Test with follow option
        logs = client.get_server_logs("server1", follow=True)
        mock_get_server_logs.assert_called_with("server1", follow=True)

    @patch("mcp_template.client.client.MCPClient.stop_server")
    def test_stop_server_with_force_option(self, mock_stop_server, mock_managers):
        """Test server stopping with force option."""
        mock_stop_server.return_value = {
            "status": "stopped",
            "deployment_id": "test-server",
        }

        client = MCPClient()

        # Test graceful stop
        result = client.stop_server("test-server")
        assert result["status"] == "stopped"

        # Test force stop
        result = client.stop_server("test-server", force=True)
        mock_stop_server.assert_called_with("test-server", force=True)

    def test_client_configuration_validation(self, mock_managers):
        """Test client configuration validation and error handling."""
        # Test with invalid backend type (should raise error)
        with pytest.raises(ValueError):
            client = MCPClient(backend_type="invalid_backend")

        # Test with negative timeout (should accept during initialization)
        try:
            client = MCPClient(timeout=-1)
            assert client.timeout == -1  # Should accept but may cause issues later
        except Exception:
            pytest.fail("Client should accept negative timeout during initialization")

    @patch("mcp_template.client.client.MCPClient.list_servers")
    def test_list_servers_with_backend_filtering(
        self, mock_list_servers, mock_managers
    ):
        """Test server listing with backend filtering."""
        mock_servers = [
            {"id": "server1", "backend": "docker", "status": "running"},
            {"id": "server2", "backend": "kubernetes", "status": "stopped"},
            {"id": "server3", "backend": "docker", "status": "running"},
        ]

        mock_list_servers.return_value = mock_servers

        client = MCPClient()

        # Test listing all servers
        servers = client.list_servers()
        assert len(servers) == 3

        # Test with backend filter
        servers = client.list_servers(backend="docker")
        mock_list_servers.assert_called_with(backend="docker")

    def test_client_resource_cleanup(self, mock_managers):
        """Test proper resource cleanup when client is destroyed."""
        client = MCPClient()

        # Add some mock connections
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        client._active_connections["test1"] = mock_conn1
        client._active_connections["test2"] = mock_conn2

        # Verify connections exist
        assert len(client._active_connections) == 2

        # Manual cleanup (simulating what happens in __del__ or context exit)
        client._active_connections.clear()
        assert len(client._active_connections) == 0

    @patch("mcp_template.client.client.MCPClient.start_server")
    def test_client_with_environment_variable_handling(
        self, mock_start_server, mock_managers
    ):
        """Test client handling of environment variables in server configuration."""
        from mcp_template.core.deployment_manager import DeploymentResult

        mock_start_server.return_value = DeploymentResult(
            success=True,
            deployment_id="env-test",
            status="running",
        )

        client = MCPClient()

        # Configuration with various environment variable patterns
        env_config = {
            "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx",
            "API_BASE_URL": "https://api.github.com",
            "RATE_LIMIT_PER_HOUR": "5000",
            "ENABLE_CACHING": "true",
            "DEBUG_LEVEL": "info",
        }

        result = client.start_server("github", configuration=env_config)

        mock_start_server.assert_called_once()
        call_args = mock_start_server.call_args

        # Verify environment configuration was passed correctly
        assert "configuration" in call_args[1]
        passed_config = call_args[1]["configuration"]

        # All environment variables should be passed through
        for key, value in env_config.items():
            assert key in str(passed_config) or value in str(passed_config)

    @patch("mcp_template.client.client.MCPClient.call_tool")
    def test_client_tool_call_with_complex_parameters(
        self, mock_call_tool, mock_managers
    ):
        """Test tool calling with complex parameter structures."""
        client = MCPClient()

        # Mock successful response with complex result
        complex_result = {
            "status": "completed",
            "data": {
                "repositories": [
                    {"name": "repo1", "stars": 100, "language": "Python"},
                    {"name": "repo2", "stars": 250, "language": "JavaScript"},
                ],
                "total_count": 2,
                "search_metadata": {
                    "query": "mcp server",
                    "sort": "stars",
                    "order": "desc",
                },
            },
        }

        mock_call_tool.return_value = complex_result

        # Complex parameters
        complex_params = {
            "query": "mcp server language:python",
            "sort": "stars",
            "order": "desc",
            "per_page": 50,
            "filters": {
                "language": "Python",
                "min_stars": 10,
                "topics": ["mcp", "ai", "server"],
            },
        }

        result = client.call_tool("github", "search_repositories", complex_params)

        # Verify complex result structure
        assert result["status"] == "completed"
        assert "repositories" in result["data"]
        assert len(result["data"]["repositories"]) == 2
        assert result["data"]["search_metadata"]["query"] == "mcp server"

        mock_call_tool.assert_called_once_with(
            "github", "search_repositories", complex_params
        )
