# GitLab MCP Server - Complete Tool Reference

## Overview

The GitLab MCP Server provides comprehensive access to GitLab's API through 66+ specialized tools. This enhanced implementation supports both GitLab.com and self-hosted GitLab instances with advanced features like multiple transport protocols, enterprise authentication, and modular tool activation.

## Why GitLab MCP Server?

### 🚀 Complete GitLab Integration
- **66+ Tools**: Comprehensive coverage of GitLab API functionality
- **Multi-Transport**: stdio, SSE, and Streamable HTTP support
- **Enterprise Ready**: Self-hosted GitLab support with proxy configuration
- **Security First**: Read-only mode and granular feature controls

### 🛡️ Enterprise Security Features
- **Token-based Authentication**: GitLab personal access tokens
- **Cookie Authentication**: Support for complex enterprise setups
- **Read-only Mode**: Restrict to safe operations in production
- **Proxy Support**: HTTP/HTTPS proxy configuration for corporate networks

### ⚡ Performance & Scalability
- **Modular Architecture**: Enable only needed tool categories
- **Multiple Transports**: Choose optimal communication method
- **Efficient Pagination**: Built-in pagination for large datasets
- **Smart Caching**: Reduce API calls with intelligent caching

### 🎯 Developer Experience
- **Comprehensive Documentation**: Detailed tool descriptions and examples
- **Type Safety**: Zod schema validation for all operations
- **Error Handling**: Graceful error handling with detailed messages
- **Debug Support**: Extensive logging and debugging capabilities

## Complete Tool Catalog

### Repository & Project Management (15 tools)

#### Core Repository Operations
1. **`search_repositories`** - Search for GitLab projects across the platform
   - Use case: Find projects by name, description, or programming language
   - Example: Search for "machine-learning" projects with Python

2. **`create_repository`** - Create new GitLab projects with full configuration
   - Use case: Initialize new projects with proper settings
   - Example: Create private project with issues and wiki enabled

3. **`fork_repository`** - Fork existing projects to your namespace
   - Use case: Contribute to open source or create project variants
   - Example: Fork upstream project for custom modifications

4. **`get_project`** - Retrieve detailed project information and metadata
   - Use case: Get project configuration, permissions, and statistics
   - Example: Check project visibility and access levels

5. **`list_projects`** - Browse projects with advanced filtering options
   - Use case: List user's projects, group projects, or starred projects
   - Example: Find all projects where user has maintainer access

#### File & Content Management
6. **`get_file_contents`** - Read file or directory contents from repositories
   - Use case: Retrieve source code, configuration files, or documentation
   - Example: Read package.json or requirements.txt for dependencies

7. **`create_or_update_file`** - Create new files or update existing ones
   - Use case: Modify source code, update documentation, or fix bugs
   - Example: Update README.md with new installation instructions

8. **`push_files`** - Perform batch file operations in a single commit
   - Use case: Create multiple related files or perform refactoring
   - Example: Add new feature with source code, tests, and documentation

9. **`get_repository_tree`** - Browse repository structure and file hierarchy
   - Use case: Navigate project structure or find specific files
   - Example: List all Python files in the src/ directory

#### Branch & Version Control
10. **`create_branch`** - Create new branches for feature development
    - Use case: Start new feature development or create release branches
    - Example: Create "feature/user-authentication" branch

11. **`get_branch_diffs`** - Compare changes between branches or commits
    - Use case: Review changes before merging or analyze feature impact
    - Example: Compare feature branch with main branch

#### Namespace Management
12. **`list_namespaces`** - List available namespaces (users and groups)
    - Use case: Find target namespace for project creation or forking
    - Example: List organization groups for project placement

13. **`get_namespace`** - Get detailed namespace information
    - Use case: Verify namespace permissions and configuration
    - Example: Check group membership and access levels

14. **`verify_namespace`** - Verify if a namespace path exists
    - Use case: Validate namespace before project operations
    - Example: Check if group name is available for new project

15. **`list_group_projects`** - List projects within a specific group
    - Use case: Browse organization projects or team repositories
    - Example: Find all projects in "data-science" group

### Issue Management (12 tools)

#### Core Issue Operations
16. **`list_issues`** - Browse issues with comprehensive filtering options
    - Use case: Find bugs, track feature requests, or monitor progress
    - Example: List all open high-priority bugs assigned to specific user

17. **`get_issue`** - Retrieve detailed issue information and metadata
    - Use case: Get full issue details including description and comments
    - Example: Fetch issue #123 with all related information

18. **`create_issue`** - Create new issues with full metadata support
    - Use case: Report bugs, request features, or create tasks
    - Example: Create bug report with labels, assignees, and milestone

19. **`update_issue`** - Modify existing issues including status changes
    - Use case: Update issue status, assignees, or priorities
    - Example: Close issue and update labels to "resolved"

20. **`delete_issue`** - Remove issues from projects (when permitted)
    - Use case: Clean up duplicate or invalid issues
    - Example: Delete spam or mistakenly created issues

#### Issue Relationships
21. **`list_issue_links`** - View relationships between issues
    - Use case: Track related issues or dependencies
    - Example: Find all issues blocked by current issue

22. **`get_issue_link`** - Get specific issue relationship details
    - Use case: Understand the nature of issue relationships
    - Example: Check if issue blocks or relates to another

23. **`create_issue_link`** - Create relationships between issues
    - Use case: Link related issues or define dependencies
    - Example: Mark issue as blocking another issue

24. **`delete_issue_link`** - Remove issue relationships
    - Use case: Clean up incorrect or outdated relationships
    - Example: Remove obsolete issue dependencies

#### Issue Discussions
25. **`list_issue_discussions`** - Browse issue conversations and comments
    - Use case: Follow issue progress and team discussions
    - Example: Read all comments on critical bug report

26. **`update_issue_note`** - Modify existing issue comments
    - Use case: Correct information or update status in comments
    - Example: Fix typo in bug reproduction steps

27. **`create_issue_note`** - Add new comments to issue discussions
    - Use case: Provide updates, ask questions, or share solutions
    - Example: Add comment with workaround solution

### Merge Request Operations (11 tools)

#### Core MR Management
28. **`list_merge_requests`** - Browse merge requests with filtering
    - Use case: Review pending changes or track feature development
    - Example: List all open MRs awaiting code review

29. **`get_merge_request`** - Get detailed merge request information
    - Use case: Review MR details before merging or reviewing
    - Example: Check MR status, conflicts, and approval state

30. **`create_merge_request`** - Create new merge requests for code review
    - Use case: Submit feature branches for review and integration
    - Example: Create MR for new API endpoint implementation

31. **`update_merge_request`** - Modify existing merge request properties
    - Use case: Update MR title, description, or target branch
    - Example: Change MR target from develop to main branch

#### Code Review Process
32. **`get_merge_request_diffs`** - View changes introduced by merge request
    - Use case: Review code changes before approval or merge
    - Example: See diff for specific file modifications

33. **`list_merge_request_diffs`** - Browse MR changes with pagination
    - Use case: Navigate through large changesets efficiently
    - Example: Review changes page by page for complex MRs

34. **`mr_discussions`** - List all discussions on merge request
    - Use case: Follow code review conversations and feedback
    - Example: See all review comments and their resolution status

35. **`create_merge_request_thread`** - Start new discussion on MR
    - Use case: Begin code review discussion on specific lines
    - Example: Comment on potential security vulnerability in code

36. **`update_merge_request_note`** - Modify existing MR comments
    - Use case: Clarify feedback or update review status
    - Example: Mark review comment as resolved

37. **`create_merge_request_note`** - Add comments to MR discussions
    - Use case: Respond to review feedback or ask questions
    - Example: Reply to reviewer's suggestion with implementation plan

38. **`create_note`** - Create general notes on issues or MRs
    - Use case: Add administrative notes or status updates
    - Example: Add note about external dependencies affecting MR

### CI/CD Pipeline Management (8 tools)

#### Pipeline Monitoring
39. **`list_pipelines`** - Browse CI/CD pipelines with status filtering
    - Use case: Monitor build status and deployment progress
    - Example: Find all failed pipelines for debugging

40. **`get_pipeline`** - Get detailed pipeline information and status
    - Use case: Investigate pipeline failures or check progress
    - Example: Get pipeline details including duration and stages

41. **`list_pipeline_jobs`** - List all jobs within a pipeline
    - Use case: Identify failed jobs or check job dependencies
    - Example: Find which test job failed in the pipeline

42. **`get_pipeline_job`** - Get specific job details and metadata
    - Use case: Debug job failures or check job configuration
    - Example: Get job details including artifacts and variables

43. **`get_pipeline_job_output`** - Retrieve job logs and output
    - Use case: Debug failing tests or build issues
    - Example: Read test failure logs with pagination support

#### Pipeline Operations
44. **`create_pipeline`** - Trigger new pipeline execution
    - Use case: Run CI/CD for specific branch or with variables
    - Example: Trigger deployment pipeline with environment variables

45. **`retry_pipeline`** - Retry failed or canceled pipelines
    - Use case: Re-run pipelines after fixing issues
    - Example: Retry pipeline after infrastructure problems

46. **`cancel_pipeline`** - Stop currently running pipelines
    - Use case: Cancel long-running or incorrect pipelines
    - Example: Stop deployment pipeline triggered by mistake

### Project Organization (8 tools)

#### Label Management
47. **`list_labels`** - Browse project labels for categorization
    - Use case: See available labels for issues and MRs
    - Example: List all priority and component labels

48. **`get_label`** - Get specific label details and usage
    - Use case: Check label color, description, and scope
    - Example: Get details for "bug" label configuration

49. **`create_label`** - Create new labels for project organization
    - Use case: Add new categories for better issue tracking
    - Example: Create "security" label with red color

50. **`update_label`** - Modify existing label properties
    - Use case: Change label colors or descriptions
    - Example: Update priority label colors for consistency

51. **`delete_label`** - Remove unused labels from project
    - Use case: Clean up obsolete or duplicate labels
    - Example: Remove old version-specific labels

#### Milestone Management (Optional Feature Set)
52. **`list_milestones`** - Browse project milestones and their status
    - Use case: Track release planning and project progress
    - Example: List all active milestones with due dates

53. **`get_milestone`** - Get detailed milestone information
    - Use case: Check milestone progress and associated items
    - Example: Get milestone details including completion percentage

54. **`create_milestone`** - Create new project milestones
    - Use case: Set up release planning and goal tracking
    - Example: Create "v2.0.0" milestone with Q2 deadline

55. **`edit_milestone`** - Modify existing milestone properties
    - Use case: Update milestone dates or descriptions
    - Example: Extend milestone due date after scope changes

56. **`delete_milestone`** - Remove completed or canceled milestones
    - Use case: Clean up outdated project planning
    - Example: Remove canceled feature milestone

57. **`get_milestone_issue`** - List issues associated with milestone
    - Use case: Track milestone progress and remaining work
    - Example: See all open issues blocking release milestone

58. **`get_milestone_merge_requests`** - List MRs for milestone
    - Use case: Review feature completion for releases
    - Example: Check all MRs targeting milestone delivery

59. **`promote_milestone`** - Promote milestone to next level
    - Use case: Move milestone between project and group scope
    - Example: Promote project milestone to group level

### Wiki Documentation (5 tools)

*Optional feature set - Enable with `USE_GITLAB_WIKI=true`*

60. **`list_wiki_pages`** - Browse project wiki pages
    - Use case: Navigate project documentation structure
    - Example: List all documentation pages with content overview

61. **`get_wiki_page`** - Read specific wiki page content
    - Use case: Retrieve documentation for specific topics
    - Example: Get API documentation page content

62. **`create_wiki_page`** - Create new documentation pages
    - Use case: Add new documentation or guides
    - Example: Create installation guide with markdown content

63. **`update_wiki_page`** - Modify existing wiki documentation
    - Use case: Update outdated documentation or fix errors
    - Example: Update API documentation for new version

64. **`delete_wiki_page`** - Remove wiki pages
    - Use case: Clean up obsolete or duplicate documentation
    - Example: Remove outdated installation instructions

### User & Commit Information (3 tools)

65. **`get_users`** - Retrieve GitLab user information by usernames
    - Use case: Get user details for mentions or assignments
    - Example: Look up team member profiles for project assignment

66. **`list_commits`** - Browse repository commit history with filtering
    - Use case: Track code changes and author contributions
    - Example: List commits by specific author in date range

67. **`get_commit`** - Get detailed commit information and statistics
    - Use case: Review specific commit changes and metadata
    - Example: Get commit details including file changes and stats

## Feature Configuration

### Transport Protocols

The GitLab MCP server supports multiple communication protocols:

#### stdio (Default)
- **Best for**: Most MCP clients and simple integrations
- **Pros**: Universal compatibility, simple setup
- **Cons**: Limited to single concurrent connection

#### Server-Sent Events (SSE)
- **Best for**: Web applications and real-time updates
- **Pros**: HTTP-based, supports multiple clients
- **Cons**: Requires running HTTP server

#### Streamable HTTP
- **Best for**: High-performance applications
- **Pros**: Efficient binary protocol, high throughput
- **Cons**: More complex setup, fewer client implementations

### Security Configuration

#### Read-Only Mode
Enable `GITLAB_READ_ONLY_MODE=true` to restrict to safe operations:
- All repository browsing tools
- Issue and MR viewing tools
- Pipeline monitoring tools
- Wiki reading tools
- User and commit information tools

#### Feature Toggles
Control tool availability for security and performance:
- `USE_GITLAB_WIKI=false` - Disable wiki tools (saves 5 tools)
- `USE_MILESTONE=false` - Disable milestone tools (saves 8 tools)
- `USE_PIPELINE=false` - Disable pipeline tools (saves 8 tools)

### Enterprise Features

#### Self-Hosted GitLab Support
- Custom API URLs for enterprise installations
- Certificate configuration for custom CAs
- Proxy support for corporate networks
- Cookie-based authentication for SSO environments

#### Proxy Configuration
- HTTP/HTTPS proxy support
- SOCKS proxy support
- Custom certificate authorities
- SSL/TLS configuration options

## Performance Considerations

### Tool Discovery Optimization
The dynamic tool discovery system adapts based on configuration:
- **Minimal Setup**: ~45 tools (read-only, no optional features)
- **Standard Setup**: ~58 tools (read-write, basic features)
- **Full Setup**: 66+ tools (all features enabled)

### API Rate Limiting
GitLab.com has API rate limits:
- **Authenticated requests**: 2,000 per minute
- **Unauthenticated requests**: 10 per minute
- **Enterprise GitLab**: Configurable limits

### Pagination Strategy
Most list operations support pagination:
- Default page size: 20 items
- Maximum page size: 100 items
- Use pagination for datasets > 100 items

## Integration Examples

### Development Workflow Automation
1. **Feature Development**: Create branch → Make changes → Create MR
2. **Code Review**: Get MR diffs → Add review comments → Track discussions
3. **CI/CD Monitoring**: Monitor pipeline → Check job outputs → Handle failures
4. **Release Management**: Create milestone → Track progress → Generate release notes

### Project Management Integration
1. **Issue Triage**: List new issues → Apply labels → Assign team members
2. **Sprint Planning**: Create milestone → Link issues → Track completion
3. **Documentation**: Create wiki pages → Update project README → Maintain guides
4. **Team Coordination**: Link related issues → Track dependencies → Monitor progress

### DevOps Operations
1. **Deployment Monitoring**: List pipelines → Check job status → Get failure logs
2. **Infrastructure as Code**: Update configuration files → Trigger deployments → Monitor results
3. **Security Scanning**: Monitor pipeline security jobs → Review vulnerabilities → Track fixes
4. **Compliance Reporting**: Generate reports from issues → Track milestone completion → Audit changes

## Best Practices

### Authentication & Security
1. **Use least-privilege tokens**: Only grant necessary scopes
2. **Enable read-only mode**: For monitoring and reporting use cases
3. **Regular token rotation**: Follow security best practices
4. **Audit tool usage**: Monitor which tools are actually needed

### Performance Optimization
1. **Enable only needed features**: Disable unused tool categories
2. **Use appropriate pagination**: Balance between API calls and memory usage
3. **Cache project metadata**: Reduce repetitive API calls
4. **Implement retry logic**: Handle rate limits gracefully

### Error Handling
1. **Validate inputs**: Check project IDs and permissions before operations
2. **Handle rate limits**: Implement exponential backoff
3. **Log operations**: Maintain audit trail for debugging
4. **Graceful degradation**: Fall back to cached data when possible

This comprehensive tool reference provides the foundation for leveraging GitLab's full capabilities through the MCP protocol, enabling powerful automation and integration scenarios across the entire software development lifecycle.
