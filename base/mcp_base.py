"""
MCP Platform Base Server Class

This module provides a standardized base class for all MCP server implementations 
in the MCP Platform ecosystem. It follows patterns from the official MCP servers
and provides common functionality for platform integration.

Based on patterns from: https://github.com/modelcontextprotocol/servers
"""

import asyncio
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass
from pathlib import Path

# Import MCP SDK components
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListResourcesRequest,
        ListResourcesResult,
        ListToolsRequest,
        ListToolsResult,
        ReadResourceRequest,
        ReadResourceResult,
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Provide fallback types for development
    class Server: pass
    class Tool: pass
    class Resource: pass


@dataclass
class MCPServerConfig:
    """Configuration class for MCP servers following platform standards"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    
    # Security settings
    enable_security_validation: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30  # seconds
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_audit_logging: bool = True
    
    # Platform integration
    platform_api_endpoint: Optional[str] = None
    platform_api_key: Optional[str] = None
    enable_metrics: bool = True
    enable_health_checks: bool = True


class BaseMCPServer(ABC):
    """
    Base class for MCP Platform servers following official MCP patterns.
    
    This class provides:
    - Standardized configuration management
    - Security utilities and validation
    - Logging and audit trails
    - Health monitoring
    - Platform integration hooks
    - Error handling patterns
    
    Subclasses should implement the abstract methods to define their specific
    tools, resources, and business logic.
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.server = None
        self._setup_logging()
        self._validate_mcp_availability()
        
        # Performance tracking
        self._request_count = 0
        self._error_count = 0
        self._start_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        
        # Security context
        self._security_context = {}
        
    def _validate_mcp_availability(self):
        """Ensure MCP SDK is available"""
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP SDK not available. Install with: pip install mcp"
            )
    
    def _setup_logging(self):
        """Configure logging following platform standards"""
        self.logger = logging.getLogger(f"mcp.{self.config.name}")
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
            )
            self.logger.addHandler(file_handler)
        
        # Audit logger for security events
        if self.config.enable_audit_logging:
            self.audit_logger = logging.getLogger(f"audit.{self.config.name}")
            self.audit_logger.setLevel(logging.INFO)
            
            audit_handler = logging.StreamHandler(sys.stdout)
            audit_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - AUDIT - %(name)s - %(message)s'
                )
            )
            self.audit_logger.addHandler(audit_handler)
    
    def create_server(self) -> Server:
        """Create and configure the MCP server instance"""
        if self.server is None:
            self.server = Server(self.config.name)
            self._register_handlers()
        return self.server
    
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            try:
                tools = await self.list_tools()
                self.logger.debug(f"Listed {len(tools)} tools")
                return tools
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}")
                self._error_count += 1
                raise
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Handle tool calls with security and audit logging"""
            self._request_count += 1
            
            try:
                # Security validation
                if self.config.enable_security_validation:
                    await self._validate_tool_request(name, arguments)
                
                # Audit logging
                if self.config.enable_audit_logging:
                    self.audit_logger.info(
                        f"Tool call: {name} with args: {json.dumps(arguments, default=str)}"
                    )
                
                # Execute tool
                result = await self.call_tool(name, arguments)
                
                # Ensure result is properly formatted
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                elif isinstance(result, list):
                    return result
                else:
                    return [TextContent(type="text", text=str(result))]
                    
            except Exception as e:
                self._error_count += 1
                self.logger.error(f"Error calling tool {name}: {e}")
                
                if self.config.enable_audit_logging:
                    self.audit_logger.error(
                        f"Tool call failed: {name} - {str(e)}"
                    )
                
                raise
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources"""
            try:
                resources = await self.list_resources()
                self.logger.debug(f"Listed {len(resources)} resources")
                return resources
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}")
                self._error_count += 1
                raise
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource reading"""
            try:
                # Security validation
                if self.config.enable_security_validation:
                    await self._validate_resource_request(uri)
                
                # Audit logging
                if self.config.enable_audit_logging:
                    self.audit_logger.info(f"Resource read: {uri}")
                
                result = await self.read_resource(uri)
                return result
                
            except Exception as e:
                self._error_count += 1
                self.logger.error(f"Error reading resource {uri}: {e}")
                
                if self.config.enable_audit_logging:
                    self.audit_logger.error(f"Resource read failed: {uri} - {str(e)}")
                
                raise
    
    async def _validate_tool_request(self, name: str, arguments: dict):
        """Validate tool requests for security"""
        # Size validation
        args_size = len(json.dumps(arguments, default=str).encode('utf-8'))
        if args_size > self.config.max_request_size:
            raise ValueError(f"Request too large: {args_size} bytes")
        
        # Tool-specific validation (override in subclasses)
        await self.validate_tool_request(name, arguments)
    
    async def _validate_resource_request(self, uri: str):
        """Validate resource requests for security"""
        # Basic URI validation
        if not uri or len(uri) > 1000:
            raise ValueError("Invalid resource URI")
        
        # Resource-specific validation (override in subclasses)
        await self.validate_resource_request(uri)
    
    # Abstract methods that subclasses must implement
    
    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """Return list of available tools"""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool call"""
        pass
    
    # Optional methods that subclasses can override
    
    async def list_resources(self) -> List[Resource]:
        """Return list of available resources (optional)"""
        return []
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource (optional)"""
        raise NotImplementedError("Resource reading not implemented")
    
    async def validate_tool_request(self, name: str, arguments: dict):
        """Custom tool request validation (optional)"""
        pass
    
    async def validate_resource_request(self, uri: str):
        """Custom resource request validation (optional)"""
        pass
    
    # Utility methods
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get server health status"""
        current_time = asyncio.get_event_loop().time()
        uptime = current_time - self._start_time if self._start_time > 0 else 0
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "version": self.config.version,
            "timestamp": current_time
        }
    
    def log_security_event(self, event: str, details: Dict[str, Any]):
        """Log security-related events"""
        if self.config.enable_audit_logging:
            self.audit_logger.warning(
                f"Security event: {event} - {json.dumps(details, default=str)}"
            )
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info(f"Shutting down {self.config.name}")
        # Cleanup resources, close connections, etc.
        # Subclasses can override for custom cleanup
    
    # Platform integration helpers
    
    def get_platform_config(self, key: str, default: Any = None) -> Any:
        """Get configuration from platform environment"""
        env_key = f"MCP_PLATFORM_{key.upper()}"
        return os.getenv(env_key, default)
    
    def is_platform_enabled(self) -> bool:
        """Check if platform integration is enabled"""
        return (
            self.config.platform_api_endpoint is not None
            and self.config.platform_api_key is not None
        )


# Utility functions for common MCP patterns

def create_text_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any]
) -> Tool:
    """Helper function to create a text-based tool"""
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys())
        }
    )


def create_file_resource(
    uri: str,
    name: str,
    description: str,
    mime_type: str = "text/plain"
) -> Resource:
    """Helper function to create a file resource"""
    return Resource(
        uri=uri,
        name=name,
        description=description,
        mimeType=mime_type
    )


def validate_file_path(path: str, allowed_roots: List[str]) -> bool:
    """Validate file path against allowed roots"""
    try:
        resolved_path = Path(path).resolve()
        for root in allowed_roots:
            root_path = Path(root).resolve()
            try:
                resolved_path.relative_to(root_path)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for security"""
    # Remove path separators and dangerous characters
    unsafe_chars = ['/', '', '..', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized.strip()


# Example implementation for reference
class ExampleMCPServer(BaseMCPServer):
    """
    Example implementation showing how to use BaseMCPServer.
    This demonstrates the patterns that all MCP Platform servers should follow.
    """
    
    def __init__(self):
        config = MCPServerConfig(
            name="example-server",
            description="Example MCP server implementation",
            version="1.0.0"
        )
        super().__init__(config)
    
    async def list_tools(self) -> List[Tool]:
        """List available tools"""
        return [
            create_text_tool(
                name="echo",
                description="Echo back the provided text",
                parameters={
                    "text": {
                        "type": "string",
                        "description": "Text to echo back"
                    }
                }
            ),
            create_text_tool(
                name="status",
                description="Get server status information",
                parameters={}
            )
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute tool calls"""
        if name == "echo":
            text = arguments.get("text", "")
            return f"Echo: {text}"
        
        elif name == "status":
            health = self.get_health_status()
            return f"Server Status: {json.dumps(health, indent=2)}"
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def validate_tool_request(self, name: str, arguments: dict):
        """Custom validation for this server"""
        if name == "echo":
            text = arguments.get("text", "")
            if len(text) > 1000:
                raise ValueError("Text too long for echo")


if __name__ == "__main__":
    # Example of how to run a server
    import asyncio
    
    async def main():
        # Create server instance
        server_impl = ExampleMCPServer()
        server = server_impl.create_server()
        
        # Run the server
        async with server:
            await server.run()
    
    asyncio.run(main())

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.models import InitializeResult
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseMCPServer(ABC):
    """
    Base class for all MCP server implementations
    
    This class provides:
    - Standard MCP protocol handling
    - Configuration management
    - Error handling and logging
    - Security utilities
    - Resource and tool management patterns
    """
    
    def __init__(self, server_name: str, version: str = "1.0.0"):
        self.server_name = server_name
        self.version = version
        self.logger = logging.getLogger(server_name)
        
        # Initialize MCP server
        self.server = Server(server_name)
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Setup handlers
        self._setup_base_handlers()
        self._setup_custom_handlers()
        
        self.logger.info(f"{server_name} v{version} initialized")
    
    @abstractmethod
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load server-specific configuration from environment variables or config files.
        
        Returns:
            Dict containing configuration parameters
        """
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[Tool]:
        """
        Return list of tools this server provides.
        
        Returns:
            List of Tool objects that define the server's capabilities
        """
        pass
    
    @abstractmethod
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle tool execution requests.
        
        Args:
            name: Tool name to execute
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        pass
    
    def get_available_resources(self) -> List[Resource]:
        """
        Return list of resources this server provides.
        Override in subclasses if resources are supported.
        
        Returns:
            List of Resource objects (empty by default)
        """
        return []
    
    async def handle_resource_read(self, uri: str) -> str:
        """
        Handle resource read requests.
        Override in subclasses if resources are supported.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content as string
        """
        raise NotImplementedError("Resource reading not implemented")
    
    def _setup_base_handlers(self):
        """Setup standard MCP protocol handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources"""
            try:
                return self.get_available_resources()
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}")
                return []

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content"""
            try:
                return await self.handle_resource_read(uri)
            except Exception as e:
                self.logger.error(f"Error reading resource {uri}: {e}")
                raise

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            try:
                return self.get_available_tools()
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}")
                return []

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute tool"""
            try:
                self.logger.info(f"Executing tool: {name}")
                return await self.handle_tool_call(name, arguments)
            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]
    
    def _setup_custom_handlers(self):
        """
        Setup custom handlers specific to the server implementation.
        Override in subclasses to add custom protocol handlers.
        """
        pass
    
    # Utility methods for common operations
    
    def validate_path_security(self, file_path: str, allowed_roots: List[str]) -> Path:
        """
        Validate file path for security (similar to filesystem server approach).
        
        Args:
            file_path: Path to validate
            allowed_roots: List of allowed root directories
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If path is not allowed
        """
        try:
            path = Path(file_path)
            if not path.is_absolute():
                # Convert relative to absolute using first allowed root
                if allowed_roots:
                    path = Path(allowed_roots[0]) / path
                else:
                    raise ValueError("No allowed roots configured")
            
            resolved_path = path.resolve()
            
            # Check if path is within allowed directories
            for root in allowed_roots:
                root_path = Path(root).resolve()
                try:
                    resolved_path.relative_to(root_path)
                    return resolved_path  # Path is within this root
                except ValueError:
                    continue
            
            raise ValueError(f"Path outside allowed directories: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Path validation failed for {file_path}: {e}")
            raise ValueError(f"Invalid path: {file_path}")
    
    def format_error_response(self, error: Exception, context: str = "") -> List[TextContent]:
        """
        Format error into standard response format.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            
        Returns:
            Formatted error response
        """
        error_msg = f"❌ Error{f' in {context}' if context else ''}: {str(error)}"
        self.logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    def format_success_response(self, message: str, data: Optional[Any] = None) -> List[TextContent]:
        """
        Format success response with optional data.
        
        Args:
            message: Success message
            data: Optional data to include
            
        Returns:
            Formatted success response
        """
        response = f"✅ {message}"
        if data is not None:
            response += f"\n\n```json\n{json.dumps(data, indent=2)}\n```"
        
        return [TextContent(type="text", text=response)]
    
    def get_env_config(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get configuration value from environment variables with type conversion.
        
        Args:
            key: Environment variable key
            default: Default value if not found
            required: Whether the config is required
            
        Returns:
            Configuration value with appropriate type
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required configuration {key} not found")
        
        # Type conversion based on default value type
        if isinstance(default, bool):
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            return int(value) if value is not None else default
        elif isinstance(default, list) and isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.split(',') if value else default
        
        return value
    
    async def run(self):
        """
        Start the MCP server using stdio transport.
        """
        self.logger.info(f"Starting {self.server_name} v{self.version}...")
        
        # Log configuration (without sensitive data)
        safe_config = {k: v for k, v in self.config.items() 
                      if 'token' not in k.lower() and 'key' not in k.lower() and 'password' not in k.lower()}
        self.logger.info(f"Configuration: {safe_config}")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializeResult(
                    protocol_version="2024-11-05",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                    server_info={
                        "name": self.server_name,
                        "version": self.version,
                    },
                ),
            )

def create_server_main(server_class, *args, **kwargs):
    """
    Generic main function for MCP servers.
    
    Args:
        server_class: Server class that inherits from BaseMCPServer
        *args, **kwargs: Arguments to pass to server constructor
    """
    async def main():
        try:
            server = server_class(*args, **kwargs)
            await server.run()
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
        except Exception as e:
            logging.error(f"Server error: {e}")
            raise

    return asyncio.run(main())
