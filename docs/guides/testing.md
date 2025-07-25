# Testing Templates

Guidelines for testing MCP server templates.

## Test Structure

Templates should include comprehensive tests:

```
templates/my-template/tests/
├── test_units.py           # Unit tests
├── test_integration.py     # Integration tests
└── conftest.py            # Test configuration
```

## Running Tests

```bash
# Run all tests for a template
cd templates/my-template
python -m pytest tests/

# Run specific test types
python -m pytest tests/ -m "not integration"  # Unit tests only
python -m pytest tests/ -m integration        # Integration tests only

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Guidelines

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Aim for 80%+ code coverage
- Fast execution (< 1s per test)

### Integration Tests
- Test complete workflows
- Use real dependencies when possible
- Test server startup and shutdown
- Validate MCP protocol compliance

## Example Test

```python
import pytest
from src.server import MyMCPServer

class TestMyMCPServer:
    def test_server_initialization(self):
        server = MyMCPServer()
        assert server is not None

    def test_handle_request(self):
        server = MyMCPServer()
        response = server.handle_request({"method": "ping"})
        assert response["result"] == "pong"
```

## Continuous Integration

All templates are automatically tested in CI:
- Unit tests must pass
- Integration tests should pass
- Code coverage must be ≥80%
- Docker build must succeed
