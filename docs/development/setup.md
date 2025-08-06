# Development Setup

Set up your development environment for MCP Templates.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- Make (optional, for convenience commands)

## Clone Repository

```bash
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates
```

## Development Installation

### Option 1: Using Make (Recommended)

```bash
# Complete development setup
make dev-setup
```

This command will:
- Install all dependencies
- Install in development mode
- Set up the development environment

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
# OR manually:
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
make install-dev
# OR manually:
pip install -e .
```

## Verify Setup

```bash
# Check CLI works
mcp-template --version
mcp-template list

# Run quick tests
make test-quick

# Run code quality checks
make lint
```

## Development Commands

### Available Make Targets

Use `make help` to see all available commands:

```bash
make help
```

### Setup Commands

```bash
make install       # Install dependencies
make install-dev   # Install in development mode
make dev-setup     # Complete development setup
```

### Testing Commands

```bash
make test-quick        # Fast validation tests (< 30s)
make test-unit         # Unit tests (no Docker required)
make test-integration  # Integration tests (requires Docker)
make test-all         # Run all tests
make test             # Alias for test-all

# Template-specific testing
make test-template TEMPLATE=filesystem  # Test specific template
make test-templates   # Test all templates

# Test with coverage
make coverage        # Generate HTML coverage report
```

### Code Quality Commands

```bash
make lint           # Run code linting (flake8, bandit)
make format         # Format code (black, isort)
make type-check     # Run type checking (mypy)
```

### Development Workflow Commands

```bash
make dev-test       # Quick development tests (test-quick + lint)
make ci-quick       # Simulate CI quick tests
make ci-full        # Simulate full CI pipeline
```

### Template Management Commands

```bash
make list-templates     # List available templates
make validate-templates # Validate all templates
make deploy-test       # Deploy test template
make cleanup-test      # Clean up test deployments
```

### Documentation Commands

```bash
make docs          # Build documentation
make docs-serve    # Serve docs locally
make docs-clean    # Clean documentation build
```

### Build and Release Commands

```bash
make build         # Build package
make clean         # Clean build artifacts
make pre-release   # Run pre-release checks
make version       # Show package version
```

### Docker and Container Commands

```bash
make docker-check  # Check Docker availability
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit code
vim mcp_template/...

# Run development tests frequently
make dev-test
```

### 3. Test Your Changes

```bash
# Run appropriate tests
make test-quick      # For quick feedback
make test-unit       # For logic changes
make test-integration # For deployment changes
make test-template TEMPLATE=your-template # For template changes
```

### 4. Validate Code Quality

```bash
# Format code
make format

# Check code quality
make lint
make type-check
```

### 5. Test Locally

```bash
# Deploy and test your changes
make deploy-test

# Check logs
mcp-template logs test-deployment

# Clean up
make cleanup-test
```

### 6. Run Full Test Suite

```bash
# Before committing, run full tests
make ci-full
```

### 7. Submit Pull Request

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Debugging

### Template Development

```bash
# Validate specific template
python -c "from mcp_template import TemplateDiscovery; d = TemplateDiscovery(); t = d.discover_templates(); print('your-template' in t)"

# Test template deployment
mcp-template deploy your-template --show-config
```

### Testing Issues

```bash
# Run tests with verbose output
pytest tests/ -v

# Run specific test with debugging
pytest tests/test_deployment_units.py::test_specific_function -v -s

# Debug test failures
pytest tests/ --pdb
```

### Build Issues

```bash
# Clean everything and rebuild
make clean
make build

# Check for dependency conflicts
pip check
```

## Performance Optimization

### Development Speed

```bash
# Use quick tests during development
make test-quick

# Use unit tests for logic validation
make test-unit

# Only run integration tests when needed
make test-integration
```

### CI Simulation

```bash
# Quick CI check (< 5 minutes)
make ci-quick

# Full CI simulation (15-20 minutes)
make ci-full
```

## Troubleshooting

### Common Issues

**Docker not available:**
```bash
# Check Docker installation
make docker-check

# For testing without Docker
MOCK_CONTAINERS=true make test-unit
```

**Tests failing:**
```bash
# Check test environment
make validate-templates

# Reset development environment
make clean
make dev-setup
```

**Import errors:**
```bash
# Reinstall in development mode
make install-dev

# Check Python path
python -c "import mcp_template; print(mcp_template.__file__)"
```

**Make command not working:**
```bash
# Check if make is installed
which make

# Use direct commands instead
python -m pytest tests/
```
```

### 2. Make Changes

Edit code, add tests, update documentation.

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific tests
python -m pytest tests/test_specific.py

# Run with coverage
make coverage
```

### 4. Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make typecheck
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

## Makefile Commands

```bash
make install      # Install development dependencies
make test         # Run all tests
make coverage     # Run tests with coverage
make lint         # Run linting checks
make format       # Format code
make typecheck    # Run type checking
make docs         # Build documentation
make clean        # Clean build artifacts
```

## Environment Variables

Set these for development:

```bash
export MCP_DEBUG=true
export MCP_LOG_LEVEL=debug
export MCP_TEST_MODE=true
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Black Formatter
- Pylance
- Docker

### PyCharm

Configure:
- Python interpreter: `venv/bin/python`
- Code style: Black
- Test runner: pytest
