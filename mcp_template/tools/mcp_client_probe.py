"""
MCP Client probe for discovering tools from MCP servers via stdio.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClientProbe:
    """Client for probing MCP servers to discover their tools."""

    def __init__(self, timeout: int = 15):
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
        self,
        image_name: str,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server running in Docker.

        Args:
            image_name: Docker image name
            args: Additional arguments for the MCP server
            env_vars: Environment variables to pass to the container

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
            ]

            # Add environment variables
            if env_vars:
                for key, value in env_vars.items():
                    docker_cmd.extend(["-e", f"{key}={value}"])

            docker_cmd.append(image_name)

            # Add custom arguments if provided
            if args:
                docker_cmd.extend(args)

            return await self.discover_tools_from_command(docker_cmd)

        except Exception as e:
            logger.debug("MCP discovery failed for Docker server %s: %s", image_name, e)
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
        """Initialize MCP session with the server using MCP protocol version 2025-03-26."""
        try:
            # Send initialize request with proper MCP 2025-03-26 protocol
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                    "clientInfo": {"name": "ExampleClient", "version": "1.0.0"},
                },
            }

            # Send initialize request
            request_line = json.dumps(init_request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read initialization response
            init_response = await self._read_json_response(process, "initialization")
            if not init_response or "error" in init_response:
                if init_response and "error" in init_response:
                    logger.error("MCP initialization error: %s", init_response["error"])
                return None

            # Send initialized notification (no params property per MCP spec)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }

            notification_line = json.dumps(initialized_notification) + "\n"
            process.stdin.write(notification_line.encode())
            await process.stdin.drain()

            # Small delay to ensure notification is processed
            await asyncio.sleep(0.1)

            logger.debug("MCP server initialized successfully")
            return init_response.get("result", {})

        except asyncio.TimeoutError:
            logger.error("Timeout during MCP initialization")
            return None
        except Exception as e:
            logger.error("Error during MCP initialization: %s", e)
            return None

    async def _read_json_response(
        self, process: asyncio.subprocess.Process, operation: str
    ) -> Optional[Dict[str, Any]]:
        """Read JSON response from MCP server, skipping non-JSON lines."""
        max_attempts = 20  # Increased attempts to handle more startup output

        for attempt in range(max_attempts):
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=2,  # Shorter timeout per line
                )

                if not response_line:
                    logger.error(f"No response from MCP server during {operation}")
                    return None

                line = response_line.decode().strip()
                logger.debug(
                    f"Raw MCP response line {attempt + 1} for {operation}: {line}"
                )

                # Skip non-JSON lines (like "Starting MCP server with stdio transport")
                if line.startswith("{") and line.endswith("}"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue

            except asyncio.TimeoutError:
                logger.debug(
                    f"Timeout on line {attempt + 1} during {operation}, continuing..."
                )
                continue

        logger.error(
            f"No valid JSON response found from MCP server for {operation} after {max_attempts} attempts"
        )
        return None

    async def _list_tools(
        self, process: asyncio.subprocess.Process
    ) -> Optional[List[Dict[str, Any]]]:
        """List tools from MCP server using correct protocol."""
        try:
            # Send tools/list request with proper params format
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},  # Empty object, not string
            }

            # Send request
            request_line = json.dumps(list_request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read response using helper method
            response = await self._read_json_response(process, "tools/list")
            if not response:
                return None

            if "error" in response:
                logger.error("MCP tools/list error: %s", response["error"])
                return None

            tools = response.get("result", {}).get("tools", [])

            # Defensive check: ensure tools is a list
            if not isinstance(tools, list):
                logger.error(f"Expected list for tools, got {type(tools)}: {tools}")
                return []

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
        self,
        image_name: str,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for discovering tools from Docker."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.discover_tools_from_docker_mcp(image_name, args, env_vars)
            )
        finally:
            loop.close()
