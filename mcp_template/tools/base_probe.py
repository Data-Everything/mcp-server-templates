"""
Base probe for discovering MCP server tools from different container orchestrators.

This module provides a common interface and shared functionality for probing
MCP servers across Docker, Kubernetes, and other container platforms.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiohttp

from mcp_template.core.mcp_connection import MCPConnection

from .mcp_client_probe import MCPClientProbe

logger = logging.getLogger(__name__)

# Constants shared across all probes
DISCOVERY_TIMEOUT = int(os.environ.get("MCP_DISCOVERY_TIMEOUT", "60"))
DISCOVERY_RETRIES = int(os.environ.get("MCP_DISCOVERY_RETRIES", "3"))
DISCOVERY_RETRY_SLEEP = int(os.environ.get("MCP_DISCOVERY_RETRY_SLEEP", "5"))
CONTAINER_PORT_RANGE = (8000, 9000)
CONTAINER_HEALTH_CHECK_TIMEOUT = 15


class BaseProbe(ABC):
    """Base class for MCP server tool discovery probes."""

    def __init__(self):
        """Initialize base probe with MCP client."""
        self.mcp_client = MCPClientProbe()

    @abstractmethod
    def discover_tools_from_image(
        self,
        image_name: str,
        server_args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = DISCOVERY_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server image.

        Args:
            image_name: Container image name to probe
            server_args: Arguments to pass to the MCP server
            env_vars: Environment variables to pass to the container
            timeout: Timeout for discovery process

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        pass

    def _get_default_endpoints(self) -> List[str]:
        """Get default endpoints to probe for MCP tools."""
        return [
            "/mcp",
            "/api/mcp",
            "/tools",
            "/list-tools",
            "/health",
            "/",
        ]

    def _normalize_mcp_tools(
        self, mcp_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize MCP tools to standard format."""
        normalized = []

        # Defensive check: ensure mcp_tools is iterable
        if not isinstance(mcp_tools, (list, tuple)):
            logger.error(
                f"Expected list/tuple for mcp_tools, got {type(mcp_tools)}: {mcp_tools}"
            )
            return []

        for tool in mcp_tools:
            try:
                # Skip None or invalid tools
                if tool is None or not isinstance(tool, dict):
                    continue

                normalized_tool = {
                    "name": tool.get("name", "unknown"),
                    "description": tool.get("description", "No description available"),
                    "category": "mcp",
                    "parameters": tool.get("inputSchema", {}),
                    "mcp_info": {
                        "input_schema": tool.get("inputSchema", {}),
                        "output_schema": tool.get("outputSchema", {}),
                    },
                }

                normalized.append(normalized_tool)

            except Exception as e:
                logger.warning(
                    "Failed to normalize MCP tool %s: %s",
                    (
                        tool.get("name", "unknown")
                        if tool and isinstance(tool, dict)
                        else "unknown"
                    ),
                    e,
                )
                continue

        return normalized

    def _generate_container_name(
        self, image_name: str, prefix: str = "mcp-discovery"
    ) -> str:
        """Generate a unique container name for discovery."""
        import time

        safe_name = image_name.replace("/", "-").replace(":", "-")
        timestamp = int(time.time())
        return f"{prefix}-{safe_name}-{timestamp}"

    def _prepare_environment_variables(
        self, env_vars: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Prepare environment variables for container execution."""
        final_env = env_vars.copy() if env_vars else {}

        # Ensure MCP transport is set
        if "MCP_TRANSPORT" not in final_env:
            final_env["MCP_TRANSPORT"] = "stdio"

        # Reduce logging noise for discovery
        if "MCP_LOG_LEVEL" not in final_env:
            final_env["MCP_LOG_LEVEL"] = "ERROR"

        return final_env

    def _should_use_stdio_discovery(self, image_name: str) -> bool:
        """Determine if stdio discovery should be attempted for this image."""
        # For now, attempt stdio for all images, but this could be extended
        # to check image labels, annotations, or known image patterns
        return True

    def _should_use_http_discovery(self, image_name: str) -> bool:
        """Determine if HTTP discovery should be attempted for this image."""
        # Attempt HTTP discovery as fallback for all images
        return True

    async def _async_discover_via_http(self, endpoint: str, timeout: int) -> List[Dict]:
        """
        Async MCP JSON-RPC discovery using unified MCPConnection.

        This method uses the MCPConnection with smart endpoint discovery
        for consistent FastMCP protocol handling.

        Args:
            endpoint: HTTP endpoint URL for the MCP server
            timeout: Timeout for the entire discovery process

        Returns:
            List of discovered tools, empty list if discovery fails
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(endpoint)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Use unified MCPConnection with smart endpoint discovery
            tools = await self._try_mcp_connection_smart(base_url, timeout)
            if tools:
                logger.info(f"Discovered {len(tools)} tools via smart MCP connection")
                return tools

            # If smart discovery fails, try with the specific endpoint path
            if parsed.path and parsed.path != "/":
                tools = await self._try_mcp_handshake(endpoint, timeout)
                if tools:
                    logger.info(f"Discovered {len(tools)} tools via specific endpoint")
                    return tools

            return []

        except Exception as e:
            logger.debug(f"Async MCP discovery failed for {endpoint}: {e}")
            return []

    async def _try_direct_tools_list(self, endpoint: str, timeout: int) -> List[Dict]:
        """Try direct tools/list MCP call."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                }

                # Support both standard MCP and FastMCP Streamable-HTTP
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",  # FastMCP requirement
                }

                logger.debug(f"Trying direct tools/list call to {endpoint}")
                async with session.post(
                    endpoint, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        result = await self._parse_mcp_response(response)
                        if (
                            result
                            and result.get("result")
                            and "tools" in result["result"]
                        ):
                            return result["result"]["tools"]
            return []
        except Exception as e:
            logger.debug(f"Direct tools/list failed: {e}")
            return []

    async def _try_mcp_connection_smart(
        self, base_url: str, timeout: int
    ) -> List[Dict]:
        """Try MCP connection with smart endpoint discovery using MCPConnection."""
        try:
            logger.debug(f"Trying smart MCP connection to {base_url}")

            # Use MCPConnection for unified protocol handling with smart discovery
            connection = MCPConnection(timeout=timeout)

            try:
                # Connect via HTTP with smart endpoint discovery
                success = await connection.connect_http_smart(base_url)
                if not success:
                    return []

                # List tools using the connection
                tools = await connection.list_tools()
                if tools:
                    logger.debug(f"Found {len(tools)} tools via smart MCP connection")
                    return self._normalize_mcp_tools(tools)
                else:
                    logger.debug("No tools found via smart MCP connection")
                    return []

            finally:
                await connection.disconnect()

        except Exception as e:
            logger.debug(f"Smart MCP connection failed for {base_url}: {e}")
            return []

    async def _try_mcp_handshake(self, endpoint: str, timeout: int) -> List[Dict]:
        """Try full MCP handshake using unified MCPConnection."""
        try:
            # Parse URL to get base URL and path
            from urllib.parse import urlparse

            parsed = urlparse(endpoint)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            path = parsed.path or "/mcp"

            logger.debug(f"Trying MCP handshake to {endpoint}")

            # Use MCPConnection for unified protocol handling
            connection = MCPConnection(timeout=timeout)

            try:
                # Connect via HTTP with specific endpoint
                success = await connection.connect_http(base_url, path)
                if not success:
                    return []

                # List tools using the connection
                tools = await connection.list_tools()
                if tools:
                    logger.debug(f"Found {len(tools)} tools via MCP connection")
                    return self._normalize_mcp_tools(tools)
                else:
                    logger.debug("No tools found via MCP connection")
                    return []

            finally:
                await connection.disconnect()

        except Exception as e:
            logger.debug(f"MCP handshake failed for {endpoint}: {e}")
            return []

    async def _parse_mcp_response(
        self, response: aiohttp.ClientResponse
    ) -> Optional[Dict]:
        """Parse MCP response handling both JSON and SSE formats."""
        try:
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                # Standard JSON response
                return await response.json()
            elif "text/event-stream" in content_type:
                # FastMCP SSE response - parse Server-Sent Events format
                text = await response.text()
                lines = text.strip().split("\n")

                # Parse SSE format: event: message\ndata: {...}
                for i, line in enumerate(lines):
                    if line.startswith("data: "):
                        json_data = line[6:]  # Remove 'data: ' prefix
                        if json_data.strip():
                            import json

                            return json.loads(json_data)
                    elif line.startswith("data:"):
                        json_data = line[5:]  # Remove 'data:' prefix
                        if json_data.strip():
                            import json

                            return json.loads(json_data)
            else:
                # Try parsing as JSON anyway
                return await response.json()
        except Exception as e:
            logger.debug(f"Failed to parse MCP response: {e}")
            return None

    async def _try_websocket_connection(
        self, ws_endpoint: str, timeout: int
    ) -> List[Dict]:
        """Try WebSocket connection for MCP (some servers prefer this)."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.ws_connect(ws_endpoint) as ws:
                    # Send initialize
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "mcp-template", "version": "1.0.0"},
                        },
                    }

                    await ws.send_str(json.dumps(init_msg))

                    # Wait for initialize response
                    msg = await ws.receive()
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        return []

                    # Send initialized notification
                    notif_msg = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                    }
                    await ws.send_str(json.dumps(notif_msg))

                    # Request tools
                    tools_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    }
                    await ws.send_str(json.dumps(tools_msg))

                    # Get tools response
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        result = json.loads(msg.data)
                        if result.get("result") and "tools" in result["result"]:
                            return result["result"]["tools"]

            return []
        except Exception as e:
            logger.debug(f"WebSocket connection failed: {e}")
            return []

    def discover_tools_from_endpoint(
        self, endpoint: str, timeout: int = 30
    ) -> List[Dict]:
        """
        Discover tools from an existing MCP endpoint.

        This is a convenience method for ToolManager and other components
        that need to discover tools from already running MCP servers.

        Args:
            endpoint: HTTP endpoint URL for the MCP server
            timeout: Timeout for the discovery process

        Returns:
            List of discovered tools
        """
        return asyncio.run(self._async_discover_via_http(endpoint, timeout))

    def discover_tools_from_deployment(
        self, deployment_info: Dict, timeout: int = 30
    ) -> List[Dict]:
        """
        Discover tools from a running deployment via HTTP.

        This method intelligently resolves endpoints and tests multiple patterns:
        1. User-provided endpoint as-is
        2. Common MCP patterns (/mcp, /tools, etc.)
        3. For Kubernetes ClusterIP, falls back to port-forwarding if needed

        Args:
            deployment_info: Dictionary containing deployment details (ports, host, etc.)
            timeout: Timeout for the discovery process

        Returns:
            List of discovered tools, empty list if discovery fails
        """
        try:
            candidate_endpoints = self._resolve_candidate_endpoints(deployment_info)

            # Try each candidate endpoint with multiple HTTP discovery approaches
            for endpoint in candidate_endpoints:
                logger.debug(f"Trying endpoint: {endpoint}")
                tools = self._try_endpoint_with_patterns(endpoint, timeout)
                if tools:
                    logger.info(f"✓ Successfully discovered tools from {endpoint}")
                    return tools

            # If all direct endpoints failed for Kubernetes ClusterIP, try port-forwarding
            if self._is_kubernetes_cluster_ip_endpoint(deployment_info):
                tools = self._try_kubernetes_port_forward(deployment_info, timeout)
                if tools:
                    return tools

            logger.debug("All endpoint discovery attempts failed")
            return []

        except Exception as e:
            logger.error(f"Failed to discover tools from deployment: {e}")
            return []

    def _resolve_candidate_endpoints(self, deployment_info: Dict) -> List[str]:
        """
        Resolve candidate endpoints from deployment information.

        Returns a prioritized list of endpoints to try.
        """
        endpoints = []

        # Priority 1: Pre-constructed endpoint from backend (user-provided or backend-computed)
        if "endpoint" in deployment_info and deployment_info["endpoint"]:
            base_endpoint = deployment_info["endpoint"]

            # For Kubernetes service endpoints, try ClusterIP resolution first
            if ".svc.cluster.local" in base_endpoint:
                resolved_endpoint = self._resolve_kubernetes_cluster_ip(
                    base_endpoint, deployment_info
                )
                if resolved_endpoint:
                    endpoints.append(resolved_endpoint)
            else:
                # User-provided or Docker endpoint - use as-is
                endpoints.append(base_endpoint)

        # Priority 2: Construct from port information (Docker format)
        port_endpoints = self._construct_endpoints_from_ports(deployment_info)
        endpoints.extend(port_endpoints)

        return endpoints

    def _resolve_kubernetes_cluster_ip(
        self, service_endpoint: str, deployment_info: Dict
    ) -> Optional[str]:
        """
        Resolve Kubernetes service endpoint to accessible ClusterIP.

        Args:
            service_endpoint: Service endpoint like "http://demo-c79670ff.mcp-servers.svc.cluster.local:8080"
            deployment_info: Deployment information

        Returns:
            Resolved endpoint or None if resolution fails
        """
        try:
            import re

            # Extract port from service endpoint
            port_match = re.search(r":(\d+)$", service_endpoint)
            if not port_match:
                return None

            port = port_match.group(1)

            # For Kubernetes probe, try to get ClusterIP from the backend
            if hasattr(self, "core_v1") and hasattr(self, "namespace"):
                deployment_name = deployment_info.get("name") or deployment_info.get(
                    "id"
                )
                if deployment_name:
                    try:
                        from kubernetes.client.rest import ApiException

                        service = self.core_v1.read_namespaced_service(
                            name=deployment_name, namespace=self.namespace
                        )
                        cluster_ip = service.spec.cluster_ip
                        if cluster_ip and cluster_ip != "None":
                            return f"http://{cluster_ip}:{port}"
                    except ApiException:
                        pass

            # Fallback: assume localhost with potential port-forward
            return f"http://127.0.0.1:{port}"

        except Exception as e:
            logger.debug(f"Failed to resolve Kubernetes ClusterIP: {e}")
            return None

    def _construct_endpoints_from_ports(self, deployment_info: Dict) -> List[str]:
        """
        Construct endpoints from port information in deployment info.
        """
        endpoints = []
        ports = deployment_info.get("ports", "")

        # For Kubernetes deployments, extract port from spec
        if not ports and "spec" in deployment_info:
            try:
                containers = deployment_info["spec"]["template"]["spec"]["containers"]
                for container in containers:
                    container_ports = container.get("ports", [])
                    for port_spec in container_ports:
                        if port_spec.get("name") == "http":
                            ports = f"{port_spec['containerPort']}/tcp"
                            break
                    if ports:
                        break
            except (KeyError, TypeError, IndexError):
                pass

        if ports:
            # Parse port mapping like "7071->7071" or just "7071" to extract external port
            if "->" in ports:
                external_port = ports.split("->")[0]
            else:
                # Remove /tcp suffix if present
                external_port = ports.split("/")[0]

            # Get host - handle both Docker and Kubernetes
            host = deployment_info.get("host")

            # For Kubernetes, try to get service cluster IP
            if not host and "service_info" in deployment_info:
                try:
                    host = deployment_info["service_info"]["spec"]["clusterIP"]
                except (KeyError, TypeError):
                    pass

            # Fallback to environment variable or localhost
            if not host:
                host = os.getenv("MCP_HOST", "127.0.0.1")

            # Construct endpoint URL
            endpoint = f"http://{host}:{external_port}"
            endpoints.append(endpoint)

            logger.debug(f"Constructed endpoint from port info: {endpoint}")

        return endpoints

    def _try_endpoint_with_patterns(
        self, base_endpoint: str, timeout: int
    ) -> List[Dict]:
        """
        Try an endpoint with smart MCPConnection discovery.

        Uses MCPConnection's smart endpoint discovery which automatically
        tests common MCP paths and handles FastMCP protocol properly.
        """

        async def _try_mcp_smart_discovery():
            connection = MCPConnection(timeout=timeout)
            try:
                # Use smart endpoint discovery - this handles all the patterns internally
                success = await connection.connect_http_smart(base_endpoint)
                if success:
                    tools = await connection.list_tools()
                    if tools:
                        return self._normalize_mcp_tools(tools)
            finally:
                await connection.disconnect()
            return []

        # Run async discovery in sync context
        try:
            return asyncio.run(_try_mcp_smart_discovery())
        except Exception as e:
            logger.debug(f"Smart MCP discovery failed for {base_endpoint}: {e}")
            return []

    def _is_kubernetes_cluster_ip_endpoint(self, deployment_info: Dict) -> bool:
        """
        Check if this is a Kubernetes ClusterIP endpoint that might need port-forwarding.
        """
        endpoint = deployment_info.get("endpoint", "")
        return ".svc.cluster.local" in endpoint or (
            hasattr(self, "namespace") and "10." in endpoint
        )  # Common ClusterIP range

    def _try_kubernetes_port_forward(
        self, deployment_info: Dict, timeout: int
    ) -> List[Dict]:
        """
        Try Kubernetes port-forwarding as a last resort for ClusterIP services.

        This sets up a temporary port-forward and tests the endpoint.
        """
        try:
            import socket
            import subprocess
            import time

            deployment_name = deployment_info.get("name") or deployment_info.get("id")
            if not deployment_name:
                return []

            # Extract port from endpoint or deployment info
            port = "8080"  # Default
            endpoint = deployment_info.get("endpoint", "")
            if endpoint:
                import re

                port_match = re.search(r":(\d+)", endpoint)
                if port_match:
                    port = port_match.group(1)

            # Find a free local port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                local_port = s.getsockname()[1]

            # Start port-forward in background
            cmd = [
                "kubectl",
                "port-forward",
                f"service/{deployment_name}",
                f"{local_port}:{port}",
                "-n",
                getattr(self, "namespace", "default"),
            ]

            logger.info(f"Starting kubectl port-forward: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Give port-forward time to establish
            time.sleep(2)

            try:
                # Test the forwarded endpoint
                forwarded_endpoint = f"http://127.0.0.1:{local_port}"
                tools = self._try_endpoint_with_patterns(forwarded_endpoint, timeout)
                return tools
            finally:
                # Clean up port-forward
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()

        except Exception as e:
            logger.debug(f"Port-forward attempt failed: {e}")
            return []
