#!/usr/bin/env python3
"""
Demo MCP Server - Reference Implementation

A demonstration MCP server that showcases FastMCP best practices
following the official FastMCP documentation patterns.
"""

# Import configuration for testing compatibility
try:
    from .config import DemoServerConfig
except ImportError:
    from config import DemoServerConfig

# Import BaseFastMCP from the correct location
try:
    from ...mcp_template.base import BaseFastMCP
except ImportError:
    try:
        from mcp_template.base import BaseFastMCP
    except ImportError:
        # Fallback for standalone usage
        import sys

        sys.path.append("../..")
        from mcp_template.base import BaseFastMCP


class DemoServer(BaseFastMCP):
    """Demo MCP Server class that extends BaseFastMCP."""

    def __init__(self, config=None):
        # Initialize demo-specific configuration
        self.demo_config = DemoServerConfig(config)

        # Initialize the base FastMCP server
        super().__init__("demo-server", config)

        # Register demo-specific tools
        self.register_demo_tools()

    def register_demo_tools(self):
        """Register demo-specific tools with the FastMCP server."""

        @self.tool
        def say_hello(name: str = "World") -> str:
            """
            Generate a personalized greeting message.

            Args:
                name: Name of the person to greet (optional)

            Returns:
                A personalized greeting message
            """
            if name and name != "World":
                greeting = (
                    f"Hello {name}! Greetings from {self.demo_config.hello_from}!"
                )
            else:
                greeting = f"Hello! Greetings from {self.demo_config.hello_from}!"
            return greeting

        @self.tool
        def get_server_info() -> dict:
            """
            Get information about the demo MCP server.

            Returns:
                Dictionary containing server information
            """
            return {
                "name": "Demo MCP Server",
                "version": "1.0.0",
                "description": "A simple demonstration MCP server that provides greeting tools",
                "hello_from": self.demo_config.hello_from,
                "log_level": self.demo_config.log_level,
                "capabilities": ["Greeting Tools", "Server Information"],
                "transport": "http",
                "port": 7071,
            }

        @self.tool
        def echo_message(message: str) -> str:
            """
            Echo back a message with server identification.

            Args:
                message: Message to echo back

            Returns:
                Echoed message with server identification
            """
            echoed = f"[{self.demo_config.hello_from}] Echo: {message}"
            return echoed


# Create the server instance for standalone usage
if __name__ == "__main__":
    # Create a DemoServer instance for direct usage
    server = DemoServer()

    # Run with HTTP transport on port 7071 as specified in Dockerfile
    server.run(transport="http", host="0.0.0.0", port=7071)
