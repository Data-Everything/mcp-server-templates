"""Integration tests for MCP Client with real templates."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_template.client import MCPClient

pytestmark = pytest.mark.integration


class TestMCPClientIntegration:
    """Integration test cases for the MCPClient."""

    @pytest.mark.asyncio
    async def test_client_with_demo_template(self):
        """Test client functionality with demo template."""
        # This test mocks the deployment backend to avoid Docker dependencies

        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager") as mock_tool_manager,
            patch("mcp_template.client.TemplateDiscovery") as mock_template_discovery,
        ):

            # Setup mock managers
            mock_server_mgr = MagicMock()
            mock_tool_mgr = MagicMock()
            mock_template_disc = MagicMock()

            mock_server_manager.return_value = mock_server_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_discovery.return_value = mock_template_disc

            # Mock demo template data
            demo_template = {
                "name": "Demo MCP Server",
                "description": "A demo server for testing",
                "version": "1.0.0",
                "docker_image": "dataeverything/mcp-demo",
                "transport": {"default": "stdio", "supported": ["stdio"]},
                "template_dir": "/path/to/demo",
            }

            mock_server_mgr.list_available_templates.return_value = {
                "demo": demo_template
            }
            mock_server_mgr.get_template_info.return_value = demo_template

            # Mock tools
            demo_tools = [
                {
                    "name": "echo",
                    "description": "Echo back the input message",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo",
                            }
                        },
                        "required": ["message"],
                    },
                },
                {
                    "name": "greet",
                    "description": "Greet with a custom message",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name to greet"}
                        },
                        "required": ["name"],
                    },
                },
            ]

            mock_tool_mgr.discover_tools_from_template.return_value = demo_tools
            mock_tool_mgr.list_discovered_tools.return_value = demo_tools
            mock_tool_mgr.list_tools.return_value = {
                "tools": demo_tools,
                "discovery_method": "auto",
                "metadata": {},
            }

            # Test the client
            async with MCPClient(backend_type="mock") as client:
                # Test template discovery
                templates = client.list_templates()
                assert "demo" in templates
                assert templates["demo"]["name"] == "Demo Hello MCP Server"

                # Test tool discovery
                tools = client.list_tools("demo")
                assert len(tools) == 2
                assert tools[0]["name"] == "echo"
                assert tools[1]["name"] == "greet"

    @pytest.mark.asyncio
    async def test_client_server_lifecycle(self):
        """Test complete server lifecycle with client."""

        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager") as mock_tool_manager,
            patch("mcp_template.client.TemplateDiscovery") as mock_template_discovery,
        ):

            # Setup mocks
            mock_server_mgr = MagicMock()
            mock_tool_mgr = MagicMock()
            mock_template_disc = MagicMock()

            mock_server_manager.return_value = mock_server_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_discovery.return_value = mock_template_disc

            # Mock server lifecycle responses
            mock_server_mgr.start_server.return_value = {
                "id": "demo-test-1",
                "name": "demo-test-1",
                "status": "running",
                "success": True,
            }

            mock_server_mgr.list_running_servers.return_value = [
                {"id": "demo-test-1", "template": "demo", "status": "running"}
            ]

            mock_server_mgr.get_server_info.return_value = {
                "id": "demo-test-1",
                "template": "demo",
                "status": "running",
                "transport": {"default": "stdio", "supported": ["stdio"]},
            }

            mock_server_mgr.get_server_logs.return_value = "Server started successfully"
            mock_server_mgr.stop_server.return_value = True

            client = MCPClient(backend_type="mock")

            # Start server
            result = client.start_server("demo", {"greeting": "Hello from test"})
            assert result["success"] is True
            assert result["deployment_id"] is not None
            assert result["deployment_id"].startswith("mcp-demo-")
            deployment_id = result["deployment_id"]

            # List running servers
            servers = client.list_servers()
            assert len(servers) == 1
            assert servers[0]["name"] == deployment_id

            # Get server info
            info = client.get_server_info(deployment_id)
            assert info["status"] == "running"

            # Get logs
            logs = client.get_server_logs(deployment_id)
            assert "Mock log line 1" in logs

            # Stop server
            stopped = client.stop_server(deployment_id)
            assert stopped["success"] is True

    @pytest.mark.asyncio
    async def test_client_connection_management(self):
        """Test direct connection management."""

        with (
            patch("mcp_template.client.MCPConnection") as mock_connection_class,
            patch("mcp_template.client.ServerManager"),
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.TemplateDiscovery"),
        ):

            # Setup mock connection
            mock_connection = MagicMock()
            mock_connection.connect_stdio = AsyncMock(return_value=True)
            mock_connection.list_tools = AsyncMock(
                return_value=[{"name": "test_tool", "description": "A test tool"}]
            )
            mock_connection.call_tool = AsyncMock(
                return_value={"content": [{"type": "text", "text": "Test response"}]}
            )
            mock_connection.disconnect = AsyncMock()

            mock_connection_class.return_value = mock_connection

            client = MCPClient()

            # Test connection
            connection_id = await client.connect_stdio(["python", "test_server.py"])
            assert connection_id == "stdio_0"
            assert connection_id in client._active_connections

            # Test tool listing from connection
            tools = await client.list_tools_from_connection(connection_id)
            assert len(tools) == 1
            assert tools[0]["name"] == "test_tool"

            # Test tool calling from connection
            result = await client.call_tool_from_connection(
                connection_id, "test_tool", {"arg": "value"}
            )
            assert result["content"][0]["text"] == "Test response"

            # Test disconnection
            disconnected = await client.disconnect(connection_id)
            assert disconnected is True
            assert connection_id not in client._active_connections

            # Verify connection methods were called
            mock_connection.connect_stdio.assert_called_once()
            mock_connection.list_tools.assert_called_once()
            mock_connection.call_tool.assert_called_once()
            mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_error_handling(self):
        """Test client error handling scenarios."""

        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager") as mock_tool_manager,
            patch("mcp_template.client.TemplateDiscovery") as mock_template_discovery,
        ):

            # Setup mocks with failures
            mock_server_mgr = MagicMock()
            mock_tool_mgr = MagicMock()
            mock_template_disc = MagicMock()

            mock_server_manager.return_value = mock_server_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_discovery.return_value = mock_template_disc

            # Mock failures
            mock_server_mgr.get_template_info.return_value = None
            mock_server_mgr.start_server.return_value = None
            mock_server_mgr.stop_server.return_value = False
            mock_tool_mgr.list_discovered_tools.return_value = None
            mock_tool_mgr.list_tools.return_value = []

            client = MCPClient()

            # Test starting non-existent template
            result = client.start_server("nonexistent")
            assert result is None

            # Test stopping non-existent server
            stopped = client.stop_server("nonexistent")
            assert stopped["success"] is False

            # Test listing tools for non-existent template - should return empty list
            tools = client.list_tools("nonexistent")
            assert tools == []

    @pytest.mark.asyncio
    async def test_client_concurrent_operations(self):
        """Test client handling of concurrent operations."""

        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager") as mock_tool_manager,
            patch("mcp_template.client.TemplateDiscovery") as mock_template_discovery,
        ):

            # Setup mocks
            mock_server_mgr = MagicMock()
            mock_tool_mgr = MagicMock()
            mock_template_disc = MagicMock()

            mock_server_manager.return_value = mock_server_mgr
            mock_tool_manager.return_value = mock_tool_mgr
            mock_template_discovery.return_value = mock_template_disc

            # Mock responses with delays to test concurrency
            def delayed_start_server(
                template_id,
                configuration=None,
                pull_image=True,
                transport="http",
                port=12345,
            ):
                return {
                    "id": f"{template_id}-1",
                    "success": True,
                    "pull_image": pull_image,
                    "transport": transport,
                    "port": port,
                }

            mock_server_mgr.start_server.side_effect = delayed_start_server

            client = MCPClient()

            # Test concurrent server starts (these are now sync operations)
            results = []
            for template_id, config in [
                ("demo", {"instance": 1}),
                ("filesystem", {"instance": 2}),
                ("demo", {"instance": 3}),
            ]:
                result = client.start_server(template_id, config)
                results.append(result)

            # Verify all operations completed
            assert len(results) == 3
            # Filter out None results (failed deployments) and check successful ones
            successful_results = [r for r in results if r is not None]
            assert all(r["success"] for r in successful_results)
            # At least some deployments should succeed
            assert len(successful_results) > 0

    @pytest.mark.asyncio
    async def test_client_resource_cleanup(self):
        """Test proper resource cleanup."""

        with (
            patch("mcp_template.client.MCPConnection") as mock_connection_class,
            patch("mcp_template.client.ServerManager"),
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.TemplateDiscovery"),
        ):

            # Setup multiple mock connections
            mock_connections = []
            for i in range(3):
                mock_conn = MagicMock()
                mock_conn.connect_stdio = AsyncMock(return_value=True)
                mock_conn.disconnect = AsyncMock()
                mock_connections.append(mock_conn)

            mock_connection_class.side_effect = mock_connections

            client = MCPClient()

            # Create multiple connections
            conn_ids = []
            for i in range(3):
                conn_id = await client.connect_stdio(["python", f"server{i}.py"])
                conn_ids.append(conn_id)

            assert len(client._active_connections) == 3

            # Test cleanup
            await client.cleanup()

            # Verify all connections were disconnected
            assert len(client._active_connections) == 0
            for mock_conn in mock_connections:
                mock_conn.disconnect.assert_called_once()
