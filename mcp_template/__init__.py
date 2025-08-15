"""
MCP Template Deployment Tool

A unified deployment system that provides:
- Rich CLI interface for standalone users
- Backend abstraction for different deployment targets
- Dynamic template discovery and configuration management
- Zero-configuration deployment experience

The system follows a layered architecture:
1. CLI Layer: Rich interface for user interaction
2. Management Layer: DeploymentManager orchestrates operations
3. Backend Layer: Pluggable deployment services (Docker, Kubernetes, etc.)
4. Discovery Layer: Dynamic template detection and configuration

Key Features:
- Template-driven configuration (no hardcoded template logic)
- Configurable image pulling (supports local development)
- Generic deployment utilities (reusable across templates)
- Comprehensive error handling and logging
"""

import logging

from mcp_template.backends.docker import DockerDeploymentService
from mcp_template.cli import EnhancedCLI
from mcp_template.client import MCPClient
from mcp_template.core import ConfigManager
from mcp_template.core import DeploymentManager as CommonDeploymentManager
from mcp_template.core import OutputFormatter, TemplateManager, ToolManager
from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.deployer import MCPDeployer
from mcp_template.template.utils.creation import TemplateCreator
from mcp_template.template.utils.discovery import TemplateDiscovery
from mcp_template.typer_cli import app

# Export the classes for external use (CI compatibility)
__all__ = [
    "TemplateDiscovery",
    "DockerDeploymentService",
    "DeploymentManager",
    "MCPDeployer",
    "TemplateCreator",
    "MCPClient",
    "TemplateManager",
    "CommonDeploymentManager",
    "ConfigManager",
    "ToolManager",
    "OutputFormatter",
]

# Constants
DEFAULT_CONFIG_PATH = "/config"
CUSTOM_NAME_HELP = "Custom container name"

# Console and logger initialization moved to functions to avoid import issues
console = None
logger = logging.getLogger(__name__)
enhanced_cli = None


def get_console():
    """Get Rich console instance."""
    global console
    if console is None:
        from rich.console import Console

        console = Console()
    return console


def get_enhanced_cli():
    """Get enhanced CLI instance."""
    global enhanced_cli
    if enhanced_cli is None:
        enhanced_cli = EnhancedCLI()
    return enhanced_cli


def split_command_args(args):
    """
    Split command line arguments into a list, handling quoted strings.
    This is useful for parsing command line arguments that may contain spaces.
    """

    out_vars = {}
    for var in args:
        key, value = var.split("=", 1)
        out_vars[key] = value

    return out_vars


def main():
    """
    Main entry point for the MCP deployer CLI.
    Uses Typer-based CLI with autocomplete and enhanced features.
    """

    app()


if __name__ == "__main__":
    main()
