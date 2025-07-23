"""
File operation tools for the MCP server

This module defines the MCP tools (functions) that AI assistants can call
to perform file system operations.
"""

import json
import logging
from typing import Any, Dict, List
from pathlib import Path

from mcp.types import Tool, TextContent, Resource

logger = logging.getLogger(__name__)

class FileTools:
    """MCP tools for file system operations"""
    
    def __init__(self, fs_client, config: Dict[str, Any]):
        self.fs_client = fs_client
        self.config = config
        
    def get_available_tools(self) -> List[Tool]:
        """Return list of available file tools based on configuration"""
        tools = [
            Tool(
                name="read_file",
                description="Read the content of a file. Returns the full text content of the specified file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read (relative to root directory)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="list_directory",
                description="List the contents of a directory. Shows files and subdirectories with their types and sizes.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory to list (relative to root directory)",
                            "default": "."
                        }
                    }
                }
            ),
            Tool(
                name="search_files",
                description="Search for files by name pattern. Finds files containing the specified pattern in their filename.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern or partial filename to look for"
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory to search in (relative to root directory)",
                            "default": "."
                        }
                    },
                    "required": ["pattern"]
                }
            ),
            Tool(
                name="get_file_info",
                description="Get detailed information about a file or directory including size, modification time, and permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file or directory to inspect"
                        }
                    },
                    "required": ["path"]
                }
            )
        ]
        
        # Add write operations only if not in read-only mode
        if not self.config.get('read_only', False):
            tools.append(
                Tool(
                    name="write_file",
                    description="Write content to a file. Creates or overwrites the specified file with the given content.",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to write (relative to root directory)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                )
            )
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a file tool and return results"""
        try:
            logger.info(f"Executing tool: {name}")
            
            if name == "read_file":
                return await self._read_file(arguments["path"])
            elif name == "write_file":
                return await self._write_file(arguments["path"], arguments["content"])
            elif name == "list_directory":
                path = arguments.get("path", ".")
                return await self._list_directory(path)
            elif name == "search_files":
                pattern = arguments["pattern"]
                path = arguments.get("path", ".")
                return await self._search_files(pattern, path)
            elif name == "get_file_info":
                return await self._get_file_info(arguments["path"])
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]
                
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]
    
    async def _read_file(self, path: str) -> List[TextContent]:
        """Read file content"""
        content = await self.fs_client.read_file(path)
        
        # Format response with file info
        response = f"""📄 **File: {path}**

```
{content}
```

*File size: {len(content)} characters*"""
        
        return [TextContent(type="text", text=response)]
    
    async def _write_file(self, path: str, content: str) -> List[TextContent]:
        """Write file content"""
        success = await self.fs_client.write_file(path, content)
        
        if success:
            response = f"""✅ **File written successfully**

📄 **Path:** {path}
📊 **Size:** {len(content)} characters
⏰ **Status:** File created/updated"""
        else:
            response = f"❌ **Failed to write file:** {path}"
        
        return [TextContent(type="text", text=response)]
    
    async def _list_directory(self, path: str) -> List[TextContent]:
        """List directory contents"""
        files = await self.fs_client.list_directory(path)
        
        if not files:
            response = f"""📁 **Directory: {path}**

*Directory is empty*"""
        else:
            file_list = "\n".join(files)
            response = f"""📁 **Directory: {path}**

```
{'Type':<4} {'Size':<10} {'Name'}
{'-'*4} {'-'*10} {'-'*20}
{file_list}
```

*Found {len(files)} items*"""
        
        return [TextContent(type="text", text=response)]
    
    async def _search_files(self, pattern: str, path: str) -> List[TextContent]:
        """Search for files"""
        matches = await self.fs_client.search_files(pattern, path)
        
        if not matches:
            response = f"""🔍 **Search Results**

📂 **Search path:** {path}
🔍 **Pattern:** {pattern}
📊 **Results:** No files found"""
        else:
            file_list = "\n".join(f"📄 {match}" for match in matches)
            response = f"""🔍 **Search Results**

📂 **Search path:** {path}
🔍 **Pattern:** {pattern}
📊 **Results:** {len(matches)} files found

{file_list}"""
        
        return [TextContent(type="text", text=response)]
    
    async def _get_file_info(self, path: str) -> List[TextContent]:
        """Get detailed file information"""
        info = await self.fs_client.get_file_info(path)
        
        # Format file size
        size = info['size']
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        response = f"""📊 **File Information**

📄 **Path:** {info['path']}
📁 **Type:** {info['type'].title()}
📊 **Size:** {size_str}
⏰ **Modified:** {info['modified']}
🔒 **Permissions:** {info['permissions']}"""

        if info['extension']:
            response += f"\n🏷️ **Extension:** {info['extension']}"
        
        return [TextContent(type="text", text=response)]
    
    async def list_resources(self) -> List[Resource]:
        """List available file system resources for MCP resource protocol"""
        try:
            # List files in root directory as resources
            files = await self.fs_client.list_directory(".")
            resources = []
            
            for file_line in files:
                # Parse the file listing format: "TYPE      SIZE NAME"
                parts = file_line.split()
                if len(parts) >= 3 and parts[0] == "FILE":
                    filename = " ".join(parts[2:])  # Handle filenames with spaces
                    resources.append(
                        Resource(
                            uri=f"file://{filename}",
                            name=filename,
                            description=f"File: {filename}",
                            mimeType="text/plain"
                        )
                    )
            
            return resources
            
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """Read a file resource by URI"""
        try:
            # Extract filename from URI (format: file://filename)
            if uri.startswith("file://"):
                filename = uri[7:]  # Remove "file://" prefix
                content = await self.fs_client.read_file(filename)
                return content
            else:
                raise ValueError(f"Invalid resource URI: {uri}")
                
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise
