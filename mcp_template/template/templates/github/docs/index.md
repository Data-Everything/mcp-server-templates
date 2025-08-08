# GitHub MCP Server Documentation

## Overview

The GitHub MCP Server template now uses a custom MCP server image that wraps and extends the official GitHub MCP server. This enables support for platform-wide template variables and configuration management, providing a consistent experience across all MCP templates.

Our platform extends the official GitHub MCP server by providing:
- **🚀 One-Command Deployment**: Deploy and manage GitHub MCP servers with a single command
- **🔧 Dynamic Tool Discovery**: Automatically discover and catalog all 77+ available GitHub tools
- **📊 Comprehensive Monitoring**: Built-in logging, status monitoring, and error tracking
- **🔄 Auto-Scaling**: Docker-based deployment with automatic container management
- **⚙️ Configuration Management**: Simplified environment variable and secret management
- **🛡️ Security**: Secure token handling and access control
- **📈 Performance Optimization**: Efficient caching and connection pooling

## Available Tools (77 Total)

The GitHub MCP server provides comprehensive GitHub API access through 77 specialized tools organized by functionality:

### Repository Management
- **`create_repository`**: Create new GitHub repositories
- **`fork_repository`**: Fork repositories to your account or organization
- **`search_repositories`**: Search for GitHub repositories
- **`get_file_contents`**: Read file contents from repositories
- **`create_or_update_file`**: Create or update files in repositories
- **`delete_file`**: Delete files from repositories
- **`push_files`**: Push multiple files in a single commit

### Branch & Tag Management
- **`create_branch`**: Create new branches
- **`list_branches`**: List all repository branches
- **`get_tag`**: Get git tag details
- **`list_tags`**: List all repository tags
- **`get_commit`**: Get commit details
- **`list_commits`**: List repository commits

### Issue Management
- **`create_issue`**: Create new issues
- **`get_issue`**: Get issue details
- **`update_issue`**: Update existing issues
- **`list_issues`**: List repository issues
- **`search_issues`**: Search issues across repositories
- **`add_issue_comment`**: Add comments to issues
- **`get_issue_comments`**: Get issue comments
- **`add_sub_issue`**: Add sub-issues to parent issues
- **`list_sub_issues`**: List sub-issues for an issue
- **`remove_sub_issue`**: Remove sub-issues
- **`reprioritize_sub_issue`**: Reorder sub-issues

### Pull Request Management
- **`create_pull_request`**: Create new pull requests
- **`get_pull_request`**: Get pull request details
- **`update_pull_request`**: Update existing pull requests
- **`list_pull_requests`**: List repository pull requests
- **`search_pull_requests`**: Search pull requests
- **`merge_pull_request`**: Merge pull requests
- **`get_pull_request_comments`**: Get PR comments
- **`get_pull_request_diff`**: Get PR diff
- **`get_pull_request_files`**: Get changed files in PR
- **`get_pull_request_reviews`**: Get PR reviews
- **`get_pull_request_status`**: Get PR status
- **`update_pull_request_branch`**: Update PR branch

### Code Review & Comments
- **`create_pending_pull_request_review`**: Create pending reviews
- **`add_comment_to_pending_pull_request_review`**: Add review comments
- **`submit_pending_pull_request_review`**: Submit reviews
- **`delete_pending_pull_request_review`**: Delete pending reviews
- **`create_and_submit_pull_request_review`**: Create and submit reviews
- **`request_copilot_review`**: Request GitHub Copilot reviews
- **`assign_copilot_to_issue`**: Assign Copilot to issues

### GitHub Actions & Workflows
- **`list_workflows`**: List repository workflows
- **`run_workflow`**: Trigger workflow runs
- **`get_workflow_run`**: Get workflow run details
- **`list_workflow_runs`**: List workflow runs
- **`cancel_workflow_run`**: Cancel running workflows
- **`rerun_workflow_run`**: Re-run entire workflows
- **`rerun_failed_jobs`**: Re-run only failed jobs
- **`list_workflow_jobs`**: List workflow jobs
- **`get_job_logs`**: Get job logs
- **`get_workflow_run_logs`**: Get complete workflow logs
- **`get_workflow_run_usage`**: Get workflow usage metrics
- **`list_workflow_run_artifacts`**: List workflow artifacts
- **`download_workflow_run_artifact`**: Download artifacts
- **`delete_workflow_run_logs`**: Delete workflow logs

### Security & Scanning
- **`list_code_scanning_alerts`**: List code scanning alerts
- **`get_code_scanning_alert`**: Get specific code scanning alerts
- **`list_dependabot_alerts`**: List Dependabot alerts
- **`get_dependabot_alert`**: Get specific Dependabot alerts
- **`list_secret_scanning_alerts`**: List secret scanning alerts
- **`get_secret_scanning_alert`**: Get specific secret scanning alerts

### Discussions
- **`list_discussions`**: List repository discussions
- **`get_discussion`**: Get discussion details
- **`get_discussion_comments`**: Get discussion comments
- **`list_discussion_categories`**: List discussion categories

### Notifications & Activity
- **`list_notifications`**: List GitHub notifications
- **`get_notification_details`**: Get notification details
- **`dismiss_notification`**: Mark notifications as read
- **`mark_all_notifications_read`**: Mark all notifications read
- **`manage_notification_subscription`**: Manage notification settings
- **`manage_repository_notifications`**: Manage repository notifications

### Search & Discovery
- **`search_code`**: Search code across repositories
- **`search_users`**: Search GitHub users
- **`search_orgs`**: Search GitHub organizations

### User & Profile
- **`get_me`**: Get authenticated user details

## Quick Start

### Installation

Deploy the GitHub MCP server using our platform:

```bash
# Deploy with automatic configuration
mcpt deploy github

# Deploy with custom configuration
mcpt deploy github --config GITHUB_PERSONAL_ACCESS_TOKEN="your_token"

# Check deployment status
mcpt status github

# View real-time logs
mcpt logs github
```

### Configuration

The template requires a GitHub Personal Access Token for authentication:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub Personal Access Token with appropriate scopes | Yes | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

#### Creating a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with required scopes:
   - `repo` - Full repository access
   - `workflow` - GitHub Actions access
   - `notifications` - Notification access
   - `security_events` - Security alert access

### Usage Examples

#### Repository Operations
```bash
# List repository files
mcp-client call get_file_contents --owner "octocat" --repo "Hello-World" --path "README.md"

# Create a new file
mcp-client call create_or_update_file --owner "user" --repo "repo" --path "new_file.py" --content "print('Hello')" --message "Add new file"

# Create a new repository
mcp-client call create_repository --name "my-new-repo" --description "A new repository"
```

#### Issue Management
```bash
# Create an issue
mcp-client call create_issue --owner "user" --repo "repo" --title "Bug Report" --body "Found a bug"

# Add a comment to an issue
mcp-client call add_issue_comment --owner "user" --repo "repo" --issue_number 1 --body "Working on this"

# Search for issues
mcp-client call search_issues --query "is:open label:bug"
```

#### Pull Request Workflow
```bash
# Create a pull request
mcp-client call create_pull_request --owner "user" --repo "repo" --title "Feature" --head "feature-branch" --base "main"

# Review a pull request
mcp-client call create_pending_pull_request_review --owner "user" --repo "repo" --pull_number 1
mcp-client call add_comment_to_pending_pull_request_review --body "Looks good!"
mcp-client call submit_pending_pull_request_review --event "APPROVE"
```

#### GitHub Actions
```bash
# List workflows
mcp-client call list_workflows --owner "user" --repo "repo"

# Trigger a workflow
mcp-client call run_workflow --owner "user" --repo "repo" --workflow_id "deploy.yml"

# Get workflow run logs
mcp-client call get_job_logs --owner "user" --repo "repo" --run_id 123456 --failed_only true
```

## Tool Discovery

Our platform provides dynamic tool discovery to automatically catalog all available GitHub tools:

```bash
# Discover all available tools
mcpt> tools github --config GITHUB_PERSONAL_ACCESS_TOKEN="your_token"

# Refresh tool cache
mcpt> tools github --refresh

# Get detailed tool information
mcpt> tools github --verbose
```

## Platform Benefits

### Enhanced Deployment
- **Docker Integration**: Seamless container-based deployment
- **Environment Management**: Secure handling of GitHub tokens
- **Health Monitoring**: Automatic health checks and restart policies
- **Port Management**: Automatic port allocation and management

### Advanced Tooling
- **Real-time Discovery**: Dynamic discovery of all 77 GitHub tools
- **Intelligent Caching**: Tool information caching for improved performance
- **Error Handling**: Robust error handling and retry mechanisms
- **Logging**: Comprehensive request/response logging

### Developer Experience
- **One-Command Setup**: Deploy GitHub integration in seconds
- **Interactive CLI**: Rich terminal interface with progress indicators
- **Comprehensive Documentation**: Auto-generated tool documentation
- **Testing Integration**: Built-in testing framework for GitHub operations

## Development

### Local Development

```bash
# Clone and set up local development
git clone <repository-url>
cd github-template

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token"
export LOG_LEVEL="DEBUG"

# Run the server locally
python -m server
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/test_github_integration.py

# Test with real GitHub API (requires token)
pytest tests/ --github-token="your_token"
```

### Docker Development

```bash
# Build local image
docker build -t github-mcp-local .

# Run with environment variables
docker run -e GITHUB_PERSONAL_ACCESS_TOKEN="your_token" github-mcp-local

# Run with our platform
mcpt deploy github --local
```

## Monitoring & Troubleshooting

### Health Checks

```bash
# Check service status
mcpt status github

# Get detailed health information
mcpt status github --detailed

# View real-time logs
mcpt logs github --follow
```

### Common Issues

1. **Authentication Errors**
   - Verify GitHub token has correct scopes
   - Check token expiration date
   - Ensure token is properly set in environment

2. **Rate Limiting**
   - GitHub API has rate limits (5000 requests/hour for authenticated users)
   - Use conditional requests when possible
   - Consider GitHub Apps for higher limits

3. **Permission Errors**
   - Verify repository access permissions
   - Check organization policies
   - Ensure token has required scopes

4. **Network Issues**
   - Check GitHub API status at https://www.githubstatus.com/
   - Verify network connectivity
   - Check firewall settings

### Debug Mode

Enable comprehensive debugging:

```bash
# Deploy with debug logging
mcpt deploy github --config LOG_LEVEL="DEBUG"

# View debug logs
mcpt logs github --level debug

# Enable trace logging for API calls
mcpt logs github --trace
```

## Security

### Token Management
- **Secure Storage**: Tokens are stored securely and never logged
- **Scope Validation**: Automatic validation of token scopes
- **Rotation Support**: Easy token rotation without service interruption

### Access Control
- **Principle of Least Privilege**: Request only necessary GitHub scopes
- **Audit Logging**: All API calls are logged for audit purposes
- **Error Sanitization**: Sensitive information is never exposed in error messages

## Performance Optimization

### Caching Strategy
- **Tool Discovery Cache**: Cache discovered tools for improved performance
- **Response Caching**: Cache frequently accessed GitHub data
- **Connection Pooling**: Efficient HTTP connection management

### Rate Limit Management
- **Intelligent Throttling**: Automatic rate limit respect
- **Request Batching**: Batch compatible requests
- **Priority Queuing**: Prioritize critical operations

## API Reference

All 77 GitHub tools are available through the MCP interface. Each tool includes:
- **Input Schema**: Detailed parameter specifications
- **Output Schema**: Response format documentation
- **Error Handling**: Comprehensive error response patterns
- **Examples**: Real-world usage examples

For detailed API documentation of each tool, use:
```bash
mcpt> tools github --tool-name <tool_name> --detailed
```

## Contributing

We welcome contributions to improve the GitHub MCP server template:

1. **Bug Reports**: Submit issues with detailed reproduction steps
2. **Feature Requests**: Propose new GitHub integrations
3. **Pull Requests**: Contribute code improvements
4. **Documentation**: Help improve this documentation

See the main repository's contributing guidelines for detailed information.

## License

This template extends the official GitHub MCP server and is part of the MCP Server Templates project. See LICENSE for details.

## Support

For support, please open an issue in the main repository or contact the maintainers.
