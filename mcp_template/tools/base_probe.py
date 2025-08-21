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
        Async MCP JSON-RPC discovery with proper session management.

        This method implements the official MCP protocol handshake:
        1. initialize request with protocol version and capabilities
        2. notifications/initialized notification
        3. tools/list request to get available tools

        Args:
            endpoint: HTTP endpoint URL for the MCP server
            timeout: Timeout for the entire discovery process

        Returns:
            List of discovered tools, empty list if discovery fails
        """
        try:
            # Try multiple MCP connection approaches
            tools = []

            # Approach 1: Direct tools/list call
            tools = await self._try_direct_tools_list(endpoint, timeout)
            if tools:
                logger.info(f"Discovered {len(tools)} tools via direct tools/list")
                return tools

            # Approach 2: Full MCP handshake (like VS Code does)
            tools = await self._try_mcp_handshake(endpoint, timeout)
            if tools:
                logger.info(f"Discovered {len(tools)} tools via MCP handshake")
                return tools

            # Approach 3: WebSocket connection (if HTTP fails)
            ws_endpoint = endpoint.replace("http://", "ws://").replace(
                "/mcp", "/mcp/ws"
            )
            tools = await self._try_websocket_connection(ws_endpoint, timeout)
            if tools:
                logger.info(f"Discovered {len(tools)} tools via WebSocket")
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

                logger.debug(f"Trying direct tools/list call to {endpoint}")
                async with session.post(
                    endpoint, json=payload, headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("result") and "tools" in result["result"]:
                            return result["result"]["tools"]
            return []
        except Exception as e:
            logger.debug(f"Direct tools/list failed: {e}")
            return []

    async def _try_mcp_handshake(self, endpoint: str, timeout: int) -> List[Dict]:
        """Try full MCP handshake like VS Code MCP clients do."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                # Step 1: Initialize connection
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {},
                        },
                        "clientInfo": {"name": "mcp-template", "version": "1.0.0"},
                    },
                }

                logger.debug(f"Trying MCP handshake to {endpoint}")
                async with session.post(
                    endpoint,
                    json=init_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        return []

                    init_result = await response.json()
                    if init_result.get("error"):
                        logger.debug(f"MCP initialize failed: {init_result['error']}")
                        return []

                # Step 2: Send initialized notification
                notif_payload = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }

                async with session.post(
                    endpoint,
                    json=notif_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    pass  # Notification doesn't need response

                # Step 3: List tools
                tools_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }

                async with session.post(
                    endpoint,
                    json=tools_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("result") and "tools" in result["result"]:
                            return result["result"]["tools"]

            return []
        except Exception as e:
            logger.debug(f"MCP handshake failed: {e}")
            return []

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
