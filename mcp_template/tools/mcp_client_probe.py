"""
MCP Client probe for discovering tools from MCP servers via stdio.
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClientProbe:
    """Client for probing MCP servers to discover their tools."""

    def __init__(self, timeout: int = 30):
        """
        Initialize MCP client probe.

        Args:
            timeout: Timeout for MCP communication
        """
        self.timeout = timeout

    async def discover_tools_from_command(
        self, command: List[str], working_dir: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server via command line.

        Args:
            command: Command to run MCP server
            working_dir: Working directory for command

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        try:
            logger.info("Starting MCP server with command: %s", " ".join(command))

            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                # Initialize MCP connection
                result = await self._initialize_mcp_session(process)
                if not result:
                    return None

                # List tools
                tools = await self._list_tools(process)
                if not tools:
                    return None

                return {
                    "discovery_method": "mcp_client",
                    "timestamp": time.time(),
                    "tools": self._normalize_mcp_tools(tools),
                    "command": command,
                    "server_info": result.get("serverInfo", {}),
                }

            finally:
                # Cleanup process
                try:
                    if process.returncode is None:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=5)
                except (ProcessLookupError, asyncio.TimeoutError):
                    try:
                        process.kill()
                        await process.wait()
                    except ProcessLookupError:
                        pass

        except Exception as e:
            logger.error("Failed to discover tools from MCP server: %s", e)
            return None

    async def discover_tools_from_docker_mcp(
        self, image_name: str, args: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server running in Docker.

        Args:
            image_name: Docker image name
            args: Additional arguments for the MCP server

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        container_name = f"mcp-discovery-{image_name.replace('/', '-').replace(':', '-')}-{int(time.time())}"

        try:
            # Build docker command
            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "-i",
                "--name",
                container_name,
                image_name,
            ]

            if args:
                docker_cmd.extend(args)

            return await self.discover_tools_from_command(docker_cmd)

        except Exception as e:
            logger.error(
                "Failed to discover tools from Docker MCP server %s: %s", image_name, e
            )
            return None
        finally:
            # Cleanup container if it's still running
            try:
                process = await asyncio.create_subprocess_exec(
                    "docker",
                    "stop",
                    container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(process.wait(), timeout=10)
            except Exception:
                pass

    async def _initialize_mcp_session(
        self, process: asyncio.subprocess.Process
    ) -> Optional[Dict[str, Any]]:
        """Initialize MCP session with the server."""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "mcp-tool-discovery", "version": "1.0.0"},
                },
            }

            # Send request
            request_line = json.dumps(init_request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=self.timeout
            )

            if not response_line:
                logger.error("No response from MCP server during initialization")
                return None

            response = json.loads(response_line.decode().strip())

            if "error" in response:
                logger.error("MCP initialization error: %s", response["error"])
                return None

            logger.debug("MCP server initialized successfully")
            return response.get("result", {})

        except asyncio.TimeoutError:
            logger.error("Timeout during MCP initialization")
            return None
        except Exception as e:
            logger.error("Error during MCP initialization: %s", e)
            return None

    async def _list_tools(
        self, process: asyncio.subprocess.Process
    ) -> Optional[List[Dict[str, Any]]]:
        """List tools from MCP server."""
        try:
            # Send tools/list request
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }

            # Send request
            request_line = json.dumps(list_request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=self.timeout
            )

            if not response_line:
                logger.error("No response from MCP server for tools/list")
                return None

            response = json.loads(response_line.decode().strip())

            if "error" in response:
                logger.error("MCP tools/list error: %s", response["error"])
                return None

            tools = response.get("result", {}).get("tools", [])
            logger.info("Found %d tools from MCP server", len(tools))
            return tools

        except asyncio.TimeoutError:
            logger.error("Timeout during MCP tools/list")
            return None
        except Exception as e:
            logger.error("Error during MCP tools/list: %s", e)
            return None

    def _normalize_mcp_tools(
        self, mcp_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize MCP tools to standard format."""
        normalized = []

        for tool in mcp_tools:
            try:
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
                    tool.get("name", "unknown"),
                    e,
                )
                continue

        return normalized

    def discover_tools_sync(
        self, command: List[str], working_dir: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for discovering tools."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.discover_tools_from_command(command, working_dir)
            )
        finally:
            loop.close()

    def discover_tools_from_docker_sync(
        self, image_name: str, args: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for discovering tools from Docker."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.discover_tools_from_docker_mcp(image_name, args)
            )
        finally:
            loop.close()
