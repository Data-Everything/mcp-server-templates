"""
MCP Connection handling for stdio, HTTP, and websocket protocols.

This module provides a unified interface for connecting to MCP servers
using different transport methods (stdio, HTTP, websocket, etc.) and handles
the MCP protocol negotiation and communication, including FastMCP support.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MCPConnection:
    """
    Manages connections to MCP servers using different transport protocols.

    Supports:
    - stdio: Direct process communication
    - http: HTTP-based communication with FastMCP protocol support
    - websocket: WebSocket-based communication (future)
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize MCP connection.

        Args:
            timeout: Timeout for MCP operations in seconds
        """
        self.timeout = timeout
        self.process = None
        self.session_info = None
        self.server_info = None

        # HTTP transport properties
        self.base_url = None
        self.session_id = None
        self.http_session = None
        self.transport_type = None

    async def connect_http_smart(
        self,
        base_url: str,
        endpoints: Optional[List[str]] = None,
    ) -> bool:
        """
        Connect to MCP server via HTTP with smart endpoint discovery.

        Tries multiple common MCP endpoints until one works.

        Args:
            base_url: Base URL of the HTTP server (e.g., "http://localhost:7071")
            endpoints: List of endpoints to try (defaults to common patterns)

        Returns:
            True if connection successful, False otherwise
        """
        if endpoints is None:
            endpoints = ["/mcp", "/", "/tools", "/api/mcp", "/v1/mcp"]

        for endpoint in endpoints:
            try:
                logger.debug(f"Trying endpoint: {base_url}{endpoint}")
                if await self.connect_http(base_url, endpoint):
                    logger.info(f"Successfully connected to {base_url}{endpoint}")
                    return True
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue

        logger.error(f"Failed to connect to any endpoint on {base_url}")
        return False

    async def connect_http(
        self,
        base_url: str,
        endpoint: str = "/mcp",
    ) -> bool:
        """
        Connect to MCP server via HTTP with FastMCP protocol support.

        Args:
            base_url: Base URL of the HTTP server (e.g., "http://localhost:7071")
            endpoint: MCP endpoint path (default: "/mcp")

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.base_url = base_url.rstrip("/")
            self.transport_type = "http"

            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.http_session = aiohttp.ClientSession(timeout=timeout)

            logger.info(f"Connecting to MCP server via HTTP: {self.base_url}{endpoint}")

            # Initialize MCP session
            init_result = await self._initialize_mcp_session_http(endpoint)
            if init_result:
                logger.info("Successfully connected to MCP server via HTTP")
                return True
            else:
                logger.error("Failed to initialize HTTP MCP session")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server: {e}")
            await self.disconnect()
            return False

    async def connect_stdio(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Connect to MCP server via stdio.

        Args:
            command: Command to execute MCP server
            working_dir: Working directory for the process
            env_vars: Environment variables for the process

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Connecting to MCP server via stdio: %s", " ".join(command))

            # Prepare environment
            env = None
            if env_vars:
                env = os.environ.copy()
                env.update(env_vars)

            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env,
            )

            self.transport_type = "stdio"

            # Initialize MCP session
            init_result = await self._initialize_mcp_session()
            if init_result:
                logger.info("Successfully connected to MCP server")
                return True
            else:
                logger.error("Failed to initialize MCP session")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error("Failed to connect to MCP server: %s", e)
            await self.disconnect()
            return False

    async def _initialize_mcp_session_http(self, endpoint: str = "/mcp") -> bool:
        """
        Initialize MCP session with HTTP server (FastMCP compatible).

        Args:
            endpoint: MCP endpoint path

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.http_session:
            return False

        try:
            full_url = f"{self.base_url}{endpoint}"

            # Send initialization request with FastMCP headers
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                    "clientInfo": {"name": "mcp-template-client", "version": "0.4.0"},
                },
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            async with self.http_session.post(
                full_url, json=init_request, headers=headers
            ) as response:
                if response.status == 200:
                    response_text = await response.text()

                    # Extract session ID for FastMCP
                    self.session_id = response.headers.get("mcp-session-id")
                    if self.session_id:
                        logger.debug(f"FastMCP session ID: {self.session_id[:8]}...")

                    # Parse response (handle both JSON and SSE formats)
                    result = self._parse_http_response(response_text)
                    if result and "result" in result:
                        self.session_info = result["result"]
                        self.server_info = result["result"].get("serverInfo", {})

                        # Send initialized notification (no response expected)
                        initialized_notification = {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                        }

                        # Add session ID to headers if available
                        if self.session_id:
                            headers["mcp-session-id"] = self.session_id

                        await self._send_http_notification(
                            full_url, initialized_notification, headers
                        )
                        return True
                    else:
                        logger.error(f"Invalid initialization response: {result}")
                        return False
                else:
                    logger.error(f"HTTP initialization failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"HTTP MCP session initialization failed: {e}")
            return False

    def _parse_http_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse HTTP response, handling both JSON and FastMCP SSE formats.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON response or None if failed
        """
        try:
            # First try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try SSE format parsing (FastMCP)
            try:
                lines = response_text.strip().split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("data: "):
                        data_content = line[6:]  # Remove "data: " prefix
                        return json.loads(data_content)
                return None
            except Exception as e:
                logger.error(f"Failed to parse SSE response: {e}")
                return None

    async def _send_http_notification(
        self, url: str, notification: Dict[str, Any], headers: Dict[str, str]
    ) -> None:
        """
        Send HTTP notification (no response expected).

        Args:
            url: Target URL
            notification: JSON-RPC notification object
            headers: HTTP headers
        """
        try:
            async with self.http_session.post(url, json=notification, headers=headers):
                # Notification, we don't need to process the response
                pass
        except Exception as e:
            logger.debug(f"Failed to send HTTP notification: {e}")

    async def _initialize_mcp_session(self) -> bool:
        """
        Initialize MCP session with the server.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.process:
            return False

        try:
            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "mcp-template-client", "version": "0.4.0"},
                },
            }

            response = await self._send_request(init_request)
            if response and "result" in response:
                self.session_info = response["result"]
                self.server_info = response["result"].get("serverInfo", {})

                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }
                await self._send_notification(initialized_notification)

                return True
            else:
                logger.error("Invalid initialization response: %s", response)
                return False

        except Exception as e:
            logger.error("MCP session initialization failed: %s", e)
            return False

    async def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions or None if failed
        """
        if self.transport_type == "http":
            return await self._list_tools_http()
        elif self.transport_type == "stdio":
            return await self._list_tools_stdio()
        else:
            logger.error("No active MCP connection")
            return None

    async def _list_tools_http(self) -> Optional[List[Dict[str, Any]]]:
        """List tools via HTTP transport."""
        if not self.http_session or not self.base_url:
            logger.error("No active HTTP MCP connection")
            return None

        try:
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            # Add session ID if available (FastMCP)
            if self.session_id:
                headers["mcp-session-id"] = self.session_id

            full_url = f"{self.base_url}/mcp"  # Default endpoint
            async with self.http_session.post(
                full_url, json=request, headers=headers
            ) as response:
                if response.status == 200:
                    response_text = await response.text()
                    result = self._parse_http_response(response_text)

                    if result and "result" in result and "tools" in result["result"]:
                        return result["result"]["tools"]
                    else:
                        logger.error(f"Invalid HTTP tools/list response: {result}")
                        return None
                else:
                    logger.error(f"HTTP tools/list failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to list tools via HTTP: {e}")
            return None

    async def _list_tools_stdio(self) -> Optional[List[Dict[str, Any]]]:
        """List tools via stdio transport."""
        if not self.process:
            logger.error("No active stdio MCP connection")
            return None

        try:
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            response = await self._send_request(request)
            if response and "result" in response and "tools" in response["result"]:
                return response["result"]["tools"]
            else:
                logger.error(f"Invalid stdio tools/list response: {response}")
                return None

        except Exception as e:
            logger.error(f"Failed to list tools via stdio: {e}")
            return None

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response or None if failed
        """
        if self.transport_type == "http":
            return await self._call_tool_http(tool_name, arguments)
        elif self.transport_type == "stdio":
            return await self._call_tool_stdio(tool_name, arguments)
        else:
            logger.error("No active MCP connection")
            return None

    async def _call_tool_http(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call tool via HTTP transport."""
        if not self.http_session or not self.base_url:
            logger.error("No active HTTP MCP connection")
            return None

        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            # Add session ID if available (FastMCP)
            if self.session_id:
                headers["mcp-session-id"] = self.session_id

            full_url = f"{self.base_url}/mcp"  # Default endpoint
            async with self.http_session.post(
                full_url, json=request, headers=headers
            ) as response:
                if response.status == 200:
                    response_text = await response.text()
                    result = self._parse_http_response(response_text)

                    if result and "result" in result:
                        return result["result"]
                    else:
                        logger.error(f"Invalid HTTP tools/call response: {result}")
                        return None
                else:
                    logger.error(f"HTTP tools/call failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} via HTTP: {e}")
            return None

    async def _call_tool_stdio(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call tool via stdio transport."""
        if not self.process:
            logger.error("No active stdio MCP connection")
            return None

        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            response = await self._send_request(request)
            if response and "result" in response:
                return response["result"]
            else:
                logger.error(f"Invalid stdio tools/call response: {response}")
                return None

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} via stdio: {e}")
            return None

    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a JSON-RPC request and wait for response.

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response or None if failed
        """
        if not self.process:
            return None

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), timeout=self.timeout
            )

            if not response_line:
                return None

            response_text = response_line.decode().strip()
            if response_text:
                return json.loads(response_text)
            else:
                return None

        except asyncio.TimeoutError:
            logger.error("Request timeout after %s seconds", self.timeout)
            return None
        except Exception as e:
            logger.error("Failed to send request: %s", e)
            return None

    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC notification (no response expected).

        Args:
            notification: JSON-RPC notification object
        """
        if not self.process:
            return

        try:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()
        except Exception as e:
            logger.error("Failed to send notification: %s", e)

    async def disconnect(self) -> None:
        """Disconnect from MCP server and cleanup resources."""
        # Handle stdio cleanup
        if self.process:
            try:
                if self.process.returncode is None:
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=5)
            except (ProcessLookupError, asyncio.TimeoutError):
                try:
                    self.process.kill()
                    await self.process.wait()
                except ProcessLookupError:
                    pass
            finally:
                self.process = None

        # Handle HTTP cleanup
        if self.http_session:
            try:
                await self.http_session.close()
            except Exception as e:
                logger.debug(f"Error closing HTTP session: {e}")
            finally:
                self.http_session = None

        # Clear state
        self.session_info = None
        self.server_info = None
        self.base_url = None
        self.session_id = None
        self.transport_type = None

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if self.transport_type == "stdio":
            return self.process is not None and self.process.returncode is None
        elif self.transport_type == "http":
            return self.http_session is not None and not self.http_session.closed
        else:
            return False

    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information from initialization."""
        return self.server_info

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get session information from initialization."""
        return self.session_info
