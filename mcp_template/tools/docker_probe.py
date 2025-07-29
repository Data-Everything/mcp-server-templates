"""
Docker probe for discovering MCP server tools from Docker images.
"""

import json
import logging
import random
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional

import requests

from .mcp_client_probe import MCPClientProbe

logger = logging.getLogger(__name__)

# Constants
DISCOVERY_TIMEOUT = 30
CONTAINER_PORT_RANGE = (8000, 9000)
CONTAINER_HEALTH_CHECK_TIMEOUT = 15


class DockerProbe:
    """Probe Docker containers to discover MCP server tools."""

    def __init__(self):
        """Initialize Docker probe."""
        self.mcp_client = MCPClientProbe()

    def discover_tools_from_image(
        self,
        image_name: str,
        server_args: Optional[List[str]] = None,
        timeout: int = DISCOVERY_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server Docker image.

        Args:
            image_name: Docker image name to probe
            server_args: Arguments to pass to the MCP server
            timeout: Timeout for discovery process

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        logger.info("Discovering tools from MCP Docker image: %s", image_name)

        try:
            # Try MCP stdio first
            result = self._try_mcp_stdio_discovery(image_name, server_args)
            if result:
                return result

            # Fallback to HTTP probe (for non-standard MCP servers)
            return self._try_http_discovery(image_name, timeout)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.error("Failed to discover tools from image %s: %s", image_name, e)
            return None

    def _try_mcp_stdio_discovery(
        self, image_name: str, server_args: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using MCP stdio protocol."""
        try:
            args = server_args or []
            result = self.mcp_client.discover_tools_from_docker_sync(image_name, args)

            if result:
                logger.info(
                    "Successfully discovered tools via MCP stdio from %s", image_name
                )
                result["discovery_method"] = "docker_mcp_stdio"

            return result

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.debug("MCP stdio discovery failed for %s: %s", image_name, e)
            return None

    def _try_http_discovery(
        self, image_name: str, timeout: int
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using HTTP endpoints (fallback)."""
        container_name = None
        try:
            # Generate unique container name
            container_name = self._generate_container_name(image_name)

            # Find available port
            port = self._find_available_port()
            if not port:
                logger.error("No available ports found for container")
                return None

            # Start container with HTTP server
            if not self._start_http_container(image_name, container_name, port):
                return None

            # Wait for container to be ready
            if not self._wait_for_container_ready(container_name, port, timeout):
                return None

            # Discover tools from running container
            base_url = f"http://localhost:{port}"
            result = self._probe_container_endpoints(
                base_url, self._get_default_endpoints()
            )

            if result:
                result.update(
                    {
                        "discovery_method": "docker_http_probe",
                        "timestamp": time.time(),
                        "source_image": image_name,
                        "container_name": container_name,
                        "port": port,
                    }
                )

            return result

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.debug("HTTP discovery failed for %s: %s", image_name, e)
            return None

        finally:
            # Always cleanup container
            if container_name:
                self._cleanup_container(container_name)

    def _generate_container_name(self, image_name: str) -> str:
        """Generate unique container name."""
        clean_name = image_name.replace("/", "-").replace(":", "-")
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        return f"mcp-tool-discovery-{clean_name}-{timestamp}-{random_suffix}"

    def _find_available_port(self) -> Optional[int]:
        """Find an available port for the container."""
        for port in range(CONTAINER_PORT_RANGE[0], CONTAINER_PORT_RANGE[1]):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(("localhost", port))
                    return port
            except OSError:
                continue
        return None

    def _start_http_container(
        self, image_name: str, container_name: str, port: int
    ) -> bool:
        """Start container with HTTP server (fallback method)."""
        try:
            cmd = [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                f"{port}:8000",
                image_name,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode == 0:
                logger.debug("Container %s started successfully", container_name)
                return True
            else:
                logger.error(
                    "Failed to start container %s: %s", container_name, result.stderr
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout starting container %s", container_name)
            return False
        except (subprocess.CalledProcessError, OSError) as e:
            logger.error("Error starting container %s: %s", container_name, e)
            return False

    def _wait_for_container_ready(
        self, container_name: str, port: int, timeout: int
    ) -> bool:
        """Wait for container to be ready to accept requests."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if container is still running
                if not self._is_container_running(container_name):
                    logger.error("Container %s is not running", container_name)
                    return False

                # Try to connect to the service
                response = requests.get(f"http://localhost:{port}/health", timeout=2)

                if response.status_code < 500:  # Any non-server-error response is good
                    logger.debug("Container %s is ready", container_name)
                    return True

            except requests.RequestException:
                # Expected during startup, continue waiting
                pass

            time.sleep(1)

        logger.warning(
            "Container %s did not become ready within %d seconds",
            container_name,
            timeout,
        )
        return False

    def _is_container_running(self, container_name: str) -> bool:
        """Check if container is still running."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip() == "true"

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _probe_container_endpoints(
        self, base_url: str, endpoints: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Probe container endpoints for tool information."""
        for endpoint in endpoints:
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                logger.debug("Probing container endpoint: %s", url)

                response = requests.get(
                    url, timeout=5, headers={"Accept": "application/json"}
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if self._is_valid_tools_response(data):
                            return {
                                "tools": self._normalize_tools(data),
                                "source_endpoint": url,
                                "response_data": data,
                            }
                    except json.JSONDecodeError:
                        logger.debug("Non-JSON response from %s", url)
                        continue

            except requests.RequestException as e:
                logger.debug("Failed to probe %s: %s", endpoint, e)
                continue

        return None

    def _get_default_endpoints(self) -> List[str]:
        """Get default endpoints to probe."""
        return ["/tools", "/api/tools", "/v1/tools", "/mcp/tools", "/.well-known/tools"]

    def _is_valid_tools_response(self, data: Any) -> bool:
        """Check if response contains valid tools data."""
        if not isinstance(data, dict):
            return False

        # Check for tools in various formats
        if "tools" in data and isinstance(data["tools"], list):
            return True

        if "result" in data and isinstance(data.get("result"), dict):
            result = data["result"]
            if "tools" in result and isinstance(result["tools"], list):
                return True

        return False

    def _normalize_tools(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize tools data to standard format."""
        tools = []

        # Extract tools from various response formats
        raw_tools = data.get("tools", [])
        if not raw_tools and "result" in data:
            raw_tools = data["result"].get("tools", [])

        for tool in raw_tools:
            if not isinstance(tool, dict):
                continue

            normalized_tool = {
                "name": tool.get("name", tool.get("function_name", "unknown")),
                "description": tool.get(
                    "description", tool.get("summary", "No description available")
                ),
                "category": tool.get("category", "general"),
                "parameters": tool.get(
                    "parameters", tool.get("args", tool.get("inputSchema", {}))
                ),
            }

            tools.append(normalized_tool)

        return tools

    def _cleanup_container(self, container_name: str) -> None:
        """Clean up container resources."""
        try:
            # Stop container
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                timeout=10,
                check=False,
            )

            # Remove container
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                timeout=10,
                check=False,
            )

            logger.debug("Cleaned up container %s", container_name)

        except subprocess.TimeoutExpired:
            logger.warning("Timeout cleaning up container %s", container_name)
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning("Error cleaning up container %s: %s", container_name, e)
