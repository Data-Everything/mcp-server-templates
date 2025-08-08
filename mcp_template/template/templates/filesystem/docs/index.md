# Filesystem MCP Server Documentation

## Overview

The Filesystem MCP Server provides secure, controlled access to local file systems for AI assistants through the Model Context Protocol (MCP). Built on the proven `mcp-filesystem-server` foundation, it offers comprehensive file and directory operations while maintaining strict security through configurable allowed directories.

## Quick Start

### Installation & Deployment

The filesystem template uses **stdio transport** and runs interactively rather than as a persistent deployment.

```bash
# Interactive mode (recommended)
mcpt interactive
mcpt> config filesystem allowed_dirs="/tmp /home/user/documents"
mcpt> tools filesystem
mcpt> call filesystem list_directory '{"path": "/tmp"}'

# Direct tool execution
mcpt run-tool filesystem list_directory \
  --config allowed_dirs="/tmp /home/user/documents" \
  '{"path": "/tmp"}'
```

### Configuration

#### Required Configuration
- **`allowed_dirs`** (required): Space-separated list of allowed directories
  - Environment: `ALLOWED_DIRS`
  - Example: `"/home/user/documents /tmp/workspace"`
  - Security: Only these directories and subdirectories are accessible

#### Optional Configuration
- **`log_level`**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
  - Environment: `LOG_LEVEL`
  - Default: `INFO`

### Configuration Examples

```bash
# Environment variables
export ALLOWED_DIRS="/home/user/documents /tmp"
export LOG_LEVEL="DEBUG"

# JSON config file
echo '{"allowed_dirs": "/tmp /home/user/documents", "log_level": "INFO"}' > config.json
mcpt run-tool filesystem list_directory --config-file config.json '{"path": "/tmp"}'

# CLI configuration
mcpt run-tool filesystem list_directory \
  --config allowed_dirs="/tmp /home/user/documents" \
  --config log_level="DEBUG" \
  '{"path": "/tmp"}'
```

## API Reference

### Available Tools

#### Directory Operations

##### `list_allowed_directories`
List all configured allowed directories.

**Parameters**: None
**Returns**: Array of allowed directory paths

**Example**:
```bash
mcpt> call filesystem list_allowed_directories '{}'
```

##### `list_directory`
List contents of a directory.

**Parameters**:
- `path` (string, required): Directory path to list

**Returns**: Array of files and subdirectories with metadata

**Example**:
```bash
mcpt> call filesystem list_directory '{"path": "/tmp"}'
```

##### `tree`
Display directory structure as a tree.

**Parameters**:
- `path` (string, required): Root directory path
- `max_depth` (integer, optional): Maximum depth to traverse

**Returns**: Tree structure representation

**Example**:
```bash
mcpt> call filesystem tree '{"path": "/tmp", "max_depth": 3}'
```

##### `create_directory`
Create a new directory.

**Parameters**:
- `path` (string, required): Directory path to create

**Returns**: Success confirmation

**Example**:
```bash
mcpt> call filesystem create_directory '{"path": "/tmp/new-folder"}'
```

#### File Operations

##### `read_file`
Read contents of a file.

**Parameters**:
- `path` (string, required): File path to read

**Returns**: File contents as string

**Example**:
```bash
mcpt> call filesystem read_file '{"path": "/tmp/example.txt"}'
```

##### `read_multiple_files`
Read multiple files efficiently in a single operation.

**Parameters**:
- `paths` (array, required): Array of file paths to read

**Returns**: Array of file contents with metadata

**Example**:
```bash
mcpt> call filesystem read_multiple_files '{"paths": ["/tmp/file1.txt", "/tmp/file2.txt"]}'
```

##### `write_file`
Create or overwrite a file with content.

**Parameters**:
- `path` (string, required): File path to write
- `content` (string, required): Content to write

**Returns**: Success confirmation

**Example**:
```bash
mcpt> call filesystem write_file '{"path": "/tmp/output.txt", "content": "Hello World!"}'
```

##### `modify_file`
Update specific parts of an existing file.

**Parameters**:
- `path` (string, required): File path to modify
- `content` (string, required): New content for the file

**Returns**: Success confirmation with modification details

**Example**:
```bash
mcpt> call filesystem modify_file '{"path": "/tmp/existing.txt", "content": "Updated content"}'
```

##### `copy_file`
Copy a file to a new location.

**Parameters**:
- `source` (string, required): Source file path
- `destination` (string, required): Destination file path

**Returns**: Success confirmation

**Example**:
```bash
mcpt> call filesystem copy_file '{"source": "/tmp/source.txt", "destination": "/tmp/backup.txt"}'
```

##### `move_file`
Move or rename a file.

**Parameters**:
- `source` (string, required): Source file path
- `destination` (string, required): Destination file path

**Returns**: Success confirmation

**Example**:
```bash
mcpt> call filesystem move_file '{"source": "/tmp/old.txt", "destination": "/tmp/new.txt"}'
```

##### `delete_file`
Delete a file or directory.

**Parameters**:
- `path` (string, required): Path to delete

**Returns**: Success confirmation

**Example**:
```bash
mcpt> call filesystem delete_file '{"path": "/tmp/unwanted.txt"}'
```

##### `get_file_info`
Get detailed metadata about a file or directory.

**Parameters**:
- `path` (string, required): File or directory path

**Returns**: Detailed metadata including size, permissions, timestamps

**Example**:
```bash
mcpt> call filesystem get_file_info '{"path": "/tmp/example.txt"}'
```

#### Search Operations

##### `search_files`
Search for files by name patterns.

**Parameters**:
- `path` (string, required): Directory to search in
- `pattern` (string, required): File name pattern (supports wildcards)

**Returns**: Array of matching file paths

**Example**:
```bash
mcpt> call filesystem search_files '{"path": "/tmp", "pattern": "*.txt"}'
```

##### `search_within_files`
Search for content within files.

**Parameters**:
- `path` (string, required): Directory to search in
- `pattern` (string, required): Content pattern to search for
- `file_pattern` (string, optional): File name pattern to limit search

**Returns**: Array of matches with file paths and line numbers

**Example**:
```bash
mcpt> call filesystem search_within_files '{"path": "/tmp", "pattern": "error", "file_pattern": "*.log"}'
```

## Advanced Usage

### Batch Operations
```bash
# Read multiple configuration files at once
mcpt> call filesystem read_multiple_files '{
  "paths": ["/etc/nginx/nginx.conf", "/etc/hosts", "/tmp/config.json"]
}'

# Search across multiple file types
mcpt> call filesystem search_within_files '{
  "path": "/var/log",
  "pattern": "ERROR|FATAL",
  "file_pattern": "*.log"
}'
```

### Working with Large Directories
```bash
# Use tree with depth limit for large directories
mcpt> call filesystem tree '{"path": "/usr", "max_depth": 2}'

# Search specific file patterns to narrow results
mcpt> call filesystem search_files '{"path": "/home", "pattern": "*.py"}'
```

### Security Best Practices
```bash
# Configure read-only access for sensitive directories
export ALLOWED_DIRS="/etc:/data/config:ro /var/log:/data/logs:ro /tmp:/data/tmp:rw"

# Use specific subdirectories rather than root access
export ALLOWED_DIRS="/home/user/documents /home/user/projects"
```

## Integration Examples

### Claude Desktop Configuration
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

### Continue.dev Integration
```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "filesystem",
      "command": "mcp-template",
      "args": ["run-tool", "filesystem"],
      "env": {
        "ALLOWED_DIRS": "/home/user/project /tmp"
      }
    }
  ]
}
```

### Custom Docker Integration
```bash
# Development environment
docker run -i --rm \
  -v "$PWD:/data/project:rw" \
  -v "/tmp:/data/tmp:rw" \
  -e ALLOWED_DIRS="/data/project /data/tmp" \
  -e LOG_LEVEL="DEBUG" \
  dataeverything/mcp-filesystem

# Production environment with read-only configs
docker run -i --rm \
  -v "/etc/app:/data/config:ro" \
  -v "/var/log/app:/data/logs:ro" \
  -v "/tmp/app:/data/temp:rw" \
  -e ALLOWED_DIRS="/data/config /data/logs /data/temp" \
  dataeverything/mcp-filesystem
```

## Development

### Local Development Setup
```bash
# Clone and setup
git clone https://github.com/DataEverything/mcp-server-templates.git
cd mcp-server-templates

# Install dependencies
pip install -r requirements.txt

# Configure environment
export ALLOWED_DIRS="/tmp /home/user/test-docs"
export LOG_LEVEL="DEBUG"

# Test locally
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | \
  python -m mcp_template.template.templates.filesystem
```

### Running Tests
```bash
# Template-specific tests
pytest mcp_template/template/templates/filesystem/tests/ -v

# Integration tests
pytest tests/test_volume_mount_command_args.py -v

# CLI parsing tests
pytest tests/test_cli_parsing_focused.py -v
```

### Custom Template Development
```bash
# Create new template based on filesystem
mcpt create my-custom-fs --base filesystem

# Modify template.json for custom configuration
# Extend Dockerfile for additional tools
# Add custom tests in tests/ directory
```

## Troubleshooting

### Common Issues

**"Directory not allowed" errors**
- Check `ALLOWED_DIRS` configuration
- Verify paths are absolute and accessible
- Use `list_allowed_directories` to confirm configuration

**Permission denied**
- Ensure Docker has access to mounted directories
- Check file/directory permissions on host system
- Verify container user has appropriate access

**Tools not discovered**
- Confirm configuration is properly set
- Use debug logging: `LOG_LEVEL=DEBUG`
- Test with `tools filesystem --force-server`

### Debug Commands
```bash
# Check configuration
mcpt> show_config filesystem

# List available tools
mcpt> tools filesystem

# Enable debug logging
mcpt> config filesystem log_level=DEBUG

# Test basic connectivity
mcpt> call filesystem list_allowed_directories '{}'
```

### Performance Optimization
```bash
# For large directories, use specific patterns
mcpt> call filesystem search_files '{"path": "/large-dir", "pattern": "specific-*.txt"}'

# Batch operations when possible
mcpt> call filesystem read_multiple_files '{"paths": ["file1", "file2", "file3"]}'

# Use tree with depth limits
mcpt> call filesystem tree '{"path": "/large-dir", "max_depth": 2}'
```

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [mcp-server-templates/issues](https://github.com/DataEverything/mcp-server-templates/issues)
- **Discord Community**: [Join our Discord](https://discord.gg/55Cfxe9gnr)
- **Documentation**: [Full Documentation](https://data-everything.github.io/mcp-server-templates/)

## License

This template incorporates the `mcp-filesystem-server` from Mark3 Labs. Please review the original project's license terms for complete usage rights and restrictions.

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m server
```

### Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/ -m "not integration"

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Docker

```bash
# Build the image
docker build -t dataeverything/mcp-filesystem .

# Run the container
docker run dataeverything/mcp-filesystem
```

## Troubleshooting

### Common Issues

1. **Server won't start**: Check that all required environment variables are set
2. **Tool not found**: Verify the MCP client is connected properly
3. **Permission errors**: Ensure the server has appropriate file system permissions

### Debug Mode

Enable debug logging by setting the `LOG_LEVEL` environment variable to `DEBUG`.

## Contributing

Contributions are welcome! Please see the main repository's contributing guidelines.

## License

This template is part of the MCP Server Templates project.

## Support

For support, please open an issue in the main repository or contact the maintainers.
