#!/usr/bin/env python3
"""
File Server MCP - Secure file system access for AI assistants

This MCP server provides secure file system operations including:
- Reading file contents
- Writing files (with permission checks)
- Listing directory contents
- Searching for files
- Path validation and security checks
- Audit logging
"""

import asyncio
import json
import os
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# MCP imports
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

from .client import FileSystemClient
from .tools import FileTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileServerMCP:
    """Main MCP server class for file system operations"""
    
    def __init__(self):
        self.server = Server("file-server-mcp")
        
        # Load configuration from environment
        self.config = self._load_config()
        
        # Initialize components
        self.fs_client = FileSystemClient(self.config)
        self.tools = FileTools(self.fs_client, self.config)
        
        # Setup MCP handlers
        self._setup_handlers()
        
        logger.info(f"File Server MCP initialized")
        logger.info(f"Root path: {self.config['root_path']}")
        logger.info(f"Read-only mode: {self.config['read_only']}")
        logger.info(f"Max file size: {self.config['max_file_size']}MB")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            'root_path': os.getenv('ROOT_PATH', '/data'),
            'allowed_extensions': json.loads(
                os.getenv('ALLOWED_EXTENSIONS', '[".*"]')
            ),
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', '10')) * 1024 * 1024,  # Convert to bytes
            'read_only': os.getenv('READ_ONLY', 'false').lower() == 'true',
            'enable_subdirectories': os.getenv('ENABLE_SUBDIRECTORIES', 'true').lower() == 'true',
            'log_file_operations': os.getenv('LOG_FILE_OPERATIONS', 'true').lower() == 'true',
            'audit_log_path': os.getenv('AUDIT_LOG_PATH', '/logs/file_operations.log'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        # Validate root path exists
        root_path = Path(config['root_path'])
        if not root_path.exists():
            logger.warning(f"Root path {root_path} does not exist, creating it")
            root_path.mkdir(parents=True, exist_ok=True)
        
        return config
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available file system resources"""
            logger.debug("Handling list_resources request")
            return await self.tools.list_resources()

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read file content as a resource"""
            logger.debug(f"Handling read_resource request for: {uri}")
            return await self.tools.read_resource(uri)

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available file operations"""
            logger.debug("Handling list_tools request")
            return self.tools.get_available_tools()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute file operation"""
            logger.info(f"Handling tool call: {name} with arguments: {arguments}")
            return await self.tools.call_tool(name, arguments)

    async def run(self):
        """Start the MCP server"""
        logger.info(f"Starting File Server MCP on stdio...")
        
        # Log startup configuration
        logger.info("=== File Server MCP Configuration ===")
        for key, value in self.config.items():
            if key == 'allowed_extensions' and isinstance(value, list):
                logger.info(f"  {key}: {', '.join(value) if value else 'All extensions allowed'}")
            else:
                logger.info(f"  {key}: {value}")
        logger.info("=====================================")
        
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
                        "name": "file-server-mcp",
                        "version": "1.0.0",
                        "description": "Secure file system access for AI assistants"
                    },
                ),
            )

def main():
    """Entry point for the MCP server"""
    try:
        server = FileServerMCP()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
