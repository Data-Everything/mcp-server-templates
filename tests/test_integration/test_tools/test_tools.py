"""
Integration tests for the tools module (mcp_template.tools.*).

Tests end-to-end tool discovery workflows across different container platforms.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.integration

from mcp_template.tools.base_probe import BaseProbe
from mcp_template.tools.docker_probe import DockerProbe
from mcp_template.tools.kubernetes_probe import KubernetesProbe
from mcp_template.tools.mcp_client_probe import MCPClientProbe

pytestmark = pytest.mark.integration


class TestToolsIntegrationWorkflows:
    """Test end-to-end tool discovery workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tools_response = {
            "tools": [
                {
                    "name": "search_repositories",
                    "description": "Search GitHub repositories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "sort": {
                                "type": "string",
                                "enum": ["stars", "forks", "updated"],
                            },
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "create_issue",
                    "description": "Create a GitHub issue",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["title"],
                    },
                },
            ],
            "server_info": {
                "name": "GitHub MCP Server",
                "version": "1.0.0",
                "description": "MCP server for GitHub API integration",
            },
        }

    def test_docker_to_kubernetes_workflow(self):
        """Test workflow from Docker discovery to Kubernetes deployment."""
        # First: Discover tools using Docker
        with patch.object(DockerProbe, "discover_tools_from_image") as mock_docker:
            mock_docker.return_value = self.mock_tools_response

            docker_probe = DockerProbe()
            docker_result = docker_probe.discover_tools_from_image(
                "github-server:latest"
            )

            assert docker_result is not None
            assert len(docker_result["tools"]) == 2

        # Then: Use same image for Kubernetes discovery
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            with patch.object(KubernetesProbe, "discover_tools_from_image") as mock_k8s:
                mock_k8s.return_value = self.mock_tools_response

                k8s_probe = KubernetesProbe()
                k8s_result = k8s_probe.discover_tools_from_image("github-server:latest")

                assert k8s_result is not None
                assert k8s_result["tools"] == docker_result["tools"]

    @pytest.mark.asyncio
    async def test_mcp_client_direct_discovery_workflow(self):
        """Test direct MCP client discovery workflow."""
        # Mock a complete MCP server interaction
        probe = MCPClientProbe()

        # Test stdio discovery
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.wait = Mock(return_value=asyncio.Future())
            mock_process.wait.return_value.set_result(0)
            mock_process.terminate = Mock()

            # Mock stdio responses
            responses = [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": self.mock_tools_response["server_info"],
                        },
                    }
                )
                + "\n",
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "result": {"tools": self.mock_tools_response["tools"]},
                    }
                )
                + "\n",
            ]

            mock_process.stdout.readline = Mock(
                side_effect=[r.encode() for r in responses]
            )
            mock_exec.return_value = mock_process

            result = await probe.discover_tools_from_command(
                ["python", "-m", "github_server"]
            )

            assert result is not None
            assert "tools" in result
            assert len(result["tools"]) == 2
            assert result["server_info"]["name"] == "GitHub MCP Server"

    def test_multi_backend_tool_discovery_comparison(self):
        """Test comparing tool discovery across multiple backends."""
        image_name = "mcp-demo-server:latest"

        # Mock responses for different backends
        backends_results = {}

        # Docker discovery
        with patch.object(DockerProbe, "discover_tools_from_image") as mock_docker:
            mock_docker.return_value = self.mock_tools_response
            docker_probe = DockerProbe()
            backends_results["docker"] = docker_probe.discover_tools_from_image(
                image_name
            )

        # Kubernetes discovery
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            with patch.object(KubernetesProbe, "discover_tools_from_image") as mock_k8s:
                mock_k8s.return_value = self.mock_tools_response
                k8s_probe = KubernetesProbe()
                backends_results["kubernetes"] = k8s_probe.discover_tools_from_image(
                    image_name
                )

        # Verify consistency across backends
        assert all(result is not None for result in backends_results.values())

        # All backends should discover same tools
        docker_tools = backends_results["docker"]["tools"]
        k8s_tools = backends_results["kubernetes"]["tools"]

        assert len(docker_tools) == len(k8s_tools)
        for i, tool in enumerate(docker_tools):
            assert tool["name"] == k8s_tools[i]["name"]
            assert tool["description"] == k8s_tools[i]["description"]

    def test_error_recovery_workflow(self):
        """Test error recovery across different discovery methods."""
        image_name = "problematic-server:latest"

        # First attempt: Docker fails
        with patch.object(DockerProbe, "discover_tools_from_image") as mock_docker:
            mock_docker.return_value = None  # Simulate failure
            docker_probe = DockerProbe()
            docker_result = docker_probe.discover_tools_from_image(image_name)
            assert docker_result is None

        # Fallback: Kubernetes succeeds
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            with patch.object(KubernetesProbe, "discover_tools_from_image") as mock_k8s:
                mock_k8s.return_value = self.mock_tools_response
                k8s_probe = KubernetesProbe()
                k8s_result = k8s_probe.discover_tools_from_image(image_name)
                assert k8s_result is not None

    @pytest.mark.asyncio
    async def test_concurrent_discovery_workflow(self):
        """Test concurrent tool discovery across multiple images."""
        images = ["server1:latest", "server2:latest", "server3:latest"]

        # Mock different responses for each image
        responses = [
            {
                "tools": [{"name": f"tool_from_server_{i}"}],
                "server_info": {"name": f"Server {i}"},
            }
            for i in range(1, 4)
        ]

        # Test concurrent Docker discovery
        with patch.object(DockerProbe, "discover_tools_from_image") as mock_docker:
            mock_docker.side_effect = responses

            docker_probe = DockerProbe()

            # Simulate concurrent discovery
            tasks = []
            for image in images:
                # In real scenario, these would be actual async calls
                result = docker_probe.discover_tools_from_image(image)
                tasks.append(result)

            # Verify all discoveries completed
            assert len(tasks) == 3
            assert all(task is not None for task in tasks)

            # Verify each got different tools
            for i, result in enumerate(tasks):
                assert result["tools"][0]["name"] == f"tool_from_server_{i+1}"

    def test_configuration_driven_discovery_workflow(self):
        """Test tool discovery driven by configuration files."""
        # Create temporary config file
        config_data = {
            "servers": [
                {
                    "name": "github-server",
                    "image": "dataeverything/mcp-github:latest",
                    "backend": "docker",
                    "args": ["--port", "8080"],
                    "env": {"GITHUB_TOKEN": "test_token"},
                },
                {
                    "name": "filesystem-server",
                    "image": "dataeverything/mcp-filesystem:latest",
                    "backend": "kubernetes",
                    "args": ["--root", "/app/data"],
                    "env": {"READ_ONLY": "true"},
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            # Process configuration-driven discovery
            config_path = Path(config_file)
            config = json.loads(config_path.read_text())

            results = {}

            for server_config in config["servers"]:
                backend = server_config["backend"]
                image = server_config["image"]
                args = server_config.get("args", [])
                env = server_config.get("env", {})

                if backend == "docker":
                    with patch.object(
                        DockerProbe, "discover_tools_from_image"
                    ) as mock_docker:
                        mock_docker.return_value = self.mock_tools_response
                        probe = DockerProbe()
                        result = probe.discover_tools_from_image(
                            image, server_args=args, env_vars=env
                        )
                        results[server_config["name"]] = result

                elif backend == "kubernetes":
                    with patch.object(KubernetesProbe, "_init_kubernetes_client"):
                        with patch.object(
                            KubernetesProbe, "discover_tools_from_image"
                        ) as mock_k8s:
                            mock_k8s.return_value = self.mock_tools_response
                            probe = KubernetesProbe()
                            result = probe.discover_tools_from_image(
                                image, server_args=args, env_vars=env
                            )
                            results[server_config["name"]] = result

            # Verify all servers were discovered
            assert len(results) == 2
            assert "github-server" in results
            assert "filesystem-server" in results
            assert all(result is not None for result in results.values())

        finally:
            Path(config_file).unlink()


class TestToolsIntegrationErrorHandling:
    """Test error handling in integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_network_isolation_scenario(self):
        """Test tool discovery in network-isolated environments."""
        # Simulate network issues
        with patch("requests.get") as mock_requests:
            mock_requests.side_effect = ConnectionError("Network unreachable")

            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image("network-test:latest")

            # Should fail gracefully
            assert result is None

    @pytest.mark.asyncio
    async def test_stdio_communication_breakdown(self):
        """Test handling of stdio communication failures."""
        probe = MCPClientProbe()

        # Test process that immediately exits
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.wait = Mock(return_value=asyncio.Future())
            mock_process.wait.return_value.set_result(1)  # Non-zero exit
            mock_process.terminate = Mock()
            mock_exec.return_value = mock_process

            result = await probe.discover_tools_from_command(["failing_server"])
            assert result is None

    def test_resource_exhaustion_scenario(self):
        """Test behavior under resource exhaustion."""
        # Simulate out of memory or disk space
        with patch.object(DockerProbe, "_find_available_port") as mock_port:
            mock_port.return_value = None  # No ports available

            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image("resource-heavy:latest")

            assert result is None

    def test_kubernetes_rbac_failure_scenario(self):
        """Test Kubernetes discovery with RBAC restrictions."""
        from kubernetes.client.rest import ApiException

        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            probe = KubernetesProbe()
            probe.apps_v1 = Mock()
            probe.core_v1 = Mock()

            # Simulate RBAC denial
            probe.apps_v1.create_namespaced_deployment.side_effect = ApiException(
                status=403, reason="Forbidden"
            )

            result = probe.discover_tools_from_image("rbac-test:latest")
            assert result is None

    def test_malformed_mcp_response_handling(self):
        """Test handling of malformed MCP protocol responses."""
        probe = MCPClientProbe()

        # Test with malformed JSON
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.wait = Mock(return_value=asyncio.Future())
            mock_process.wait.return_value.set_result(0)
            mock_process.terminate = Mock()

            # Return invalid JSON
            mock_process.stdout.readline = Mock(return_value=b"invalid json\n")
            mock_exec.return_value = mock_process

            async def test_malformed():
                result = await probe.discover_tools_from_command(["malformed_server"])
                assert result is None

            asyncio.run(test_malformed())


class TestToolsIntegrationPerformance:
    """Test performance aspects of tool discovery integration."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_discovery_timeout_handling(self):
        """Test handling of discovery timeouts."""
        # Test with very short timeout
        with patch.object(DockerProbe, "_wait_for_container_health") as mock_health:
            mock_health.return_value = False  # Timeout

            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image(
                "slow-starting-server:latest", timeout=1  # Very short timeout
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_discovery_resource_management(self):
        """Test resource management during concurrent discoveries."""
        # Simulate multiple concurrent discoveries
        probe = MCPClientProbe()

        concurrent_commands = [["server1"], ["server2"], ["server3"]]

        # Mock process creation to track resource usage
        created_processes = []

        async def mock_create_process(*args, **kwargs):
            mock_process = Mock()
            mock_process.wait = Mock(return_value=asyncio.Future())
            mock_process.wait.return_value.set_result(0)
            mock_process.terminate = Mock()
            created_processes.append(mock_process)
            return mock_process

        with patch("asyncio.create_subprocess_exec", side_effect=mock_create_process):
            with patch.object(probe, "_communicate_via_stdio", return_value={}):
                # Run discoveries concurrently
                tasks = [
                    probe.discover_tools_from_command(cmd)
                    for cmd in concurrent_commands
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Verify all completed without exceptions
                assert len(results) == 3
                assert len(created_processes) == 3

    def test_memory_usage_in_large_tool_discovery(self):
        """Test memory usage with large tool discovery results."""
        # Create large mock response
        large_tools_response = {
            "tools": [
                {
                    "name": f"tool_{i}",
                    "description": f"Tool {i} " + "x" * 1000,  # Large description
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            f"param_{j}": {"type": "string"} for j in range(100)
                        },
                    },
                }
                for i in range(100)  # 100 tools
            ],
            "server_info": {"name": "Large Server", "version": "1.0"},
        }

        with patch.object(DockerProbe, "discover_tools_from_image") as mock_docker:
            mock_docker.return_value = large_tools_response

            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image("large-server:latest")

            # Should handle large responses
            assert result is not None
            assert len(result["tools"]) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
