"""
MCP Connection handling for stdio and websocket protocols.

This module provides a unified interface for connecting to MCP servers
using different transport methods (stdio, websocket, etc.) and handles
the MCP protocol negotiation and communication.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPConnection:
    """
    Manages connections to MCP servers using different transport protocols.

    Supports:
    - stdio: Direct process communication
    - websocket: WebSocket-based communication (future)
    - http: HTTP-based communication (existing)
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
        if not self.process:
            logger.error("No active MCP connection")
            return None

        try:
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            response = await self._send_request(request)
            if response and "result" in response and "tools" in response["result"]:
                return response["result"]["tools"]
            else:
                logger.error("Invalid tools/list response: %s", response)
                return None

        except Exception as e:
            logger.error("Failed to list tools: %s", e)
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
        if not self.process:
            logger.error("No active MCP connection")
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
                logger.error("Invalid tools/call response: %s", response)
                return None

        except Exception as e:
            logger.error("Failed to call tool %s: %s", tool_name, e)
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
                self.session_info = None
                self.server_info = None

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.process is not None and self.process.returncode is None

    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information from initialization."""
        return self.server_info

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get session information from initialization."""
        return self.session_info
