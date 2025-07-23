"""
File system client for secure file operations

This module provides the core file system operations with security checks,
path validation, and audit logging.
"""

import os
import glob
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FileSystemClient:
    """Secure file system client with permission controls"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.root_path = Path(config['root_path']).resolve()
        self.allowed_extensions = config.get('allowed_extensions', ['.*'])
        self.max_file_size = config.get('max_file_size', 10 * 1024 * 1024)
        self.read_only = config.get('read_only', False)
        self.enable_subdirectories = config.get('enable_subdirectories', True)
        self.log_operations = config.get('log_file_operations', True)
        self.audit_log_path = config.get('audit_log_path', '/logs/file_operations.log')
        
        # Ensure root path exists
        self.root_path.mkdir(parents=True, exist_ok=True)
        
        # Setup audit logging
        if self.log_operations:
            self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup audit logging for file operations"""
        try:
            audit_path = Path(self.audit_log_path)
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup separate logger for audit
            self.audit_logger = logging.getLogger('file_audit')
            if not self.audit_logger.handlers:
                handler = logging.FileHandler(audit_path)
                formatter = logging.Formatter('%(asctime)s - %(message)s')
                handler.setFormatter(formatter)
                self.audit_logger.addHandler(handler)
                self.audit_logger.setLevel(logging.INFO)
        except Exception as e:
            logger.warning(f"Could not setup audit logging: {e}")
            self.log_operations = False
    
    def _log_operation(self, operation: str, path: str, success: bool, details: str = ""):
        """Log file operation for audit purposes"""
        if not self.log_operations:
            return
            
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'path': path,
                'success': success,
                'details': details
            }
            self.audit_logger.info(json.dumps(log_entry))
        except Exception as e:
            logger.warning(f"Could not log operation: {e}")
    
    def _validate_path(self, file_path: str) -> Path:
        """Validate and resolve file path with security checks"""
        try:
            # Convert to Path object and resolve
            path = Path(file_path)
            if not path.is_absolute():
                path = self.root_path / path
            
            resolved_path = path.resolve()
            
            # Security check: ensure path is within root directory
            if not str(resolved_path).startswith(str(self.root_path)):
                raise ValueError(f"Path outside allowed directory: {file_path}")
            
            # Check subdirectory permissions
            if not self.enable_subdirectories:
                if resolved_path.parent != self.root_path:
                    raise ValueError(f"Subdirectories not allowed: {file_path}")
            
            return resolved_path
            
        except Exception as e:
            logger.error(f"Path validation failed for {file_path}: {e}")
            raise ValueError(f"Invalid path: {file_path}")
    
    def _check_file_extension(self, file_path: Path) -> bool:
        """Check if file extension is allowed"""
        if not self.allowed_extensions or '.*' in self.allowed_extensions:
            return True
        
        file_ext = file_path.suffix.lower()
        return file_ext in self.allowed_extensions
    
    def _check_file_size(self, file_path: Path) -> bool:
        """Check if file size is within limits"""
        try:
            if file_path.exists():
                return file_path.stat().st_size <= self.max_file_size
            return True  # For new files, we'll check content size during write
        except Exception:
            return False
    
    async def read_file(self, file_path: str) -> str:
        """Read file content with security checks"""
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                self._log_operation('read', file_path, False, 'File not found')
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path.is_file():
                self._log_operation('read', file_path, False, 'Not a file')
                raise ValueError(f"Path is not a file: {file_path}")
            
            if not self._check_file_extension(path):
                self._log_operation('read', file_path, False, 'Extension not allowed')
                raise ValueError(f"File extension not allowed: {path.suffix}")
            
            if not self._check_file_size(path):
                self._log_operation('read', file_path, False, 'File too large')
                raise ValueError(f"File too large: {file_path}")
            
            # Read file content
            content = path.read_text(encoding='utf-8')
            
            self._log_operation('read', file_path, True, f'Read {len(content)} characters')
            logger.info(f"Successfully read file: {file_path}")
            
            return content
            
        except Exception as e:
            self._log_operation('read', file_path, False, str(e))
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write file content with security checks"""
        if self.read_only:
            self._log_operation('write', file_path, False, 'Read-only mode')
            raise ValueError("Write operations not allowed in read-only mode")
        
        try:
            path = self._validate_path(file_path)
            
            if not self._check_file_extension(path):
                self._log_operation('write', file_path, False, 'Extension not allowed')
                raise ValueError(f"File extension not allowed: {path.suffix}")
            
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > self.max_file_size:
                self._log_operation('write', file_path, False, 'Content too large')
                raise ValueError(f"Content too large: {content_size} bytes")
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            path.write_text(content, encoding='utf-8')
            
            self._log_operation('write', file_path, True, f'Wrote {content_size} bytes')
            logger.info(f"Successfully wrote file: {file_path}")
            
            return True
            
        except Exception as e:
            self._log_operation('write', file_path, False, str(e))
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    async def list_directory(self, dir_path: str = ".") -> List[str]:
        """List directory contents with security checks"""
        try:
            path = self._validate_path(dir_path)
            
            if not path.exists():
                self._log_operation('list', dir_path, False, 'Directory not found')
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            
            if not path.is_dir():
                self._log_operation('list', dir_path, False, 'Not a directory')
                raise ValueError(f"Path is not a directory: {dir_path}")
            
            # List directory contents
            items = []
            for item in sorted(path.iterdir()):
                try:
                    relative_path = item.relative_to(self.root_path)
                    item_type = "DIR" if item.is_dir() else "FILE"
                    size = item.stat().st_size if item.is_file() else "-"
                    items.append(f"{item_type:4} {size:>10} {relative_path}")
                except Exception as e:
                    logger.warning(f"Error listing item {item}: {e}")
            
            self._log_operation('list', dir_path, True, f'Listed {len(items)} items')
            logger.info(f"Successfully listed directory: {dir_path}")
            
            return items
            
        except Exception as e:
            self._log_operation('list', dir_path, False, str(e))
            logger.error(f"Error listing directory {dir_path}: {e}")
            raise
    
    async def search_files(self, pattern: str, search_path: str = ".") -> List[str]:
        """Search for files matching pattern"""
        try:
            base_path = self._validate_path(search_path)
            
            if not base_path.exists():
                self._log_operation('search', search_path, False, 'Search path not found')
                raise FileNotFoundError(f"Search path not found: {search_path}")
            
            matches = []
            
            # Perform glob search
            if self.enable_subdirectories:
                search_pattern = str(base_path / "**" / f"*{pattern}*")
                found_files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = str(base_path / f"*{pattern}*")
                found_files = glob.glob(search_pattern)
            
            # Filter and format results
            for file_path in found_files:
                try:
                    path = Path(file_path)
                    if path.is_file() and self._check_file_extension(path):
                        relative_path = path.relative_to(self.root_path)
                        matches.append(str(relative_path))
                except Exception as e:
                    logger.warning(f"Error processing search result {file_path}: {e}")
            
            self._log_operation('search', f"{search_path}:{pattern}", True, f'Found {len(matches)} matches')
            logger.info(f"Search for '{pattern}' found {len(matches)} files")
            
            return sorted(matches)
            
        except Exception as e:
            self._log_operation('search', f"{search_path}:{pattern}", False, str(e))
            logger.error(f"Error searching for '{pattern}' in {search_path}: {e}")
            raise
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat = path.stat()
            
            info = {
                'path': str(path.relative_to(self.root_path)),
                'type': 'directory' if path.is_dir() else 'file',
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:],
                'extension': path.suffix if path.is_file() else None
            }
            
            self._log_operation('info', file_path, True, 'Retrieved file info')
            return info
            
        except Exception as e:
            self._log_operation('info', file_path, False, str(e))
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise
