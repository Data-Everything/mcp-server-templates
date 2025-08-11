"""
Common module initialization for mcp_template shared functionality.

This module contains shared functionality that is used by both the CLI and MCPClient,
centralizing common operations to reduce code duplication and improve maintainability.

Modules:
- template_manager: Template discovery, loading, and validation
- deployment_manager: Deployment orchestration and management
- config_manager: Configuration processing and merging
- tool_manager: Tool discovery and management
- backend_manager: Backend abstraction layer
"""

from .config_manager import ConfigManager
from .deployment_manager import DeploymentManager
from .template_manager import TemplateManager
from .tool_manager import ToolManager

__version__ = "0.1.0"
__all__ = [
    "TemplateManager",
    "DeploymentManager",
    "ConfigManager",
    "ToolManager",
]
