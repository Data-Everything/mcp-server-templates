# Zendesk MCP Server

A comprehensive Zendesk integration MCP server that provides full ticket management, user operations, knowledge base access, and analytics capabilities using the Model Context Protocol (MCP) and FastMCP framework.

## Features

### 🎫 Ticket Management
- **Create tickets** with custom priority, type, and tags
- **Retrieve ticket details** with comments and metadata
- **Update ticket properties** (status, priority, assignee)
- **Search tickets** with advanced filters and criteria
- **Add comments** (public or internal) to existing tickets

### 👥 User Management
- **Create new users** with roles and organization assignment
- **Retrieve user information** by ID or email
- **Search users** by various criteria
- **Manage user roles** (end-user, agent, admin)

### 📚 Knowledge Base
- **Search articles** in knowledge base
- **Retrieve article content** with full text and metadata
- **Filter by language locale** and sections
- **Access help center content** programmatically

### 📊 Analytics & Reporting
- **Ticket metrics** with status, priority, and type breakdowns
- **Resolution statistics** and performance tracking
- **Date range filtering** for time-based analysis
- **Customizable grouping** by various fields

### 🏢 Organization Management
- **List organizations** with search capabilities
- **Organization-based filtering** for users and tickets

### ⚡ Performance Features
- **Rate limiting** to respect Zendesk API limits
- **Intelligent caching** for frequently accessed data
- **Async/await support** for high-performance operations
- **Configurable timeouts** and retry logic

## Configuration

### Required Settings

```json
{
  "zendesk_subdomain": "your-company",
  "zendesk_email": "support@your-company.com"
}
```

### Authentication Options

**API Token Authentication (Recommended):**
```bash
export ZENDESK_API_TOKEN="your_api_token_here"
```

**OAuth Token Authentication:**
```bash
export ZENDESK_OAUTH_TOKEN="your_oauth_token_here"
```

### Optional Configuration

```bash
# Performance Settings
export ZENDESK_RATE_LIMIT=200              # Requests per minute (default: 200)
export ZENDESK_TIMEOUT=30                  # Request timeout in seconds (default: 30)

# Caching Settings
export ZENDESK_ENABLE_CACHE=true           # Enable caching (default: true)
export ZENDESK_CACHE_TTL=300              # Cache TTL in seconds (default: 300)

# Default Ticket Settings
export ZENDESK_DEFAULT_PRIORITY=normal     # Default priority (default: normal)
export ZENDESK_DEFAULT_TYPE=question       # Default type (default: question)

# Logging
export MCP_LOG_LEVEL=info                  # Log level (default: info)
```

## Quick Start

### Using the Template System

```bash
# Deploy with basic configuration
python -m mcp_template deploy zendesk \
  --config zendesk_subdomain=mycompany \
  --config zendesk_email=support@mycompany.com

# Deploy with API token
python -m mcp_template deploy zendesk \
  --config zendesk_subdomain=mycompany \
  --config zendesk_email=support@mycompany.com \
  --config zendesk_api_token=your_token_here

# Deploy with custom settings
python -m mcp_template deploy zendesk \
  --config zendesk_subdomain=mycompany \
  --config zendesk_email=support@mycompany.com \
  --config rate_limit_requests=150 \
  --config enable_cache=false
```

### Using Docker

```bash
# Build the image
docker build -t zendesk-mcp .

# Run with environment variables
docker run -d \
  -p 7072:7072 \
  -e ZENDESK_SUBDOMAIN=mycompany \
  -e ZENDESK_EMAIL=support@mycompany.com \
  -e ZENDESK_API_TOKEN=your_token_here \
  zendesk-mcp

# Run with custom transport
docker run -d \
  -p 7072:7072 \
  -e MCP_TRANSPORT=http \
  -e MCP_PORT=7072 \
  -e ZENDESK_SUBDOMAIN=mycompany \
  -e ZENDESK_EMAIL=support@mycompany.com \
  -e ZENDESK_API_TOKEN=your_token_here \
  zendesk-mcp
```

### Direct Python Usage

```python
import asyncio
from zendesk import ZendeskMCPServer

async def main():
    config = {
        "zendesk_subdomain": "mycompany",
        "zendesk_email": "support@mycompany.com",
        "zendesk_api_token": "your_token_here"
    }
    
    server = ZendeskMCPServer(config_dict=config)
    
    # Use as async context manager
    async with server:
        # Create a ticket
        ticket = await server.create_ticket(
            subject="Test Ticket",
            description="This is a test ticket",
            priority="normal"
        )
        
        print(f"Created ticket #{ticket['ticket_id']}")
        
        # Search for recent tickets
        results = await server.search_tickets(
            status="open",
            limit=10
        )
        
        print(f"Found {results['ticket_count']} open tickets")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Tools

### Ticket Operations

#### `create_ticket`
Create a new support ticket.

```python
await server.create_ticket(
    subject="Login Issue",
    description="User cannot log into the application",
    requester_email="user@example.com",
    priority="high",
    type="incident",
    tags=["login", "urgent"]
)
```

#### `get_ticket`
Retrieve ticket details with optional comments.

```python
await server.get_ticket(
    ticket_id=123,
    include_comments=True
)
```

#### `update_ticket`
Update ticket properties.

```python
await server.update_ticket(
    ticket_id=123,
    status="solved",
    priority="normal",
    assignee_id=456
)
```

#### `search_tickets`
Search tickets with filters.

```python
await server.search_tickets(
    query="login error",
    status="open",
    priority="high",
    created_after="2024-01-01T00:00:00Z",
    limit=25
)
```

#### `add_ticket_comment`
Add comment to existing ticket.

```python
await server.add_ticket_comment(
    ticket_id=123,
    body="Thank you for contacting support. We're investigating this issue.",
    public=True
)
```

### User Operations

#### `create_user`
Create a new user.

```python
await server.create_user(
    name="John Doe",
    email="john.doe@example.com",
    role="end-user",
    organization_id=101
)
```

#### `get_user`
Retrieve user information.

```python
# By user ID
await server.get_user(user_id=456)

# By email
await server.get_user(email="john.doe@example.com")
```

#### `search_users`
Search for users.

```python
await server.search_users(
    query="john",
    role="agent",
    organization_id=101
)
```

### Knowledge Base

#### `search_articles`
Search knowledge base articles.

```python
await server.search_articles(
    query="password reset",
    locale="en-us",
    section_id=201
)
```

#### `get_article`
Retrieve specific article.

```python
await server.get_article(
    article_id=789,
    locale="en-us"
)
```

### Analytics

#### `get_ticket_metrics`
Generate ticket analytics.

```python
await server.get_ticket_metrics(
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-01-31T23:59:59Z",
    group_by="day"
)
```

### Organizations

#### `list_organizations`
List organizations.

```python
await server.list_organizations(
    query="tech company"
)
```

## Transport Support

The server supports multiple MCP transports:

- **HTTP** (default): RESTful HTTP interface
- **Stdio**: Standard input/output for direct integration
- **SSE**: Server-Sent Events for real-time updates
- **Streamable HTTP**: HTTP with streaming support

Set the transport using environment variables:

```bash
export MCP_TRANSPORT=http        # Default
export MCP_TRANSPORT=stdio       # For direct integration
export MCP_TRANSPORT=sse         # For real-time updates
export MCP_TRANSPORT=streamable-http  # For streaming
```

## Error Handling

The server provides comprehensive error handling:

- **Authentication errors**: Clear messages for invalid credentials
- **Rate limiting**: Automatic retry with exponential backoff
- **Network errors**: Timeout and connection error handling
- **Validation errors**: Input validation with helpful messages
- **API errors**: Detailed Zendesk API error reporting

## Security Features

- **Secure credential handling**: Sensitive data masked in logs
- **Input validation**: All parameters validated before API calls
- **Rate limiting**: Prevents API abuse and quota exhaustion
- **Timeout protection**: Prevents hanging requests
- **Error sanitization**: Prevents credential leakage in error messages

## Performance Optimization

- **Intelligent caching**: Configurable TTL for frequently accessed data
- **Rate limiting**: Respects Zendesk API limits automatically
- **Async operations**: Non-blocking operations for high throughput
- **Connection pooling**: Efficient HTTP connection management
- **Retry logic**: Automatic retry for transient failures

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_config.py
pytest tests/test_zendesk_server.py
pytest tests/test_integration.py

# Run with coverage
pytest --cov=. tests/
```

## Development

### Local Development Setup

```bash
# Clone and setup
git clone <repository>
cd zendesk-mcp-server

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ZENDESK_SUBDOMAIN=your-test-subdomain
export ZENDESK_EMAIL=your-test-email
export ZENDESK_API_TOKEN=your-test-token

# Run the server
python server.py
```

### Adding New Features

1. **Add tool method** to `ZendeskMCPServer` class
2. **Register tool** in `register_tools()` method
3. **Update template.json** with tool definition
4. **Add tests** for the new functionality
5. **Update documentation**

### Configuration Customization

The server supports extensive customization through the configuration system:

```python
# Custom configuration
config = {
    "zendesk_subdomain": "mycompany",
    "zendesk_email": "support@mycompany.com",
    "zendesk_api_token": "token",
    "rate_limit_requests": 100,  # Custom rate limit
    "enable_cache": False,       # Disable caching
    "default_ticket_priority": "high"  # Change defaults
}

server = ZendeskMCPServer(config_dict=config)
```

## Troubleshooting

### Common Issues

**Authentication Failures:**
```bash
# Verify credentials
curl -u user@example.com/token:api_token https://subdomain.zendesk.com/api/v2/users/me.json
```

**Rate Limiting:**
- Reduce `rate_limit_requests` setting
- Increase `timeout_seconds` for slower responses
- Enable caching to reduce API calls

**Connection Issues:**
- Check network connectivity to Zendesk
- Verify subdomain is correct
- Check firewall settings

**Performance Issues:**
- Enable caching for frequently accessed data
- Increase rate limits if your plan supports it
- Use connection pooling for high throughput

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review the test files for usage examples
- Open an issue with detailed error information
- Include configuration (with sensitive data masked)
