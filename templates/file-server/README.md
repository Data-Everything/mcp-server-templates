# File Server MCP Template

A secure file system access server for AI assistants, built on top of the official [@modelcontextprotocol/server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) with enhanced platform integration, security features, and monitoring capabilities.

## Overview

This template extends the robust, battle-tested official MCP filesystem server with additional features specifically designed for the MCP Platform:

- **Enhanced Security**: Path validation, symlink handling, and configurable access controls
- **Platform Integration**: Seamless deployment and monitoring within MCP Platform
- **Advanced Configuration**: Flexible settings for different use cases and environments
- **Audit Logging**: Comprehensive logging of all file operations for compliance
- **Health Monitoring**: Built-in health checks and performance metrics

## Based on Official MCP Filesystem Server

This template leverages the official `@modelcontextprotocol/server-filesystem` which provides:

- ✅ **Robust file operations**: Read, write, edit, list, search, move
- ✅ **Security by design**: Path traversal protection, symlink validation
- ✅ **Performance optimized**: Efficient file handling and streaming
- ✅ **Well tested**: Comprehensive test suite and real-world usage
- ✅ **Active maintenance**: Regular updates and security patches

### Why extend instead of rebuild?

Following the principle "don't reinvent the wheel", this template:
- Reuses the proven filesystem server implementation
- Adds platform-specific enhancements and configuration
- Provides additional security layers and monitoring
- Maintains compatibility with official MCP protocol standards

🛠️ **What you get**: Complete MCP server source code, Docker configurations, deployment guides, full customization freedom

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ROOT_PATH` | Base directory for all file operations | `/data` | `/home/user/files` |
| `MAX_FILE_SIZE` | Maximum file size in MB | `10` | `50` |
| `READ_ONLY` | Enable read-only mode | `false` | `true` |
| `ALLOWED_EXTENSIONS` | JSON array of allowed extensions | `[".*"]` | `[".txt", ".json", ".md"]` |
| `ENABLE_SUBDIRECTORIES` | Allow subdirectory access | `true` | `false` |
| `LOG_FILE_OPERATIONS` | Enable audit logging | `true` | `false` |
| `AUDIT_LOG_PATH` | Path for audit logs | `/logs/file_operations.log` | `/var/log/mcp.log` |

### Security Configuration Examples

## Features

### File Operations
- **Read files**: Complete file contents or partial reads (head/tail)
- **Write files**: Create new files or overwrite existing ones
- **Edit files**: Smart editing with pattern matching and diff preview
- **Directory operations**: List, create, and navigate directories
- **File search**: Recursive file and content search with glob patterns
- **File management**: Move, rename, and get detailed file information

### Security Features
- **Path validation**: Prevents directory traversal attacks
- **Sandboxed access**: Restricts operations to configured directories
- **Symlink handling**: Configurable symlink resolution with validation
- **File size limits**: Configurable maximum file sizes for operations
- **Pattern exclusions**: Exclude sensitive files and directories
- **Audit logging**: Track all file operations for security compliance

### Platform Integration
- **Docker ready**: Optimized container with security best practices
- **Health monitoring**: Built-in health checks and metrics
- **Configuration management**: Flexible JSON and environment variable config
- **Logging**: Structured logging with rotation and retention
- **Graceful shutdown**: Proper cleanup and signal handling

## Quick Start

### Using MCP Platform (Recommended)

1. **Deploy via Platform UI**:
   - Go to your MCP Platform dashboard
   - Click "Add Server" → "From Template"
   - Select "File Server" template
   - Configure directories and permissions
   - Deploy with one click

2. **Configure Access**:
   ```json
   {
     "allowed_directories": ["/data", "/workspace"],
     "read_only_mode": false,
     "max_file_size": 100,
     "exclude_patterns": ["**/.git/**", "**/node_modules/**"]
   }
   ```

### Self-Hosted Deployment

1. **Clone and Build**:
   ```bash
   git clone https://github.com/Data-Everything/mcp-server-templates.git
   cd mcp-server-templates/file-server
   docker build -t mcp-file-server .
   ```

2. **Run with Docker**:
   ```bash
   docker run -d \
     --name mcp-file-server \
     -v /path/to/your/data:/data \
     -v /path/to/logs:/logs \
     -e MCP_ALLOWED_DIRS="/data" \
     -e MCP_READ_ONLY=false \
     mcp-file-server
   ```

3. **Connect to MCP Client**:
   ```json
   {
     "servers": {
       "file-server": {
         "command": "docker",
         "args": ["exec", "-i", "mcp-file-server", "node", "src/platform-wrapper.js"]
       }
     }
   }
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ALLOWED_DIRS` | Colon-separated list of allowed directories | `/data` |
| `MCP_READ_ONLY` | Enable read-only mode | `false` |
| `MCP_ENABLE_SYMLINKS` | Allow symlink resolution | `true` |
| `MCP_MAX_FILE_SIZE` | Maximum file size in bytes | `104857600` (100MB) |
| `MCP_EXCLUDE_PATTERNS` | Comma-separated exclusion patterns | `.git,.env` |
| `LOG_LEVEL` | Logging level (debug, info, warn, error) | `info` |

### Configuration File

Create `/app/config/file-server.json`:

```json
{
  "security": {
    "allowedDirs": ["/data", "/workspace"],
    "readOnly": false,
    "enableSymlinks": true,
    "maxFileSize": 104857600,
    "excludePatterns": [
      "**/.git/**",
      "**/node_modules/**",
      "**/.env*"
    ]
  },
  "logging": {
    "level": "info",
    "enableAudit": true,
    "logFile": "/logs/file-server.log"
  }
}
```

## Available Tools

### File Operations
- `read_file` - Read complete file contents with head/tail support
- `read_multiple_files` - Efficiently read multiple files in batch
- `write_file` - Create or overwrite files with validation
- `edit_file` - Smart file editing with pattern matching

### Directory Operations  
- `list_directory` - List directory contents with metadata
- `create_directory` - Create directories recursively
- `directory_tree` - Get complete directory structure as JSON

### Search and Discovery
- `search_files` - Find files matching patterns recursively
- `get_file_info` - Detailed file/directory metadata
- `list_allowed_directories` - Show accessible root directories

### Management
- `move_file` - Safely move or rename files and directories

## Security Considerations

### Path Security
- All paths are validated against allowed directories
- Directory traversal attempts (`../`) are blocked
- Symlinks are optionally resolved with validation
- Hidden files and system directories can be excluded

### File Size Limits
- Configurable maximum file sizes prevent resource exhaustion
- Large file operations are streamed for memory efficiency
- Timeout protection for long-running operations

### Audit Trail
- All file operations are logged with timestamps
- User context and operation details recorded
- Configurable log retention and rotation
- Integration with platform monitoring

## Monitoring and Health

### Health Checks
The server provides comprehensive health monitoring:

```bash
# Check server health
docker exec mcp-file-server node src/health-check.js

# Verbose health information
docker exec -e HEALTH_CHECK_VERBOSE=true mcp-file-server node src/health-check.js
```

### Metrics
- File operation counts and timings
- Memory and CPU usage tracking
- Error rates and types
- Directory access patterns

### Logging
Structured JSON logs include:
- Operation type and parameters
- Success/failure status
- Performance timing
- Error details and stack traces

## Integration Examples

### Basic File Operations
```javascript
// Read a configuration file
const config = await mcp.callTool('read_file', {
  path: '/data/config.json'
});

// Write processed data
await mcp.callTool('write_file', {
  path: '/data/output.txt',
  contents: processedData
});

// Search for log files
const logFiles = await mcp.callTool('search_files', {
  pattern: '**/*.log',
  path: '/data/logs'
});
```

### Advanced Usage
```javascript
// Batch read multiple files
const files = await mcp.callTool('read_multiple_files', {
  paths: [
    '/data/file1.txt',
    '/data/file2.txt',
    '/data/file3.txt'
  ]
});

// Smart file editing
await mcp.callTool('edit_file', {
  path: '/data/config.ini',
  pattern: 'database_url=.*',
  replacement: 'database_url=postgresql://newhost:5432/db'
});
```

## Platform vs Self-Hosted

| Feature | Platform | Self-Hosted |
|---------|----------|-------------|
| **Deployment** | One-click deploy | Manual setup |
| **Security** | Platform-managed | Self-managed |
| **Monitoring** | Built-in dashboard | Manual setup |
| **Updates** | Automatic | Manual |
| **Scaling** | Auto-scaling | Manual scaling |
| **Support** | 24/7 platform support | Community |
| **Cost** | Usage-based pricing | Infrastructure costs |

## Support and Resources

- 📖 **Documentation**: [Template Development Guide](https://docs.mcp-platform.ai/templates/file-server)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- 💬 **Community**: [MCP Platform Discord](https://discord.gg/mcp-platform)
- 🔧 **Base Server**: [@modelcontextprotocol/server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

## License

MIT License - see [LICENSE](LICENSE) file for details.

This template builds upon the official MCP filesystem server which is also MIT licensed.
# Last updated: Thu 24 Jul 2025 18:16:58 AEST
# Updated: Thu 24 Jul 2025 18:34:40 AEST
