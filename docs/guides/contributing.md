# Contributing

Help improve MCP Server Templates!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/mcp-server-templates.git`
3. Create a feature branch: `git checkout -b feature-name`
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
black mcp_template/ tests/
flake8 mcp_template/ tests/
```

## Contributing Guidelines

### Code Style
- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Write clear docstrings

### Testing
- Write tests for new features
- Maintain 80%+ code coverage
- Test both happy path and edge cases
- Update integration tests

### Documentation
- Update relevant documentation
- Add docstrings to new functions
- Update CLI help text
- Include usage examples

## Template Contributions

### New Templates
1. Create template using: `mcpt create your-template`
2. Implement MCP server in `src/server.py`
3. Add comprehensive tests
4. Write clear documentation
5. Ensure Docker build works

### Template Requirements
- Must implement MCP protocol
- Include Dockerfile
- Have 80%+ test coverage
- Include clear documentation
- Follow naming conventions

## Review Process

1. Automated tests must pass
2. Code review by maintainers
3. Documentation review
4. Integration testing
5. Merge to main branch

## Community

- Join discussions in GitHub Issues
- Ask questions in GitHub Discussions
- Follow our Code of Conduct
- Help others in the community
