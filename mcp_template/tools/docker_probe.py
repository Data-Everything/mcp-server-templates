"""
Docker probe for discovering MCP server tools from Docker images.
"""

import json
import logging
import random
import socket
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from .base_probe import (
    CONTAINER_PORT_RANGE,
    DISCOVERY_RETRIES,
    DISCOVERY_RETRY_SLEEP,
    DISCOVERY_TIMEOUT,
    BaseProbe,
)

logger = logging.getLogger(__name__)


class DockerProbe(BaseProbe):
    """Probe Docker containers to discover MCP server tools."""

    def __init__(self):
        """Initialize Docker probe."""
        super().__init__()

    def _cleanup_container(self, container_name: str, timeout: int = 10):
        """Clean up container with background task if timeout occurs."""

        def cleanup_task():
            try:
                logger.debug(f"Starting cleanup for container {container_name}")
                # Try normal removal first
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    timeout=timeout,
                    check=True,
                )
                logger.debug(f"Successfully cleaned up container {container_name}")
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Cleanup timeout for container {container_name}, scheduling background cleanup"
                )
                # Schedule background cleanup
                background_cleanup = threading.Thread(
                    target=self._background_cleanup, args=(container_name,), daemon=True
                )
                background_cleanup.start()
            except subprocess.CalledProcessError as e:
                logger.debug(f"Cleanup failed for {container_name}: {e}")
            except Exception as e:
                logger.debug(f"Unexpected cleanup error for {container_name}: {e}")

        # Run cleanup in separate thread to not block main discovery
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def _background_cleanup(self, container_name: str, max_retries: int = 3):
        """Background cleanup with retries."""

        for attempt in range(max_retries):
            try:
                time.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                logger.info(
                    f"Background cleanup successful for {container_name} on attempt {attempt + 1}"
                )
                return
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                logger.debug(
                    f"Background cleanup attempt {attempt + 1} failed for {container_name}: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        f"Background cleanup failed after {max_retries} attempts for {container_name}"
                    )

    def discover_tools_from_image(
        self,
        image_name: str,
        server_args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = DISCOVERY_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server Docker image.

        Args:
            image_name: Docker image name to probe
            server_args: Arguments to pass to the MCP server
            env_vars: Environment variables to pass to the container
            timeout: Timeout for discovery process

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        logger.info("Discovering tools from MCP Docker image: %s", image_name)

        try:
            # Try MCP stdio first
            result = self._try_mcp_stdio_discovery(image_name, server_args, env_vars)
            if result:
                return result

            # Fallback to HTTP probe (for non-standard MCP servers)
            return self._try_http_discovery(image_name, timeout)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.error("Failed to discover tools from image %s: %s", image_name, e)
            return None

    @retry(
        stop=stop_after_attempt(DISCOVERY_RETRIES),
        wait=wait_fixed(DISCOVERY_RETRY_SLEEP),
        retry=retry_if_exception_type(
            (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError)
        ),
        reraise=True,
    )
    def _try_mcp_stdio_discovery(
        self,
        image_name: str,
        server_args: Optional[List[str]],
        env_vars: Optional[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using MCP stdio protocol."""
        try:
            args = server_args or []
            result = self.mcp_client.discover_tools_from_docker_sync(
                image_name, args, env_vars
            )

            if result:
                logger.info(
                    "Successfully discovered tools via MCP stdio from %s", image_name
                )
                result["discovery_method"] = "docker_mcp_stdio"

            return result

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.debug("MCP stdio discovery failed for %s: %s", image_name, e)
            return None

    @retry(
        stop=stop_after_attempt(DISCOVERY_RETRIES),
        wait=wait_fixed(DISCOVERY_RETRY_SLEEP),
        retry=retry_if_exception_type(
            (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError)
        ),
        reraise=True,
    )
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

    @staticmethod
    def _find_available_port() -> Optional[int]:
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
                    logger.debug("Container %s is not running", container_name)
                    return False

                # Try different health check endpoints for different server types
                health_endpoints = ["/health", "/mcp", "/", "/api/health"]

                for endpoint in health_endpoints:
                    try:
                        response = requests.get(
                            f"http://localhost:{port}{endpoint}", timeout=2
                        )
                        if (
                            response.status_code < 500
                        ):  # Any non-server-error response is good
                            logger.debug(
                                "Container %s is ready (endpoint: %s)",
                                container_name,
                                endpoint,
                            )
                            return True
                    except requests.RequestException:
                        continue  # Try next endpoint

                # If no endpoint worked, try simple port connectivity check
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(("localhost", port))
                    sock.close()
                    if result == 0:  # Port is open
                        logger.debug(
                            "Container %s port %d is open", container_name, port
                        )
                        return True
                except socket.error:
                    pass

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
        """Clean up container synchronously, with background fallback on timeout/error."""
        try:
            # Stop container with short timeout
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                timeout=5,  # Reduced timeout
                check=False,
            )

            # Try to remove container synchronously first
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                timeout=30,
                check=True,
            )
            logger.debug("Successfully cleaned up container %s", container_name)

        except subprocess.TimeoutExpired:
            logger.warning(
                "Timeout cleaning up container %s, scheduling background cleanup",
                container_name,
            )
            self._background_cleanup(container_name)
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(
                "Error cleaning up container %s: %s, scheduling background cleanup",
                container_name,
                e,
            )
            # Still try cleanup
            self._background_cleanup(container_name)
