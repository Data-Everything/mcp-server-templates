# Template Testing Guide

Comprehensive guide for testing MCP server templates at all levels.

## 🎯 Testing Philosophy

The MCP Server Templates testing framework provides multi-level validation:

1. **Quick Tests** (< 5 seconds): Basic validation and syntax checks
2. **Unit Tests** (< 30 seconds): Individual component testing
3. **Integration Tests** (< 2 minutes): Full template deployment and interaction
4. **Template-Specific Tests**: Custom validation for each template

## 🚀 Getting Started

### Running Tests Locally

```bash
# Run all tests for all templates
make test

# Run quick tests only (great for development)
make test-quick

# Run tests for specific template
make test TEMPLATE=file-server

# Run with verbose output
make test VERBOSE=1

# Run integration tests only
make test-integration

# Run with coverage report
make test-coverage
```

### Test Categories

#### Quick Tests
- **Purpose**: Fast feedback during development
- **Runtime**: < 5 seconds per template
- **Validates**:
  - `template.json` structure and schema
  - Required files presence
  - Documentation format
  - Basic configuration validity

#### Unit Tests
- **Purpose**: Component-level validation
- **Runtime**: < 30 seconds per template
- **Validates**:
  - Configuration parsing logic
  - Tool implementations
  - Error handling
  - Edge cases

#### Integration Tests
- **Purpose**: End-to-end template functionality
- **Runtime**: < 2 minutes per template
- **Validates**:
  - Docker build and container startup
  - MCP server protocol compliance
  - Tool execution and responses
  - Configuration application

## Testing Architecture

Our testing strategy follows a multi-tiered approach with different test categories optimized for speed and coverage:

### Test Structure

```
tests/
├── __init__.py
├── test_runner.py              # Main test orchestrator
├── test_all_templates.py       # Template discovery validation
├── test_config_strategy.py     # Configuration system tests
├── test_configuration.py       # Config parsing tests
├── test_deployment_integration.py # Full deployment tests
├── test_deployment_units.py    # Unit tests for deployment
├── test_local_deployment.py    # Local deployment tests
├── test_utils.py               # Utility function tests
└── test_config_files/          # Test configuration data
```

## Running Tests

### Using Make Commands

```bash
# Quick validation - fastest tests
make test-quick

# Unit tests only (no Docker required)
make test-unit

# Integration tests (requires Docker/containers)
make test-integration

# All tests
make test-all

# Test specific template
make test-template TEMPLATE=file-server

# Test all templates
make test-templates
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_deployment_units.py -m unit

# Run with coverage
pytest tests/test_deployment_units.py -m unit --cov=mcp_template --cov-report=html

# Run integration tests
pytest tests/test_deployment_integration.py -m integration
```

### Using the Test Runner

The `test_runner.py` provides a unified interface:

```bash
# Quick tests
python tests/test_runner.py quick

# Unit tests
python tests/test_runner.py unit

# Integration tests
python tests/test_runner.py integration

# All tests
python tests/test_runner.py all
```

## GitHub Actions CI/CD

Our CI pipeline runs multiple test stages:

### 1. Quick Tests
- **Trigger**: Every commit
- **Duration**: ~2 minutes
- **Python versions**: 3.10, 3.11, 3.12
- **Purpose**: Fast feedback on basic functionality

### 2. Unit Tests
- **Trigger**: Every commit
- **Duration**: ~5 minutes
- **Python versions**: 3.10, 3.11, 3.12
- **Coverage**: Generates coverage reports
- **Purpose**: Validate individual components

### 3. Integration Tests
- **Trigger**: Pull requests and main branch
- **Duration**: ~15 minutes
- **Python versions**: 3.10, 3.11 (limited for speed)
- **Container runtime**: Uses nerdctl/containerd
- **Purpose**: Test full deployment workflows

### 4. Template Validation
- **Trigger**: Every commit
- **Duration**: ~3 minutes
- **Purpose**: Validate all templates using TemplateDiscovery

### 5. Security Scanning
- **Trigger**: Every commit
- **Tool**: Bandit security linter
- **Purpose**: Identify security vulnerabilities

### 6. Code Quality
- **Trigger**: Every commit
- **Tools**: black, isort, flake8
- **Purpose**: Maintain code standards

### 7. Pre-release Tests
- **Trigger**: Main branch only
- **Duration**: ~20 minutes
- **Purpose**: Comprehensive testing before PyPI release

## Testing Methodology

### Quick Tests
Fast validation that templates can be discovered and basic CLI works:

```python
def test_template_discovery():
    """Validate templates can be discovered."""
    discovery = TemplateDiscovery()
    templates = discovery.discover_templates()
    assert len(templates) > 0
    assert 'file-server' in templates
```

### Unit Tests
Test individual components without external dependencies:

```python
@pytest.mark.unit
def test_config_conversion():
    """Test configuration type conversion."""
    deployer = MCPDeployer()
    config = {"read_only_mode": "true", "max_file_size": "50"}
    result = deployer._convert_config_values(config, template)
    assert result["MCP_READ_ONLY"] == "true"
```

### Integration Tests
Test full deployment workflows with mock or real containers:

```python
@pytest.mark.integration
def test_template_deployment():
    """Test complete template deployment."""
    manager = DeploymentManager(backend_type='mock')
    result = manager.deploy_template(
        template_id='file-server',
        configuration={'MCP_READ_ONLY': 'true'}
    )
    assert result['status'] == 'deployed'
```

### Template-Specific Tests
Each template has its own test suite:

```
templates/file-server/tests/
├── test_file_server_units.py       # Unit tests
├── test_config_validation.py       # Config tests
└── test_integration.py             # Integration tests
```

## Mock Backend Testing

For environments without Docker, we use a mock deployment backend:

```python
class MockDeploymentService:
    def deploy_template(self, template_id, config, template_data):
        return {
            'deployment_name': f'mock-{template_id}-{uuid.uuid4().hex[:8]}',
            'status': 'deployed',
            'container_id': f'mock-container-{uuid.uuid4().hex[:8]}'
        }
```

## Container Runtime Testing

In CI environments, we test with different container runtimes:

- **Local development**: Docker
- **GitHub Actions**: containerd + nerdctl
- **Mock testing**: No containers (for speed)

## Test Data and Fixtures

Test configurations are stored in `tests/test_config_files/`:

```
test_config_files/
├── __init__.py
├── basic_config.json
├── advanced_config.yaml
├── invalid_config.json
└── nested_config.json
```

## Writing New Tests

### Template Tests

When creating a new template, add tests:

```python
# templates/my-template/tests/test_my_template.py
import pytest
from mcp_template import TemplateDiscovery

def test_template_discovery():
    """Test template can be discovered."""
    discovery = TemplateDiscovery()
    templates = discovery.discover_templates()
    assert 'my-template' in templates

@pytest.mark.unit
def test_config_validation():
    """Test template configuration validation."""
    # Test configuration logic
    pass

@pytest.mark.integration
def test_deployment():
    """Test template deployment."""
    # Test deployment workflow
    pass
```

### Core Tests

For core functionality changes:

```python
# tests/test_new_feature.py
import pytest
from mcp_template import MCPDeployer

@pytest.mark.unit
def test_new_feature():
    """Test new feature functionality."""
    deployer = MCPDeployer()
    result = deployer.new_feature()
    assert result is not None
```

## Performance Testing

Monitor test execution times:

```bash
# Run with timing
pytest tests/ --durations=10

# Profile specific tests
pytest tests/test_deployment_units.py --profile --profile-svg
```

## Debugging Tests

```bash
# Run with verbose output
pytest tests/ -v

# Drop into debugger on failure
pytest tests/ --pdb

# Run specific test with debugging
pytest tests/test_deployment_units.py::test_config_conversion -v -s
```

## Test Coverage

Generate coverage reports:

```bash
# HTML coverage report
make coverage

# View coverage
open htmlcov/index.html
```

Target coverage metrics:
- **Unit tests**: >90%
- **Integration tests**: >80%
- **Overall**: >85%

## Continuous Integration

### Local CI Simulation

```bash
# Simulate quick CI
make ci-quick

# Simulate full CI pipeline
make ci-full
```

### CI Environment Variables

Tests use environment variables for configuration:

- `CI=true`: Indicates CI environment
- `GITHUB_ACTIONS=true`: GitHub Actions specific
- `MOCK_CONTAINERS=true`: Use mock backend

## Best Practices

1. **Test Naming**: Use descriptive names (`test_config_validation_with_nested_objects`)
2. **Test Isolation**: Each test should be independent
3. **Mock External Services**: Use mocks for external dependencies
4. **Fast Feedback**: Keep unit tests under 1 second each
5. **Clear Assertions**: Use specific assertions with helpful messages
6. **Test Data**: Use fixtures for reusable test data
7. **Error Testing**: Test both success and failure cases

## Troubleshooting

### Common Issues

**Docker not available in CI:**
```python
# Use mock backend
if os.getenv('CI') and not docker_available():
    pytest.skip("Docker not available in CI")
```

**Tests timeout:**
```python
# Add timeout to slow tests
@pytest.mark.timeout(300)  # 5 minutes
def test_slow_deployment():
    pass
```

**Template discovery fails:**
```python
# Check template directory exists
def test_template_exists():
    template_dir = Path("templates/my-template")
    assert template_dir.exists()
    assert (template_dir / "template.json").exists()
```
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
