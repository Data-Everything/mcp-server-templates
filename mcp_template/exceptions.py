"""
Core execptions for MCP Template system.
"""

from typing import Optional


class MCPException(Exception):
    """Base exception for MCP Template system."""

    pass


class MCPServerError(MCPException):
    """Exception raised for errors related to MCP server operations."""

    def __init__(self, message: str):
        super().__init__(message)


class StdIoTransportDeploymentError(MCPException):
    """Exception raised for errors related to standard I/O deployments."""

    def __init__(
        self,
        message: str = "Stdio transport do not support deployments. "
        "Consider calling tools directly.",
    ):
        """
        Args:
            message: Error message to display.
        """

        super().__init__(message)


class TemplateNotFoundError(MCPException):
    """Exception raised when a requested template is not found."""

    def __init__(self, template_id: str):
        """
        Args:
            template_id: ID of the template that was not found.
        """

        super().__init__(f"Template '{template_id}' not found.")
        self.template_id = template_id


class InvalidConfigurationError(MCPException):
    """Exception raised for invalid configuration errors."""

    def __init__(self, message: str):
        """
        Args:
            message: Error message to display.
        """

        super().__init__(message)


class ToolNotFoundError(MCPException):
    """Exception raised when a requested tool is not found."""

    def __init__(self, tool_name: str, template_id: Optional[str] = None):
        """
        Args:
            tool_name: Name of the tool that was not found.
        """

        message = f"Tool '{tool_name}' not found."
        if template_id:
            message = f"{message} in template '{template_id}'."

        super().__init__(message)
        self.tool_name = tool_name


class DeploymentError(MCPException):
    """Exception raised for errors during deployment operations."""

    def __init__(self, message: str):
        """
        Args:
            message: Error message to display.
        """

        super().__init__(message)


class ToolCallError(MCPException):
    """Exception raised for errors during tool calls."""

    def __init__(self, message: str, tool_name: Optional[str] = None):
        """
        Args:
            message: Error message to display.
            tool_name: Name of the tool that failed (optional).
        """
        if tool_name:
            super().__init__(f"Error calling tool '{tool_name}': {message}")
            self.tool_name = tool_name
        else:
            super().__init__(message)
            self.tool_name = None
        self.message = message
