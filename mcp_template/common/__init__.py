"""
Common shared functionality for MCP Template system.

This package contains shared modules that centralize common functionality
between CLI and MCPClient interfaces, following the refactor plan to eliminate
code duplication and provide a clean separation of concerns.

Modules:
- template_manager: Template discovery, validation, and metadata operations
- deployment_manager: Deployment lifecycle management across backends
- config_manager: Configuration processing, validation, and merging
- tool_manager: Tool discovery, management, and operations
- output_formatter: Output formatting utilities for CLI display
"""

from .config_manager import ConfigManager
from .deployment_manager import DeploymentManager
from .output_formatter import OutputFormatter
from .template_manager import TemplateManager
from .tool_manager import ToolManager

__all__ = [
    "TemplateManager",
    "DeploymentManager", 
    "ConfigManager",
    "ToolManager",
    "OutputFormatter",
]
