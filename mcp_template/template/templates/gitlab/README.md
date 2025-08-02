# GitLab MCP Server Template

A comprehensive Model Context Protocol (MCP) server template for GitLab integration, providing extensive API coverage for project management, version control, CI/CD pipelines, and collaboration features.

## Overview

This template provides access to GitLab's rich ecosystem through the enhanced GitLab MCP server implementation. It includes 66+ tools covering all major GitLab functionalities from basic repository operations to advanced project management features.

## Key Features

- **Complete GitLab API Coverage**: Access to repositories, issues, merge requests, pipelines, wiki, milestones, and more
- **Flexible Authentication**: Support for personal access tokens and cookie-based authentication
- **Transport Options**: stdio, Server-Sent Events (SSE), and Streamable HTTP transports
- **Security Controls**: Read-only mode and configurable feature toggles
- **Enterprise Ready**: Support for self-hosted GitLab instances with proxy configuration
- **Modular Features**: Enable/disable wiki, milestone, and pipeline tools as needed

## Quick Start

### 1. Prerequisites

- GitLab personal access token with appropriate scopes
- Docker (recommended) or Node.js environment

### 2. Configuration

Create your MCP configuration with the GitLab server:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITLAB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITLAB_API_URL",
        "iwakitakuma/gitlab-mcp"
      ],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "your_gitlab_token",
        "GITLAB_API_URL": "https://gitlab.com/api/v4"
      }
    }
  }
}
```

### 3. Basic Usage

Once configured, you can:
- Search and manage GitLab projects
- Create and update files in repositories
- Manage issues and merge requests
- Access CI/CD pipeline information
- Work with project wikis and milestones

## Configuration Options

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `GITLAB_PERSONAL_ACCESS_TOKEN` | GitLab personal access token | - | ✅ |
| `GITLAB_API_URL` | GitLab API endpoint | `https://gitlab.com/api/v4` | ❌ |
| `GITLAB_PROJECT_ID` | Default project ID | - | ❌ |
| `GITLAB_READ_ONLY_MODE` | Enable read-only operations | `false` | ❌ |
| `USE_GITLAB_WIKI` | Enable wiki tools | `false` | ❌ |
| `USE_MILESTONE` | Enable milestone tools | `false` | ❌ |
| `USE_PIPELINE` | Enable pipeline tools | `false` | ❌ |

## Transport Modes

### stdio (Default)
Standard input/output communication - most compatible:

```json
{
  "command": "npx",
  "args": ["-y", "@zereight/mcp-gitlab"],
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "your_token"
  }
}
```

### Server-Sent Events (SSE)
For web-based integrations:

```json
{
  "type": "sse",
  "url": "http://localhost:3333/sse"
}
```

### Streamable HTTP
For high-performance scenarios:

```json
{
  "url": "http://localhost:3333/mcp"
}
```

## Tool Categories

### Repository Management
- `search_repositories` - Find GitLab projects
- `create_repository` - Create new projects
- `fork_repository` - Fork existing projects
- `get_file_contents` - Read file contents
- `create_or_update_file` - Modify files
- `push_files` - Batch file operations
- `get_repository_tree` - Browse project structure

### Issue Management
- `list_issues` - Browse project issues
- `get_issue` - Get issue details
- `create_issue` - Create new issues
- `update_issue` - Modify existing issues
- `delete_issue` - Remove issues
- `create_issue_link` - Link related issues
- `list_issue_discussions` - View issue conversations

### Merge Request Operations
- `list_merge_requests` - Browse merge requests
- `get_merge_request` - Get MR details
- `create_merge_request` - Create new MRs
- `update_merge_request` - Modify existing MRs
- `get_merge_request_diffs` - View changes
- `create_merge_request_thread` - Add review comments

### CI/CD Pipeline Management (Optional)
- `list_pipelines` - Browse CI/CD pipelines
- `get_pipeline` - Get pipeline details
- `create_pipeline` - Trigger new pipelines
- `retry_pipeline` - Retry failed pipelines
- `cancel_pipeline` - Stop running pipelines
- `list_pipeline_jobs` - View pipeline jobs
- `get_pipeline_job_output` - Read job logs

### Wiki Management (Optional)
- `list_wiki_pages` - Browse wiki pages
- `get_wiki_page` - Read wiki content
- `create_wiki_page` - Create new pages
- `update_wiki_page` - Edit existing pages
- `delete_wiki_page` - Remove pages

### Project Milestones (Optional)
- `list_milestones` - Browse project milestones
- `get_milestone` - Get milestone details
- `create_milestone` - Create new milestones
- `edit_milestone` - Modify milestones
- `get_milestone_issues` - View milestone progress

## Security Features

### Read-Only Mode
Enable `GITLAB_READ_ONLY_MODE=true` to restrict operations to read-only tools:
- Repository browsing
- Issue and MR viewing
- Pipeline monitoring
- Wiki reading

### Feature Toggles
Control which tool categories are available:
- `USE_GITLAB_WIKI=false` - Disable wiki tools
- `USE_MILESTONE=false` - Disable milestone tools  
- `USE_PIPELINE=false` - Disable pipeline tools

## Self-Hosted GitLab

For GitLab Enterprise or self-hosted instances:

```json
{
  "env": {
    "GITLAB_API_URL": "https://gitlab.company.com/api/v4",
    "GITLAB_PERSONAL_ACCESS_TOKEN": "your_token",
    "HTTP_PROXY": "http://proxy.company.com:8080"
  }
}
```

## Best Practices

1. **Token Scopes**: Ensure your GitLab token has appropriate scopes:
   - `api` - Full API access
   - `read_user` - User information
   - `read_repository` - Repository access
   - `write_repository` - File modifications

2. **Security**: Use read-only mode in production environments where write access isn't needed

3. **Performance**: Enable only required feature sets to optimize tool discovery

4. **Enterprise**: Configure proxy settings for corporate environments

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify token is valid and not expired
- Check token scopes include required permissions
- Ensure API URL is correct for your GitLab instance

**Connection Timeout**
- Verify network connectivity to GitLab instance
- Configure proxy settings if behind corporate firewall
- Check if GitLab instance is accessible

**Tool Not Found**
- Verify feature toggles are correctly configured
- Check if read-only mode is preventing write operations
- Ensure GitLab instance supports the API version

### Debug Mode

Enable detailed logging:

```json
{
  "env": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

## Examples

See the `docs/` directory for comprehensive examples and the `tests/` directory for integration test patterns.

## Version Compatibility

- GitLab CE/EE 13.0+
- GitLab.com (SaaS)
- Self-hosted GitLab instances

## License

This template integrates with the GitLab MCP server which is licensed under MIT. See the original project at [zereight/gitlab-mcp](https://github.com/zereight/gitlab-mcp) for details.
