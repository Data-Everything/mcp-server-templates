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

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt
```

## Verify Setup

```bash
# Check CLI works
mcp-template --version
mcp-template list

# Run tests
python -m pytest

# Run code quality checks
make lint
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
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
