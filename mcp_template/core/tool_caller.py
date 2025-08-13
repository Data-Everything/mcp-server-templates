"""
Unified Tool Calling Interface for MCP Platform.

This module provides a shared tool calling interface that can be used by both
the CLI and Client components, ensuring consistent behavior and reducing code duplication.
"""

import json
import logging
import requests
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from mcp_template.backends.docker import DockerDeploymentService
from mcp_template.exceptions import ToolCallError
from mcp_template.core.config_manager import ConfigManager
from mcp_template.utils.config_processor import ConfigProcessor

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResult:
    """Structured result from a tool call."""

    success: bool
    result: Optional[Dict[str, Any]] = None
    content: Optional[list] = None
    is_error: bool = False
    error_message: Optional[str] = None
    raw_output: Optional[str] = None


class ToolCaller:
    """
    Unified tool calling interface for MCP Platform.

    This class provides a common interface for calling MCP tools via stdio and HTTP transports,
    used by both CLI and Client components. It handles the low-level details of
    Docker container communication and JSON-RPC protocol.

    Supports both stdio and HTTP transports, providing a consistent
    interface for tool execution across different deployment methods.
    """

    def __init__(
        self,
        backend_type: str = "docker",
        timeout: int = 30,
        caller_type: Literal["cli", "client"] = "client",
    ):
        """
        Initialize tool caller.

        Args:
            backend_type: Backend type (docker, kubernetes, mock)
            timeout: Default timeout for operations
            caller_type: Type of caller (cli or client) for behavior customization
        """
        self.backend_type = backend_type
        self.timeout = timeout
        self.caller_type = caller_type

        # Import here to avoid circular imports
        from mcp_template.utils.config_processor import ConfigProcessor
        from mcp_template.backends.docker import DockerDeploymentService

        self.config_processor = ConfigProcessor()

        # Initialize backends
        if backend_type == "docker":
            self.docker_service = DockerDeploymentService()
        else:
            self.docker_service = None  # For mock/other backends

    def _call_http_api(self, url: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make HTTP API call with error handling."""
        try:
            if method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                response = requests.get(url, timeout=self.timeout)

            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": f"Unexpected error: {e}"}

    def list_tools_from_server(
        self, endpoint: str, transport: str, timeout: int = 30
    ) -> List[Dict]:
        """List tools from a running MCP server."""
        try:
            if transport == "http":
                # Try standard tools endpoint
                tools_url = f"{endpoint.rstrip('/')}/tools"
                result = self._call_http_api(tools_url)
                if result.get("status") == "success":
                    data = result.get("data", {})
                    # Handle different response formats
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "tools" in data:
                        return data["tools"]
                    return []
            # For other transports, return empty list for now
            return []
        except Exception as e:
            logger.error(f"Failed to list tools from {endpoint}: {e}")
            return []

    def call_tool(
        self,
        endpoint: str,
        transport: str,
        tool_name: str,
        parameters: Dict,
        timeout: int = 30,
    ) -> Dict:
        """Call a tool on a running MCP server."""
        try:
            if transport == "http":
                # Call HTTP tool endpoint
                tool_url = f"{endpoint.rstrip('/')}/call/{tool_name}"
                result = self._call_http_api(tool_url, "POST", parameters)
                if result.get("status") == "success":
                    return {"success": True, "result": result.get("data")}
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                    }
            else:
                # For other transports, use stdio
                result = self.call_tool_stdio(endpoint, tool_name, parameters, timeout)
                return {
                    "success": result.success,
                    "result": result.result,
                    "error": result.error_message,
                }
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    def call_tool_stdio(
        self,
        template_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        template_config: Dict[str, Any],
        config_values: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
    ) -> ToolCallResult:
        """
        Call a tool via stdio transport.

        Args:
            template_name: Name of the template
            tool_name: Name of the tool to call
            arguments: Tool arguments
            template_config: Template configuration
            config_values: Configuration values to apply
            env_vars: Environment variables
            pull_image: Whether to pull the image

        Returns:
            ToolCallResult with structured response
        """
        if not self.docker_service:
            raise ToolCallError("Docker backend not available for stdio calls")

        # Validate stdio transport support
        transport = template_config.get("transport", {})
        default_transport = transport.get("default", "http")
        supported_transports = transport.get("supported", ["http"])

        if "stdio" not in supported_transports and default_transport != "stdio":
            raise ToolCallError(
                f"Template '{template_name}' does not support stdio transport. "
                f"Supported: {', '.join(supported_transports)}"
            )

        # Prepare configuration using the unified config processor
        config = self.config_processor.prepare_configuration(
            template=template_config,
            config_values=config_values,
            env_vars=env_vars,
        )

        # Handle volume mounts and command arguments
        template_config_dict = (
            self.config_processor.handle_volume_and_args_config_properties(
                template_config, config
            )
        )
        config = template_config_dict.get("config", config)
        template = template_config_dict.get("template", template_config)

        # Create the MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        # Convert to JSON string
        json_input = json.dumps(mcp_request)

        try:
            result = self.docker_service.run_stdio_command(
                template_name,
                config,
                template,
                json_input,
                pull_image=pull_image,
            )

            if result["status"] == "completed":
                logger.debug("Tool executed successfully via stdio")
                return self._parse_stdio_response_enhanced(result, tool_name)
            else:
                error_msg = result.get("error", "Tool execution failed")
                return ToolCallResult(
                    success=False,
                    is_error=True,
                    error_message=error_msg,
                    raw_output=result.get("stderr", ""),
                )

        except Exception as e:
            logger.error("Failed to call tool %s via stdio: %s", tool_name, e)
            raise ToolCallError(f"Stdio tool call failed: {e}")

    def call_tool_http(
        self,
        server_url: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool via HTTP transport.

        Args:
            server_url: URL of the HTTP server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool response or None if failed
        """
        try:
            # Call HTTP tool endpoint
            tool_url = f"{server_url.rstrip('/')}/call/{tool_name}"
            result = self._call_http_api(tool_url, "POST", arguments)

            if result.get("status") == "success":
                logger.debug("Tool executed successfully via HTTP")
                return result.get("data")
            else:
                logger.error("HTTP tool call failed: %s", result.get("error"))
                return None

        except Exception as e:
            logger.error("Failed to call tool %s via HTTP: %s", tool_name, e)
            raise ToolCallError(f"HTTP tool call failed: {e}")

    def _parse_stdio_response_enhanced(
        self, docker_result: Dict[str, Any], tool_name: str
    ) -> ToolCallResult:
        """
        Parse the stdio response from Docker execution with enhanced structure.

        Args:
            docker_result: Result from Docker stdio execution
            tool_name: Name of the tool that was called

        Returns:
            Parsed ToolCallResult with structured content
        """
        stdout_content = docker_result.get("stdout", "")
        stderr_content = docker_result.get("stderr", "")

        # Try to find JSON-RPC responses in stdout
        json_responses = []
        for line in stdout_content.split("\n"):
            line = line.strip()
            if (
                line.startswith('{"jsonrpc"')
                or line.startswith('{"result"')
                or line.startswith('{"error"')
            ):
                try:
                    json_response = json.loads(line)
                    json_responses.append(json_response)
                except json.JSONDecodeError:
                    continue

        # Find the tool call response (should be the last response or one with id=3)
        tool_response = None
        for response in json_responses:
            if response.get("id") == 3:  # Tool call has id=3 in our sequence
                tool_response = response
                break

        # If no id=3 response, use the last response (might be the tool result)
        if not tool_response and json_responses:
            tool_response = json_responses[-1]

        if not tool_response:
            # No JSON response found, might be plain text or error
            if stderr_content:
                return ToolCallResult(
                    success=False,
                    is_error=True,
                    error_message=f"Tool '{tool_name}' failed",
                    raw_output=stderr_content,
                )
            else:
                # Plain text response
                content = [{"type": "text", "text": stdout_content.strip()}]
                return ToolCallResult(
                    success=True,
                    result={
                        "content": content,
                        "structuredContent": {"result": stdout_content.strip()},
                        "isError": False,
                    },
                    content=content,
                    is_error=False,
                    raw_output=stdout_content,
                )

        # Parse JSON-RPC response
        if "error" in tool_response:
            error_info = tool_response["error"]
            error_message = error_info.get("message", f"Tool '{tool_name}' failed")
            return ToolCallResult(
                success=False,
                is_error=True,
                error_message=error_message,
                raw_output=stdout_content,
            )

        if "result" not in tool_response:
            return ToolCallResult(
                success=False,
                is_error=True,
                error_message=f"No result in tool response for '{tool_name}'",
                raw_output=stdout_content,
            )

        # Successful tool call
        result_data = tool_response["result"]

        # Handle different result formats
        if isinstance(result_data, dict) and "content" in result_data:
            # MCP standard format
            content = result_data["content"]
            is_error = result_data.get("isError", False)

            # Extract structured content if available
            structured_content = self._extract_structured_content(content)

            # Create enhanced result with both raw and structured content
            enhanced_result = {
                "content": content,
                "structuredContent": structured_content,
                "isError": is_error,
            }

            return ToolCallResult(
                success=not is_error,
                result=enhanced_result,
                content=content,
                is_error=is_error,
                raw_output=stdout_content,
            )
        else:
            # Simple result format
            content = [{"type": "text", "text": str(result_data)}]
            return ToolCallResult(
                success=True,
                result={
                    "content": content,
                    "structuredContent": result_data,
                    "isError": False,
                },
                content=content,
                is_error=False,
                raw_output=stdout_content,
            )

    def _extract_structured_content(self, content: list) -> Dict[str, Any]:
        """
        Extract structured content from MCP content array.

        Args:
            content: MCP content array

        Returns:
            Structured representation of the content
        """
        if not content:
            return {}

        # For single text content, try to parse as JSON
        if len(content) == 1 and content[0].get("type") == "text":
            text = content[0].get("text", "")

            # Try to parse as JSON for structured data
            try:
                parsed = json.loads(text)
                return parsed
            except json.JSONDecodeError:
                # Not JSON, return as simple result
                return {"result": text}

        # For multiple content items or non-text content
        structured = {}
        for i, item in enumerate(content):
            if item.get("type") == "text":
                key = "result" if len(content) == 1 else f"item_{i}"
                structured[key] = item.get("text", "")
            else:
                # Handle other content types (images, etc.)
                structured[f"item_{i}"] = item

        return structured

    def call_tool_stdio_legacy(
        self,
        template_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        template_config: Dict[str, Any],
        config_values: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Legacy method for backward compatibility with CLI.

        Returns the result in the old format for CLI compatibility.
        """
        result = self.call_tool_stdio(
            template_name,
            tool_name,
            arguments,
            template_config,
            config_values,
            env_vars,
            pull_image,
        )

        if result.success:
            return result.result
        else:
            return None

    def validate_template_stdio_support(self, template_config: Dict[str, Any]) -> bool:
        """
        Validate that a template supports stdio transport.

        Args:
            template_config: Template configuration

        Returns:
            True if stdio is supported, False otherwise
        """
        transport = template_config.get("transport", {})
        default_transport = transport.get("default", "http")
        supported_transports = transport.get("supported", ["http"])

        return "stdio" in supported_transports or default_transport == "stdio"

    def _process_tool_response(
        self, tool_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a tool response and return formatted result."""
        if "result" in tool_response:
            result_data = tool_response["result"]
            if isinstance(result_data, dict) and "content" in result_data:
                return result_data
            else:
                # Simple result format
                return {"content": [{"type": "text", "text": str(result_data)}]}
        elif "error" in tool_response:
            error_info = tool_response["error"]
            raise ToolCallError(f"Tool execution error: {error_info}")

        return None
