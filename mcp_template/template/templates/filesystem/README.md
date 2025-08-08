# Filesystem MCP Server

Secure local filesystem access with configurable allowed paths for AI assistants using the Model Context Protocol (MCP).

## Overview

The Filesystem MCP Server provides comprehensive file system operations while maintaining security through configurable allowed directories. Built on the proven `mcp-filesystem-server` foundation, it offers 14 powerful tools for file and directory management.

## Features

### Core Capabilities
- **🗂️ Directory Operations**: List, create, and manage directories with tree visualization
- **📁 File Management**: Read, write, copy, move, and delete files with metadata access
- **🔍 Search & Discovery**: Search files by name and content with flexible patterns
- **📊 Batch Operations**: Read multiple files efficiently in a single operation
- **🔐 Security First**: Configurable allowed directories with strict path validation
- **🚀 High Performance**: Optimized for large directory structures and file operations

### Available Tools
- `list_allowed_directories` - View configured allowed directories
- `list_directory` - List files and subdirectories
- `tree` - Display directory structure as a tree
- `read_file` - Read file contents with encoding detection
- `read_multiple_files` - Batch read multiple files efficiently
- `write_file` - Create or overwrite files with content
- `modify_file` - Update specific parts of existing files
- `copy_file` - Copy files between locations
- `move_file` - Move or rename files and directories
- `delete_file` - Remove files and directories
- `create_directory` - Create new directories with parents
- `get_file_info` - Get detailed file metadata and statistics
- `search_files` - Find files by name patterns
- `search_within_files` - Search for content within files

## Configuration

### Required Parameters
- **`allowed_dirs`** (required): Space-separated list of allowed directories for file access
  - Environment: `ALLOWED_DIRS`
  - Example: `"/home/user/documents /tmp/workspace"`
  - Security: Only these directories and their subdirectories are accessible

### Optional Parameters
- **`log_level`**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
  - Environment: `LOG_LEVEL`
  - Default: `INFO`

### Configuration Methods

#### 1. Interactive CLI (Recommended)
```bash
# Start interactive mode
mcpt interactive

# Configure and call tools
mcpt> config filesystem allowed_dirs="/home/user/documents /tmp/workspace"
mcpt> tools filesystem
mcpt> call filesystem list_directory '{"path": "/tmp"}'
```

#### 2. Command Line with Configuration
```bash
# Using --config flag
mcpt run-tool filesystem list_directory \
  --config allowed_dirs="/home/user/documents /tmp" \
  '{"path": "/home/user/documents"}'

# Using environment variables
export ALLOWED_DIRS="/home/user/documents /tmp"
mcpt run-tool filesystem list_directory '{"path": "/tmp"}'

# Using config file
echo '{"allowed_dirs": "/home/user/documents /tmp"}' > config.json
mcpt run-tool filesystem list_directory \
  --config-file config.json \
  '{"path": "/tmp"}'
```

#### 3. Direct Docker Usage
```bash
# Run with volume mounts for allowed directories
docker run -i --rm \
  -v "/home/user/documents:/data/documents:ro" \
  -v "/tmp:/data/tmp:rw" \
  -e ALLOWED_DIRS="/data/documents /data/tmp" \
  dataeverything/mcp-filesystem
```

## Usage Examples

### Basic File Operations
```bash
# List directory contents
mcpt> call filesystem list_directory '{"path": "/tmp"}'

# Read a file
mcpt> call filesystem read_file '{"path": "/tmp/example.txt"}'

# Write content to a file
mcpt> call filesystem write_file '{"path": "/tmp/output.txt", "content": "Hello World!"}'

# Get file information
mcpt> call filesystem get_file_info '{"path": "/tmp/example.txt"}'
```

### Advanced Operations
```bash
# Search for files by pattern
mcpt> call filesystem search_files '{"path": "/tmp", "pattern": "*.txt"}'

# Search within file contents
mcpt> call filesystem search_within_files '{"path": "/tmp", "pattern": "error", "file_pattern": "*.log"}'

# Display directory tree
mcpt> call filesystem tree '{"path": "/tmp", "max_depth": 3}'

# Read multiple files at once
mcpt> call filesystem read_multiple_files '{"paths": ["/tmp/file1.txt", "/tmp/file2.txt"]}'
```

### File Management
```bash
# Copy files
mcpt> call filesystem copy_file '{"source": "/tmp/source.txt", "destination": "/tmp/backup.txt"}'

# Move/rename files
mcpt> call filesystem move_file '{"source": "/tmp/old.txt", "destination": "/tmp/new.txt"}'

# Create directories
mcpt> call filesystem create_directory '{"path": "/tmp/new-folder"}'

# Delete files/directories
mcpt> call filesystem delete_file '{"path": "/tmp/unwanted.txt"}'
```

## Security & Best Practices

### Directory Access Control
- Only directories specified in `allowed_dirs` are accessible
- Path traversal attacks (../) are prevented
- Symbolic links are handled securely
- Read-only vs read-write access can be controlled via Docker volume mounts

### Recommended Patterns
```bash
# Read-only document access
-v "/home/user/documents:/data/docs:ro"

# Read-write workspace access
-v "/tmp/workspace:/data/workspace:rw"

# Multiple mount points with different permissions
-v "/etc/config:/data/config:ro" \
-v "/var/log:/data/logs:ro" \
-v "/tmp/output:/data/output:rw"
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export ALLOWED_DIRS="/tmp /home/user/documents"
export LOG_LEVEL="DEBUG"

# Test tools directly via JSON-RPC
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | \
  python -m mcp_filesystem
```

### Running Tests
```bash
# Run filesystem-specific tests
pytest mcp_template/template/templates/filesystem/tests/ -v

# Run integration tests
pytest tests/test_volume_mount_command_args.py -v
```

### Building Custom Images
```bash
# Build the image
docker build -t my-filesystem-server \
  mcp_template/template/templates/filesystem/

# Run with custom configuration
docker run -i --rm \
  -v "$PWD:/data/workspace:rw" \
  -e ALLOWED_DIRS="/data/workspace" \
  my-filesystem-server
```

## Integration with AI Tools

### Claude Desktop
Add to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/home/user/documents:/data/docs:ro",
        "-v", "/tmp:/data/tmp:rw",
        "-e", "ALLOWED_DIRS=/data/docs /data/tmp",
        "dataeverything/mcp-filesystem"
      ]
    }
  }
}
```

### Continue.dev
```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "filesystem",
      "command": "mcp-template",
      "args": ["run", "filesystem", "--transport", "stdio"],
      "env": {
        "ALLOWED_DIRS": "/home/user/project /tmp"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

**Permission Denied**
```bash
# Ensure Docker has access to mount directories
sudo chown -R $USER:$USER /path/to/directory

# Check SELinux/AppArmor policies if applicable
ls -laZ /path/to/directory
```

**Directory Not Found**
```bash
# Verify allowed_dirs configuration
mcpt> call filesystem list_allowed_directories '{}'

# Check actual mount points in container
docker run --rm -v "/host/path:/container/path" \
  dataeverything/mcp-filesystem ls -la /container/path
```

**Tools Not Available**
```bash
# Verify configuration is properly set
mcpt> show_config filesystem

# Test tool discovery
mcpt> tools filesystem --force-server
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"
mcpt run filesystem --config log_level=DEBUG
```

## License

This template uses the `mcp-filesystem-server` from Mark3 Labs under their licensing terms. Please review the original project's license for usage rights and restrictions.

## Author

Sam Arora

## Version

1.0.0
