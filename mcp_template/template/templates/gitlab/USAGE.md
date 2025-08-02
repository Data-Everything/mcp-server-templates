# GitLab MCP Server Usage Guide

This guide provides practical examples and patterns for using the GitLab MCP server template effectively.

## Table of Contents

1. [Setup Scenarios](#setup-scenarios)
2. [Common Operations](#common-operations)
3. [Advanced Workflows](#advanced-workflows)
4. [Integration Patterns](#integration-patterns)
5. [Performance Optimization](#performance-optimization)

## Setup Scenarios

### Development Environment

For local development with full feature access:

```json
{
  "mcpServers": {
    "gitlab-dev": {
      "command": "npx",
      "args": ["-y", "@zereight/mcp-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat-xxxxxxxxxxxxxxxxxxxx",
        "GITLAB_API_URL": "https://gitlab.com/api/v4",
        "USE_GITLAB_WIKI": "true",
        "USE_MILESTONE": "true",
        "USE_PIPELINE": "true",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Production Environment

For production with security restrictions:

```json
{
  "mcpServers": {
    "gitlab-prod": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITLAB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITLAB_READ_ONLY_MODE=true",
        "iwakitakuma/gitlab-mcp"
      ],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat-readonly-token",
        "GITLAB_READ_ONLY_MODE": "true"
      }
    }
  }
}
```

### Self-Hosted GitLab

For enterprise GitLab installation:

```json
{
  "mcpServers": {
    "gitlab-enterprise": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITLAB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITLAB_API_URL",
        "-e", "HTTP_PROXY",
        "-e", "GITLAB_CA_CERT_PATH",
        "iwakitakuma/gitlab-mcp"
      ],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "your_enterprise_token",
        "GITLAB_API_URL": "https://gitlab.company.com/api/v4",
        "HTTP_PROXY": "http://proxy.company.com:8080",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      }
    }
  }
}
```

## Common Operations

### Repository Management

#### Browse and Search Projects

```bash
# Search for projects
search_repositories(search="machine-learning", page=1, per_page=10)

# Get project details
get_project(project_id="group/project-name")

# List user's projects
list_projects(owned=true, with_issues_enabled=true)
```

#### File Operations

```bash
# Read file contents
get_file_contents(
  project_id="123",
  file_path="src/main.py",
  ref="main"
)

# Create/update a single file
create_or_update_file(
  project_id="123",
  file_path="README.md",
  content="# My Project\n\nDescription here",
  commit_message="Update README",
  branch="main"
)

# Batch file operations
push_files(
  project_id="123",
  commit_message="Add new features",
  branch="feature/new-api",
  files=[
    {"file_path": "api/v1.py", "content": "..."},
    {"file_path": "tests/test_v1.py", "content": "..."}
  ]
)
```

### Issue Management Workflow

#### Create and Track Issues

```bash
# Create a bug report
create_issue(
  project_id="123",
  title="Bug: Login fails with LDAP authentication",
  description="When using LDAP login, users get authentication error...",
  labels=["bug", "authentication", "priority::high"],
  assignee_ids=[456],
  milestone_id=10
)

# Update issue status
update_issue(
  project_id="123",
  issue_iid=42,
  state_event="close",
  labels=["bug", "resolved"]
)

# Link related issues
create_issue_link(
  project_id="123",
  issue_iid=42,
  target_project_id="124",
  target_issue_iid=15,
  link_type="relates_to"
)
```

#### Issue Discussions

```bash
# List issue conversations
list_issue_discussions(
  project_id="123",
  issue_iid=42
)

# Add comment to issue
create_issue_note(
  project_id="123",
  issue_iid=42,
  discussion_id="abc123",
  body="I can reproduce this issue in version 2.1.0"
)
```

### Merge Request Workflow

#### Create and Manage MRs

```bash
# Create merge request
create_merge_request(
  project_id="123",
  source_branch="feature/new-api",
  target_branch="main",
  title="Add new API endpoints",
  description="This MR adds REST API endpoints for user management",
  assignee_ids=[456],
  reviewer_ids=[789, 101],
  labels=["api", "enhancement"]
)

# Get MR details and diffs
get_merge_request(
  project_id="123",
  merge_request_iid=15
)

get_merge_request_diffs(
  project_id="123",
  merge_request_iid=15,
  view="inline"
)
```

#### Code Review Process

```bash
# Start review discussion
create_merge_request_thread(
  project_id="123",
  merge_request_iid=15,
  body="Consider adding input validation here",
  position={
    "new_path": "api/users.py",
    "new_line": 45,
    "old_path": "api/users.py",
    "old_line": 42
  }
)

# Respond to review
create_merge_request_note(
  project_id="123",
  merge_request_iid=15,
  discussion_id="review_thread_id",
  body="Good point! I'll add validation in the next commit."
)
```

## Advanced Workflows

### CI/CD Pipeline Management

#### Monitor Pipeline Status

```bash
# List recent pipelines
list_pipelines(
  project_id="123",
  status="running",
  ref="main",
  per_page=5
)

# Get detailed pipeline info
get_pipeline(
  project_id="123",
  pipeline_id=567
)

# Check individual job status
list_pipeline_jobs(
  project_id="123",
  pipeline_id=567
)

# Get job output for debugging
get_pipeline_job_output(
  project_id="123",
  job_id=890,
  limit=100
)
```

#### Pipeline Operations

```bash
# Trigger new pipeline
create_pipeline(
  project_id="123",
  ref="main",
  variables=[
    {"key": "DEPLOY_ENV", "value": "staging"},
    {"key": "RUN_TESTS", "value": "true"}
  ]
)

# Retry failed pipeline
retry_pipeline(
  project_id="123",
  pipeline_id=567
)

# Cancel running pipeline
cancel_pipeline(
  project_id="123",
  pipeline_id=568
)
```

### Project Milestone Management

#### Track Project Progress

```bash
# List project milestones
list_milestones(
  project_id="123",
  state="active",
  sort="due_date"
)

# Create release milestone
create_milestone(
  project_id="123",
  title="v2.0.0 Release",
  description="Major version release with breaking changes",
  due_date="2024-06-01",
  start_date="2024-03-01"
)

# Track milestone progress
get_milestone_issues(
  project_id="123",
  milestone_id=10
)

get_milestone_merge_requests(
  project_id="123",
  milestone_id=10
)
```

### Wiki Documentation

#### Manage Project Documentation

```bash
# List all wiki pages
list_wiki_pages(
  project_id="123",
  with_content=false
)

# Create documentation page
create_wiki_page(
  project_id="123",
  title="API Documentation",
  content="# API Reference\n\n## Authentication\n...",
  format="markdown"
)

# Update existing wiki page
update_wiki_page(
  project_id="123",
  slug="api-documentation",
  title="API Documentation v2",
  content="# Updated API Reference\n\n## New Features\n...",
  format="markdown"
)
```

## Integration Patterns

### Automated Issue Triage

Use the GitLab MCP server to automatically process incoming issues:

1. **Monitor new issues** with `list_issues(state="opened", sort="created_desc")`
2. **Analyze content** and apply appropriate labels
3. **Assign issues** based on component or expertise area
4. **Create linked issues** for complex problems requiring breakdown

### Release Management

Automate release workflows:

1. **Create milestone** for release version
2. **Track progress** with milestone issue/MR queries
3. **Generate release notes** from closed issues and merged MRs
4. **Trigger deployment pipeline** when milestone is complete

### Code Quality Monitoring

Monitor code quality through MRs:

1. **List open MRs** requiring review
2. **Check pipeline status** for quality gates
3. **Review diff complexity** and suggest breaking down large changes
4. **Track review completion** and approval status

## Performance Optimization

### Efficient Pagination

For large datasets, use pagination effectively:

```bash
# Process issues in batches
for page in range(1, 10):
    issues = list_issues(
        project_id="123",
        page=page,
        per_page=50,
        state="opened"
    )
    if not issues:
        break
    # Process batch
```

### Selective Feature Activation

Enable only needed features to reduce tool discovery time:

```bash
# Minimal feature set for CI monitoring
USE_GITLAB_WIKI=false
USE_MILESTONE=false  
USE_PIPELINE=true
GITLAB_READ_ONLY_MODE=true
```

### Caching Project Information

Cache frequently accessed project metadata:

```bash
# Cache project details
project_info = get_project(project_id="123")
default_branch = project_info["default_branch"]

# Use cached info for subsequent operations
get_file_contents(
    project_id="123",
    file_path="README.md",
    ref=default_branch
)
```

### Filtering Large Responses

Use specific filters to reduce response size:

```bash
# Filter pipelines by status
list_pipelines(
    project_id="123",
    status="failed",
    ref="main",
    per_page=10
)

# Get only essential MR information
list_merge_requests(
    project_id="123",
    state="opened",
    view="simple"
)
```

## Error Handling Patterns

### Graceful Degradation

Handle API limits and network issues:

```python
try:
    issues = list_issues(project_id="123")
except RateLimitError:
    # Implement backoff strategy
    time.sleep(60)
    issues = list_issues(project_id="123", per_page=10)
except NetworkError:
    # Fall back to cached data or reduced functionality
    issues = get_cached_issues()
```

### Validation Before Operations

Verify resources exist before modification:

```python
# Check if MR exists before updating
try:
    mr = get_merge_request(project_id="123", merge_request_iid=15)
    if mr["state"] == "merged":
        print("Cannot update merged MR")
    else:
        update_merge_request(...)
except NotFoundError:
    print("Merge request not found")
```

This usage guide provides practical patterns for leveraging the GitLab MCP server effectively across different scenarios and use cases.
