# Stdio Tool Execution Guide

This guide covers executing tools from stdio MCP servers using the `run-tool` command. Stdio MCP servers use standard input/output for communication and are designed for interactive tool execution rather than persistent deployment.

## Overview

### Transport Types

MCP servers support two transport types:

- **HTTP Transport**: Servers run as persistent containers accessible via HTTP endpoints. Use `mcpt deploy` for these servers.
- **Stdio Transport**: Servers run interactively using stdin/stdout communication. Use `mcpt run-tool` for these servers.

### Why Stdio Servers Can't Be Deployed

Stdio MCP servers are designed for interactive communication and cannot run as persistent background services. When you attempt to deploy a stdio server, you'll see a helpful error message:

```bash
$ mcpt deploy github
❌ Cannot deploy stdio transport MCP servers

The template github uses stdio transport, which doesn't require deployment.
Stdio MCP servers run interactively and cannot be deployed as persistent containers.

Available tools in this template:
  • search_repositories
  • create_repository
  • get_file_contents
  • create_issue
  • create_pull_request

To use this template, run tools directly:
  mcpt> tools github                         # List available tools
  mcpt run-tool github <tool_name>          # Run a specific tool
```

## Basic Usage

### 1. Discovering Available Tools

Before running tools, discover what's available:

```bash
# List all tools in a template
mcpt> tools github

# List tools with configuration (for dynamic discovery)
mcpt> tools github --config github_token=your_token

# Force refresh tool cache
mcpt> tools github --refresh

# Discover tools from a Docker image directly
mcpt> tools --image mcp/custom-server:latest
```

### 2. Running Tools

Execute individual tools using the `run-tool` command:

```bash
# Basic syntax
mcpt run-tool <template> <tool_name> [options]

# Simple example
mcpt run-tool github search_repositories --args '{"query": "mcp server"}'
```

## Command Options

### `--args`: JSON Tool Arguments

Pass structured data to tools using JSON format:

```bash
# Simple arguments
mcpt run-tool github search_repositories \
  --args '{"query": "mcp server", "per_page": 10}'

# Complex nested arguments
mcpt run-tool github create_pull_request \
  --args '{
    "owner": "username",
    "repo": "project",
    "title": "Feature: Add new functionality",
    "head": "feature-branch",
    "base": "main",
    "body": "This PR adds:\n- Feature 1\n- Feature 2"
  }'
```

### `--env`: Environment Variables

Provide authentication and configuration via environment variables:

```bash
# GitHub authentication
mcpt run-tool github create_issue \
  --args '{"owner": "user", "repo": "test", "title": "Bug report"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Multiple environment variables
mcpt run-tool database query \
  --args '{"sql": "SELECT * FROM users"}' \
  --env DB_HOST=localhost \
  --env DB_PORT=5432 \
  --env DB_PASSWORD=secret
```

### `--config`: Server Configuration

Configure the MCP server behavior:

```bash
# Filesystem security settings
mcpt run-tool filesystem read_file \
  --args '{"path": "/data/file.txt"}' \
  --config allowed_directories='["/data", "/workspace"]' \
  --config read_only=true

# Timeout and performance settings
mcpt run-tool api-client fetch_data \
  --args '{"url": "https://api.example.com/data"}' \
  --config timeout=30 \
  --config max_retries=3
```

## Practical Examples

### GitHub Operations

```bash
# Search for repositories
mcpt run-tool github search_repositories \
  --args '{"query": "python machine learning", "sort": "stars"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Get file contents from a repository
mcpt run-tool github get_file_contents \
  --args '{"owner": "microsoft", "repo": "vscode", "path": "README.md"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Create an issue
mcpt run-tool github create_issue \
  --args '{
    "owner": "user",
    "repo": "project",
    "title": "Bug: Application crashes on startup",
    "body": "## Description\nThe app crashes when...\n\n## Steps to Reproduce\n1. Step 1\n2. Step 2",
    "labels": ["bug", "high-priority"]
  }' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Search for users
mcpt run-tool github search_users \
  --args '{"q": "location:San Francisco followers:>100"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token
```

### Filesystem Operations

```bash
# List directory contents
mcpt run-tool filesystem list_directory \
  --args '{"path": "/data"}' \
  --config allowed_directories='["/data", "/workspace"]'

# Read file contents
mcpt run-tool filesystem read_file \
  --args '{"path": "/data/config.json"}' \
  --config allowed_directories='["/data"]' \
  --config read_only=true

# Create a new file
mcpt run-tool filesystem create_file \
  --args '{"path": "/workspace/output.txt", "content": "Hello, World!"}' \
  --config allowed_directories='["/workspace"]' \
  --config read_only=false

# Search files
mcpt run-tool filesystem search_files \
  --args '{"pattern": "*.py", "directory": "/workspace"}' \
  --config allowed_directories='["/workspace"]'
```

### Database Operations

```bash
# Execute a query
mcpt run-tool database query \
  --args '{"sql": "SELECT name, email FROM users WHERE active = true LIMIT 10"}' \
  --config connection_string="postgresql://localhost:5432/mydb" \
  --env DB_PASSWORD=secret

# Get table schema
mcpt run-tool database describe_table \
  --args '{"table_name": "users"}' \
  --config connection_string="postgresql://localhost:5432/mydb" \
  --env DB_PASSWORD=secret
```

### Custom MCP Servers

```bash
# Work with custom Docker images
mcpt> tools --image company/custom-mcp:latest

# Run tools from custom servers
mcpt run-tool custom-template analyze_data \
  --args '{"dataset": "sales_2024.csv", "type": "summary"}' \
  --config input_directory="/data" \
  --config output_format="json"
```

## Error Handling

### Common Errors and Solutions

**1. Template Not Found**
```bash
$ mcpt run-tool nonexistent search
❌ Template 'nonexistent' not found
```
*Solution*: Check available templates with `mcpt list`

**2. Tool Not Found**
```bash
$ mcpt run-tool github invalid_tool
❌ Unknown tool: invalid_tool
```
*Solution*: List available tools with `mcpt> tools github`

**3. Invalid JSON Arguments**
```bash
$ mcpt run-tool github search --args '{invalid json}'
❌ Invalid JSON in tool arguments: {invalid json}
```
*Solution*: Validate JSON syntax, use online JSON validators

**4. Authentication Errors**
```bash
❌ Tool execution failed: Authentication required
```
*Solution*: Provide required environment variables (e.g., API tokens)

**5. Permission Errors**
```bash
❌ Tool execution failed: Access denied to path /restricted
```
*Solution*: Check `allowed_directories` configuration for filesystem tools

## Advanced Usage

### Configuration Files

For complex configurations, use configuration files:

```json
// config.json
{
  "security": {
    "allowed_directories": ["/data", "/workspace"],
    "read_only": false,
    "max_file_size": 100
  },
  "performance": {
    "timeout": 30,
    "max_concurrent_operations": 5
  }
}
```

```bash
# Use configuration file (if supported by the template)
mcpt run-tool filesystem read_file \
  --args '{"path": "/data/file.txt"}' \
  --config-file config.json
```

### Scripting and Automation

Use run-tool in scripts for automation:

```bash
#!/bin/bash

# Automated GitHub workflow
GITHUB_TOKEN="your_token"

# Search for issues
echo "Searching for open issues..."
mcpt run-tool github search_issues \
  --args '{"q": "repo:user/project state:open label:bug"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"

# Create a new issue
echo "Creating issue..."
mcpt run-tool github create_issue \
  --args '{"owner": "user", "repo": "project", "title": "Automated Issue", "body": "Created by script"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
```

### Integration with Other Tools

Combine with standard Unix tools:

```bash
# Process JSON output with jq
mcpt run-tool github search_repositories \
  --args '{"query": "mcp"}' \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=token | \
  jq '.items[0:5] | .[] | {name: .name, stars: .stargazers_count}'

# Save output to file
mcpt run-tool filesystem list_directory \
  --args '{"path": "/data"}' > directory_listing.json
```

## Best Practices

### 1. Security
- Never hardcode sensitive tokens in scripts
- Use environment variables or secure config files for authentication
- Configure appropriate `allowed_directories` for filesystem access
- Enable `read_only` mode when write access isn't needed

### 2. Performance
- Use appropriate timeout values for long-running operations
- Cache tool discovery results when possible
- Limit result sets with pagination parameters

### 3. Error Handling
- Always check tool output for errors before processing
- Use `--refresh` flag if tool discovery seems outdated
- Validate JSON arguments before sending complex requests

### 4. Documentation
- Use `mcpt> tools <template>` to discover available tools
- Check template documentation for specific configuration options
- Review tool descriptions and parameter requirements

## Integration Examples

### VS Code/Cursor Integration

```json
{
  "tasks": [
    {
      "label": "Search GitHub Issues",
      "type": "shell",
      "command": "mcpt run-tool github search_issues --args '{\"q\": \"${input:searchQuery}\"}' --env GITHUB_PERSONAL_ACCESS_TOKEN=${env:GITHUB_TOKEN}",
      "group": "build"
    }
  ]
}
```

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
name: MCP Tool Integration
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install MCP Template
        run: pip install mcp-template
      - name: Analyze Repository
        run: |
          mcpt run-tool filesystem search_files \
            --args '{"pattern": "*.py", "directory": "."}' \
            --config allowed_directories='["."]' > analysis.json
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

This comprehensive guide should help you effectively use stdio MCP servers with the `run-tool` command for interactive tool execution.
