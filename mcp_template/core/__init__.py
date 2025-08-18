"""
Core business logic and infrastructure for MCP Template system.

This package contains both shared business logic modules and infrastructure components
that centralize common functionality between CLI and MCPClient interfaces.

Business Logic Modules:
- template_manager: Template discovery, validation, and metadata operations
- deployment_manager: Deployment lifecycle management across backends
- config_manager: Configuration processing, validation, and merging
- tool_manager: Tool discovery, management, and operations
- output_formatter: Output formatting utilities for CLI display

Infrastructure Components:
- mcp_connection: MCP server connection management
- tool_caller: Tool execution infrastructure
"""

# Business Logic Modules (new refactored components)
from .cache import CacheManager
from .deployment_manager import DeploymentManager
from .mcp_connection import MCPConnection

# Infrastructure Components (legacy components, kept for compatibility)
from .multi_backend_manager import MultiBackendManager
from .template_manager import TemplateManager
from .tool_caller import ToolCaller
from .tool_manager import ToolManager

__all__ = [
    # Business Logic
    "CacheManager",
    "TemplateManager",
    "DeploymentManager",
    "ToolManager",
    # Infrastructure
    "MCPConnection",
    "MultiBackendManager",
    "ToolCaller",
]
