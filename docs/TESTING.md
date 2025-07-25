# MCP Server Templates - Test Organization

## Overview

The test suite has been reorganized for CI/CD pipeline integration with the following structure:

```
tests/
├── __init__.py                     # Test package initialization
├── test_deployment_units.py       # Unit tests (fast, no Docker)
├── test_deployment_integration.py # Integration tests (require Docker)
├── test_runner.py                 # CI/CD test runner
├── test_all_templates.py          # Existing template tests
├── test_config_strategy.py        # Existing config tests
├── test_local_deployment.py       # Existing local tests
└── test_utils.py                  # Existing utilities
```

## Test Categories

### Unit Tests (`test_deployment_units.py`)
- **Purpose**: Fast tests with no external dependencies
- **Marker**: `@pytest.mark.unit`
- **Coverage**: 
  - Template discovery logic
  - Configuration generation
  - Deployment manager initialization
  - Docker service mocking
- **Runtime**: < 1 second
- **CI Stage**: Quick validation on every commit

### Integration Tests (`test_deployment_integration.py`)
- **Purpose**: End-to-end tests requiring Docker
- **Marker**: `@pytest.mark.integration` and `@pytest.mark.docker`
- **Coverage**:
  - Actual template deployment
  - Container lifecycle management
  - CLI interface testing
  - Cleanup functionality
- **Runtime**: 30-60 seconds
- **CI Stage**: Full validation before merge

## Running Tests

### Local Development

```bash
# Using Make (recommended)
make test-quick      # Quick validation
make test-unit       # Unit tests only
make test-integration # Integration tests
make test-all        # All tests

# Direct pytest
source .venv/bin/activate
pytest tests/test_deployment_units.py -m unit -v
pytest tests/test_deployment_integration.py -m integration -v
```

### CI/CD Pipeline

```bash
# Using test runner
python tests/test_runner.py unit         # Unit tests
python tests/test_runner.py integration  # Integration tests
python tests/test_runner.py all          # All tests
python tests/test_runner.py quick        # Quick validation
```

## CI/CD Integration

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

The workflow includes multiple stages:

1. **Quick Tests** - Run on every commit
   - Python 3.9, 3.10, 3.11, 3.12
   - Template validation
   - Fast unit tests

2. **Unit Tests** - Comprehensive unit testing
   - All Python versions
   - Code coverage reporting
   - No Docker required

3. **Integration Tests** - Docker-based testing
   - Python 3.10, 3.11 (limited for speed)
   - Actual deployment testing
   - Container lifecycle validation

4. **Template Validation** - Ensure all templates are valid
   - Dynamic template discovery
   - Schema validation
   - Docker image availability

5. **Security & Quality** - Code quality checks
   - Bandit security scanning
   - Black formatting
   - Flake8 linting
   - MyPy type checking

### Test Configuration

#### `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Unit tests (fast, no Docker)
    integration: Integration tests (require Docker)
    docker: Tests requiring Docker
    slow: Slow-running tests
```

#### `requirements-dev.txt`
- `pytest>=7.0.0` - Testing framework
- `pytest-mock>=3.10.0` - Mocking utilities
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `bandit>=1.7.0` - Security scanning

## Test Strategy

### Pre-commit Validation
```bash
make dev-test  # Quick tests + linting
```

### CI Pipeline Stages
1. **Lint & Format Check** - Code quality validation
2. **Quick Tests** - Fast validation across Python versions
3. **Unit Tests** - Comprehensive unit testing with coverage
4. **Integration Tests** - Docker-based deployment testing
5. **Security Scan** - Bandit security analysis
6. **Pre-release** - Full validation before release

### Development Workflow
```bash
# Setup development environment
make dev-setup

# Run tests during development
make test-quick      # Fast feedback
make test-unit       # Comprehensive unit tests
make dev-test        # Pre-commit validation

# Full validation before PR
make ci-full         # Simulate full CI pipeline
```

## Benefits

1. **Fast Feedback**: Unit tests run in <1 second
2. **CI Efficiency**: Staged testing reduces resource usage
3. **Developer Experience**: Make commands for common tasks
4. **Quality Assurance**: Multiple validation layers
5. **Docker Safety**: Integration tests isolated to specific stages
6. **Coverage**: Both unit and integration test coverage
7. **Scalability**: Easy to add new test categories

## Test Execution Examples

### Successful Unit Test Run
```
🧪 Running unit tests...
=================== 19 passed in 0.14s ===================
✅ Unit tests passed!
```

### Integration Test with Docker
```
🐳 Running integration tests...
=================== 6 passed in 45.2s ===================
✅ Integration tests passed!
```

### CI Pipeline Simulation
```bash
make ci-full
# ⚡ Quick tests...
# 🧪 Unit tests...
# 🔍 Code linting...
# 🔬 Type checking...
# 🐳 Integration tests...
# 📦 Package building...
# ✅ Full CI pipeline completed!
```

This organized structure ensures reliable testing for package deployment in CI/CD pipelines while maintaining fast feedback cycles for developers.
