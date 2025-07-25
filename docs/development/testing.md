# Testing

Testing guidelines and practices for MCP Templates development.

## Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared test configuration
├── test_cli.py              # CLI testing
├── test_discovery.py        # Template discovery tests
├── test_deployment.py       # Deployment engine tests
├── test_template_creation.py # Template creation tests
├── utils/
│   ├── __init__.py
│   └── mcp_test_utils.py    # Test utilities
└── fixtures/                # Test data
    ├── templates/           # Sample templates
    └── configs/             # Test configurations
```

## Test Categories

### Unit Tests
Test individual components in isolation:

```python
def test_template_discovery():
    discovery = TemplateDiscovery()
    templates = discovery.discover_templates()
    assert len(templates) > 0

def test_template_validation():
    validator = TemplateValidator()
    result = validator.validate_template_json(sample_config)
    assert result.is_valid
```

### Integration Tests
Test component interactions:

```python
@pytest.mark.integration
def test_template_deployment_lifecycle():
    # Deploy template
    deployment = deploy_template("demo")
    assert deployment.status == "running"

    # Check health
    response = requests.get(f"http://localhost:{deployment.port}/health")
    assert response.status_code == 200

    # Stop deployment
    stop_deployment(deployment.id)
    assert deployment.status == "stopped"
```

### Template Tests
Each template includes its own test suite:

```python
# templates/demo/tests/test_demo_units.py
class TestDemoServer:
    def test_server_initialization(self):
        server = DemoServer()
        assert server is not None

    def test_mcp_protocol_compliance(self):
        server = DemoServer()
        response = server.handle_mcp_request({"method": "initialize"})
        assert "result" in response
```

## Test Configuration

### conftest.py
Shared test configuration and fixtures:

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_template_dir(tmp_path):
    """Create a temporary template directory."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir

@pytest.fixture
def sample_template():
    """Provide a sample template for testing."""
    return {
        "id": "test-template",
        "name": "Test Template",
        "description": "A template for testing",
        "version": "1.0.0"
    }
```

### Test Markers
Use pytest markers to organize tests:

```python
# Mark slow tests
@pytest.mark.slow
def test_full_deployment_cycle():
    pass

# Mark integration tests
@pytest.mark.integration
def test_docker_deployment():
    pass

# Mark template-specific tests
@pytest.mark.template("demo")
def test_demo_specific_functionality():
    pass
```

## Running Tests

### Local Testing
```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_discovery.py

# Run with coverage
python -m pytest --cov=mcp_template --cov-report=html

# Run only unit tests
python -m pytest -m "not integration and not slow"

# Run integration tests
python -m pytest -m integration

# Run tests for specific template
python -m pytest -m "template('demo')"
```

### Continuous Integration
Tests run automatically in GitHub Actions:

```yaml
- name: Run unit tests
  run: python -m pytest tests/ -m "not integration" --cov=mcp_template

- name: Run integration tests
  run: python -m pytest tests/ -m integration
```

## Test Utilities

### Mock Services
Utilities for mocking external services:

```python
from tests.utils.mcp_test_utils import MockMCPServer

def test_mcp_interaction():
    with MockMCPServer() as server:
        response = server.call_method("test_method")
        assert response["status"] == "success"
```

### Template Fixtures
Helper functions for creating test templates:

```python
from tests.utils.mcp_test_utils import create_test_template

def test_template_creation():
    template_path = create_test_template("test-template", {
        "id": "test",
        "name": "Test Template"
    })
    assert template_path.exists()
```

## Performance Testing

### Load Testing
Test template performance under load:

```python
@pytest.mark.performance
def test_template_load():
    deployment = deploy_template("demo")

    # Simulate concurrent requests
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(make_request, deployment.url)
            for _ in range(100)
        ]
        results = [f.result() for f in futures]

    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in results)
```

### Memory Testing
Monitor memory usage during tests:

```python
import psutil
import os

def test_memory_usage():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Perform memory-intensive operation
    large_deployment = deploy_multiple_templates(10)

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Assert memory usage is reasonable
    assert memory_increase < 100 * 1024 * 1024  # 100MB limit
```

## Test Data Management

### Fixtures Directory
Organize test data:

```
tests/fixtures/
├── templates/
│   ├── valid-template/      # Valid template for testing
│   └── invalid-template/    # Invalid template for error testing
├── configs/
│   ├── valid-config.json
│   └── invalid-config.json
└── responses/
    └── mcp-responses.json   # Sample MCP responses
```

### Test Database
For integration tests requiring persistence:

```python
@pytest.fixture(scope="session")
def test_database():
    # Set up test database
    db = create_test_db()
    yield db
    # Clean up
    db.drop_all_tables()
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Fast Unit Tests**: Keep unit tests under 1 second
3. **Comprehensive Coverage**: Aim for 80%+ code coverage
4. **Clear Test Names**: Use descriptive test function names
5. **Setup/Teardown**: Clean up resources after tests
6. **Mock External Dependencies**: Don't rely on external services
7. **Test Edge Cases**: Include error conditions and boundary cases
8. **Document Complex Tests**: Add comments for complex test logic
