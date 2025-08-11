"""
HTTP-based tool calling implementation for MCP servers.

This module provides efficient HTTP-based tool calling functionality for deployed MCP servers.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class HTTPToolCaller:
    """HTTP-based tool caller for MCP servers."""

    def __init__(self, timeout: int = 30):
        """
        Initialize HTTP tool caller.

        Args:
            timeout: Timeout for HTTP requests
        """
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def call_tool(
        self,
        server_url: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool on an HTTP MCP server.

        Args:
            server_url: Base URL of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            session_id: Optional session ID for stateful calls

        Returns:
            Dictionary containing tool response
        """
        if not self.session:
            raise RuntimeError("HTTPToolCaller must be used as async context manager")

        # Construct MCP call URL
        if not server_url.endswith("/"):
            server_url += "/"

        call_url = f"{server_url}tools/call"

        # Prepare request payload
        payload = {"name": tool_name, "arguments": arguments}

        if session_id:
            payload["sessionId"] = session_id

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            logger.info("Calling tool %s on %s", tool_name, server_url)

            async with self.session.post(
                call_url, json=payload, headers=headers
            ) as response:
                response_text = await response.text()

                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        return {
                            "status": "success",
                            "result": result,
                            "tool_name": tool_name,
                            "method": "http",
                        }
                    except json.JSONDecodeError:
                        return {
                            "status": "success",
                            "result": {
                                "content": [{"type": "text", "text": response_text}]
                            },
                            "tool_name": tool_name,
                            "method": "http",
                        }
                else:
                    logger.error(
                        "HTTP tool call failed: %s %s", response.status, response_text
                    )
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}: {response_text}",
                        "tool_name": tool_name,
                        "method": "http",
                    }

        except asyncio.TimeoutError:
            logger.error("Timeout calling tool %s on %s", tool_name, server_url)
            return {
                "status": "error",
                "error": f"Timeout after {self.timeout}s",
                "tool_name": tool_name,
                "method": "http",
            }
        except Exception as e:
            logger.error("Error calling tool %s on %s: %s", tool_name, server_url, e)
            return {
                "status": "error",
                "error": str(e),
                "tool_name": tool_name,
                "method": "http",
            }

    def call_tool_sync(
        self,
        server_url: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for HTTP tool calling.

        Args:
            server_url: Base URL of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            session_id: Optional session ID for stateful calls

        Returns:
            Dictionary containing tool response
        """

        async def _call():
            async with HTTPToolCaller(self.timeout) as caller:
                return await caller.call_tool(
                    server_url, tool_name, arguments, session_id
                )

        try:
            return asyncio.run(_call())
        except Exception as e:
            logger.error("Error in synchronous tool call: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "tool_name": tool_name,
                "method": "http_sync",
            }

    async def list_tools(self, server_url: str) -> Dict[str, Any]:
        """
        List available tools on an HTTP MCP server.

        Args:
            server_url: Base URL of the MCP server

        Returns:
            Dictionary containing available tools
        """
        if not self.session:
            raise RuntimeError("HTTPToolCaller must be used as async context manager")

        # Construct MCP tools URL
        if not server_url.endswith("/"):
            server_url += "/"

        tools_url = f"{server_url}tools/list"

        headers = {"Accept": "application/json"}

        try:
            logger.info("Listing tools from %s", server_url)

            async with self.session.get(tools_url, headers=headers) as response:
                response_text = await response.text()

                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        return {
                            "status": "success",
                            "tools": result.get("tools", []),
                            "method": "http",
                        }
                    except json.JSONDecodeError:
                        return {
                            "status": "error",
                            "error": "Invalid JSON response from server",
                            "method": "http",
                        }
                else:
                    logger.error(
                        "HTTP tools list failed: %s %s", response.status, response_text
                    )
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}: {response_text}",
                        "method": "http",
                    }

        except asyncio.TimeoutError:
            logger.error("Timeout listing tools from %s", server_url)
            return {
                "status": "error",
                "error": f"Timeout after {self.timeout}s",
                "method": "http",
            }
        except Exception as e:
            logger.error("Error listing tools from %s: %s", server_url, e)
            return {"status": "error", "error": str(e), "method": "http"}

    def list_tools_sync(self, server_url: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for HTTP tool listing.

        Args:
            server_url: Base URL of the MCP server

        Returns:
            Dictionary containing available tools
        """

        async def _list():
            async with HTTPToolCaller(self.timeout) as caller:
                return await caller.list_tools(server_url)

        try:
            return asyncio.run(_list())
        except Exception as e:
            logger.error("Error in synchronous tool listing: %s", e)
            return {"status": "error", "error": str(e), "method": "http_sync"}

    async def check_server_health(self, server_url: str) -> Dict[str, Any]:
        """
        Check if an HTTP MCP server is healthy and responsive.

        Args:
            server_url: Base URL of the MCP server

        Returns:
            Dictionary containing health status
        """
        if not self.session:
            raise RuntimeError("HTTPToolCaller must be used as async context manager")

        # Try both /health and /tools/list endpoints
        if not server_url.endswith("/"):
            server_url += "/"

        health_url = f"{server_url}health"
        tools_url = f"{server_url}tools/list"

        headers = {"Accept": "application/json"}

        try:
            # Try health endpoint first
            try:
                async with self.session.get(health_url, headers=headers) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "url": server_url,
                            "endpoint": "health",
                        }
            except:
                pass

            # Fall back to tools list endpoint
            async with self.session.get(tools_url, headers=headers) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "url": server_url,
                        "endpoint": "tools/list",
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "url": server_url,
                        "error": f"HTTP {response.status}",
                    }

        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "url": server_url,
                "error": f"Timeout after {self.timeout}s",
            }
        except Exception as e:
            return {"status": "unhealthy", "url": server_url, "error": str(e)}

    def check_server_health_sync(self, server_url: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for HTTP server health check.

        Args:
            server_url: Base URL of the MCP server

        Returns:
            Dictionary containing health status
        """

        async def _check():
            async with HTTPToolCaller(self.timeout) as caller:
                return await caller.check_server_health(server_url)

        try:
            return asyncio.run(_check())
        except Exception as e:
            logger.error("Error in synchronous health check: %s", e)
            return {"status": "unhealthy", "url": server_url, "error": str(e)}
