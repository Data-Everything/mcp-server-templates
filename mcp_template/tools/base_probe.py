"""
Base probe for discovering MCP server tools from different container orchestrators.

This module provides a common interface and shared functionality for probing
MCP servers across Docker, Kubernetes, and other container platforms.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

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
