#!/usr/bin/env python3
"""
FastMCP File Server - Clean Implementation

A comprehensive file server using FastMCP framework that provides secure
filesystem access for AI assistants through the Model Context Protocol.

This is a standalone implementation that doesn't rely on external base classes
for better reliability and maintainability.
"""

import fnmatch
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import aiofiles
    import aiofiles.os
    from fastmcp import FastMCP
except ImportError as e:
    print("Required dependencies not found. Install with:")
    print("pip install fastmcp>=2.10.0 aiofiles>=23.1.0")
    print(f"Error: {e}")
    sys.exit(1)


class FileServerConfig:
    """Configuration management for the file server."""

    def __init__(self):
        # Parse allowed directories from environment variable
        allowed_dirs_env = os.getenv("MCP_ALLOWED_DIRS", "/data:/workspace")
        self.allowed_directories = [
            d.strip() for d in allowed_dirs_env.split(":") if d.strip()
        ]

        # Other configuration options
        self.read_only = os.getenv("MCP_READ_ONLY", "false").lower() == "true"
        self.max_file_size = int(
            os.getenv("MCP_MAX_FILE_SIZE", str(10 * 1024 * 1024))
        )  # 10MB default

        # Setup logging
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("file-server")

    def validate_path(self, path: str) -> Path:
        """Validate that a path is within allowed directories."""
        resolved_path = Path(path).resolve()

        for allowed_dir in self.allowed_directories:
            allowed_path = Path(allowed_dir).resolve()
            try:
                resolved_path.relative_to(allowed_path)
                return resolved_path
            except ValueError:
                continue

        raise ValueError(
            f"Path '{path}' is not within allowed directories: {self.allowed_directories}"
        )


class FileServer:
    """FastMCP-based file server implementation."""

    def __init__(self):
        self.config = FileServerConfig()
        self.mcp = FastMCP(name="file-server")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all file server tools."""

        @self.mcp.tool()
        async def read_file(path: str) -> str:
            """
            Read the contents of a file.

            Args:
                path: Path to the file to read

            Returns:
                File contents as a string
            """
            validated_path = self.config.validate_path(path)

            if not validated_path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            if not validated_path.is_file():
                raise ValueError(f"Path is not a file: {path}")

            # Check file size
            if validated_path.stat().st_size > self.config.max_file_size:
                raise ValueError(
                    f"File too large: {validated_path.stat().st_size} > {self.config.max_file_size}"
                )

            async with aiofiles.open(validated_path, "r", encoding="utf-8") as f:
                return await f.read()

        @self.mcp.tool()
        async def write_file(path: str, content: str) -> str:
            """
            Write content to a file, creating directories if needed.

            Args:
                path: Path to the file to write
                content: Content to write to the file

            Returns:
                Success message with details
            """
            if self.config.read_only:
                raise ValueError("Server is in read-only mode")

            # Check content size
            if len(content.encode("utf-8")) > self.config.max_file_size:
                raise ValueError(
                    f"Content too large: {len(content)} > {self.config.max_file_size}"
                )

            validated_path = self.config.validate_path(path)

            # Create parent directories if they don't exist
            validated_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(validated_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return f"Successfully wrote {len(content)} characters to {path}"

        @self.mcp.tool()
        async def read_multiple_files(paths: List[str]) -> List[Dict[str, Any]]:
            """
            Read multiple files at once for efficiency.

            Args:
                paths: List of file paths to read

            Returns:
                List of results with path, content, and any errors
            """
            results = []

            for path in paths:
                try:
                    validated_path = self.config.validate_path(path)

                    if not validated_path.exists():
                        raise FileNotFoundError(f"File not found: {path}")

                    if not validated_path.is_file():
                        raise ValueError(f"Path is not a file: {path}")

                    if validated_path.stat().st_size > self.config.max_file_size:
                        raise ValueError(
                            f"File too large: {validated_path.stat().st_size}"
                        )

                    async with aiofiles.open(
                        validated_path, "r", encoding="utf-8"
                    ) as f:
                        content = await f.read()

                    results.append(
                        {
                            "path": path,
                            "content": content,
                            "success": True,
                            "error": None,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "path": path,
                            "content": None,
                            "success": False,
                            "error": str(e),
                        }
                    )

            return results

        @self.mcp.tool()
        async def create_directory(path: str) -> str:
            """
            Create a directory and any necessary parent directories.

            Args:
                path: Path to the directory to create

            Returns:
                Success message
            """
            if self.config.read_only:
                raise ValueError("Server is in read-only mode")

            validated_path = self.config.validate_path(path)
            validated_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created directory: {path}"

        @self.mcp.tool()
        async def list_directory(path: str) -> List[Dict[str, Any]]:
            """
            List the contents of a directory with detailed information.

            Args:
                path: Path to the directory to list

            Returns:
                List of directory entries with metadata
            """
            validated_path = self.config.validate_path(path)

            if not validated_path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")

            if not validated_path.is_dir():
                raise ValueError(f"Path is not a directory: {path}")

            entries = []
            for item in validated_path.iterdir():
                stat = item.stat()
                entries.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": stat.st_mtime,
                        "created": stat.st_ctime,
                        "permissions": oct(stat.st_mode)[-3:],
                    }
                )

            return sorted(entries, key=lambda x: x["name"].lower())

        @self.mcp.tool()
        async def move_file(source: str, destination: str) -> str:
            """
            Move or rename a file or directory.

            Args:
                source: Source path to move from
                destination: Destination path to move to

            Returns:
                Success message
            """
            if self.config.read_only:
                raise ValueError("Server is in read-only mode")

            source_path = self.config.validate_path(source)
            dest_path = self.config.validate_path(destination)

            if not source_path.exists():
                raise FileNotFoundError(f"Source path does not exist: {source}")

            # Create destination parent directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Use aiofiles.os for async file operations
            await aiofiles.os.rename(source_path, dest_path)
            return f"Successfully moved {source} to {destination}"

        @self.mcp.tool()
        async def search_files(
            directory: str, pattern: str = "*", include_content: bool = False
        ) -> List[Dict[str, Any]]:
            """
            Search for files matching a pattern in a directory tree.

            Args:
                directory: Directory to search in (searches recursively)
                pattern: File name pattern to match (supports wildcards like *.txt)
                include_content: Whether to include file content in results

            Returns:
                List of matching files with metadata and optionally content
            """
            validated_dir = self.config.validate_path(directory)

            if not validated_dir.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")

            if not validated_dir.is_dir():
                raise ValueError(f"Path is not a directory: {directory}")

            results = []

            # Search recursively through the directory tree
            for file_path in validated_dir.rglob("*"):
                if file_path.is_file() and fnmatch.fnmatch(file_path.name, pattern):
                    stat = file_path.stat()
                    result = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "directory": str(file_path.parent),
                    }

                    if include_content and stat.st_size <= self.config.max_file_size:
                        try:
                            async with aiofiles.open(
                                file_path, "r", encoding="utf-8"
                            ) as f:
                                result["content"] = await f.read()
                        except Exception as e:
                            result["content_error"] = str(e)

                    results.append(result)

            return sorted(results, key=lambda x: x["path"])

        @self.mcp.tool()
        async def get_file_info(path: str) -> Dict[str, Any]:
            """
            Get detailed information about a file or directory.

            Args:
                path: Path to the file or directory

            Returns:
                Detailed information including size, timestamps, permissions, etc.
            """
            validated_path = self.config.validate_path(path)

            if not validated_path.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")

            stat = validated_path.stat()

            info = {
                "path": str(validated_path),
                "name": validated_path.name,
                "type": "directory" if validated_path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:],
                "owner_readable": os.access(validated_path, os.R_OK),
                "owner_writable": os.access(validated_path, os.W_OK),
                "owner_executable": os.access(validated_path, os.X_OK),
            }

            if validated_path.is_file():
                # Add file-specific information
                info["extension"] = validated_path.suffix
                info["stem"] = validated_path.stem

                # Try to determine if it's a text file
                try:
                    with open(validated_path, "r", encoding="utf-8") as f:
                        f.read(100)  # Try to read first 100 chars
                    info["is_text"] = True
                except (UnicodeDecodeError, PermissionError):
                    info["is_text"] = False

            return info

        @self.mcp.tool()
        async def list_allowed_directories() -> List[Dict[str, Any]]:
            """
            List all directories that the file server has access to.

            Returns:
                List of allowed directories with their status and permissions
            """
            directories = []

            for allowed_dir in self.config.allowed_directories:
                dir_path = Path(allowed_dir)
                if dir_path.exists():
                    stat = dir_path.stat()
                    directories.append(
                        {
                            "path": str(dir_path),
                            "exists": True,
                            "readable": os.access(dir_path, os.R_OK),
                            "writable": os.access(dir_path, os.W_OK)
                            and not self.config.read_only,
                            "modified": stat.st_mtime,
                        }
                    )
                else:
                    directories.append(
                        {
                            "path": str(dir_path),
                            "exists": False,
                            "readable": False,
                            "writable": False,
                            "modified": None,
                        }
                    )

            return directories

    def run(self) -> None:
        """Run the MCP server."""
        self.config.logger.info("Starting FastMCP File Server")
        self.config.logger.info(
            f"Allowed directories: {self.config.allowed_directories}"
        )
        self.config.logger.info(f"Read-only mode: {self.config.read_only}")

        try:
            self.mcp.run()
        except KeyboardInterrupt:
            self.config.logger.info("Server shutdown requested")
        except Exception as e:
            self.config.logger.error(f"Server error: {e}")
            raise


def main():
    """Main entry point for the file server."""
    server = FileServer()
    server.run()


if __name__ == "__main__":
    main()
