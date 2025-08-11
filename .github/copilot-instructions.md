# MCP Server Templates Development Guide

Always follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

**CRITICAL Environment Setup:**
```bash
export PYTHONPATH=/home/runner/work/mcp-server-templates/mcp-server-templates:$PYTHONPATH
```

**Install Dependencies:**
```bash
# Runtime dependencies - takes ~60 seconds. NEVER CANCEL.
time pip install -r requirements.txt
# Expected time: 56 seconds. Set timeout to 120+ seconds.

# Development dependencies - takes ~50 seconds. NEVER CANCEL.  
time pip install -r requirements-dev.txt
# Expected time: 45 seconds. Set timeout to 120+ seconds.

# Note: pip install -e . may fail due to network timeouts - use PYTHONPATH export instead
```

**Test the Installation:**
```bash
# Basic functionality test - takes <1 second
python -m mcp_template --help

# Template validation - takes <1 second  
make validate-templates
# Expected output: "Found 5 templates: ['filesystem', 'zendesk', 'github', 'gitlab', 'demo']"

# List available templates - takes <1 second
python -m mcp_template list
```

**Run Tests:**
```bash
# Unit tests - takes ~25 seconds. NEVER CANCEL.
time python tests/runner.py --unit
# Expected time: 23 seconds. Set timeout to 60+ seconds.

# Integration tests - takes ~40 seconds. NEVER CANCEL.
time python tests/runner.py --integration  
# Expected time: 38 seconds. Set timeout to 90+ seconds.

# All tests together - takes ~60-90 seconds. NEVER CANCEL.
time python tests/runner.py --all
# Set timeout to 180+ seconds.
```

**Code Quality Checks:**
```bash
# Code formatting - takes ~3 seconds
time make format
# Expected time: 2.3 seconds. Set timeout to 30+ seconds.

# Linting - has warnings but runs, takes ~2 seconds
make lint
# Note: Will show E226 warnings but completes successfully

# Type checking - has errors but completes, takes ~25 seconds. NEVER CANCEL.
time make type-check  
# Expected time: 22 seconds, 100+ type errors. Set timeout to 60+ seconds.
# Note: Many type errors exist but this is expected in development
```

## Validation

### Always Manually Validate Functionality

**Test Core Commands (Each takes <1 second):**
```bash
# List all templates
python -m mcp_template list

# Show configuration for demo template
python -m mcp_template config demo

# Show integration examples  
python -m mcp_template connect demo

# Show configuration without deploying
python -m mcp_template deploy demo --show-config
```

**Test Template Discovery:**
```bash
# Validate template structure
make validate-templates
# Expected: "Found 5 templates: ['filesystem', 'zendesk', 'github', 'gitlab', 'demo']"
```

**ALWAYS test these user scenarios after making changes:**
1. **Template Listing**: Verify all 5 templates are discovered
2. **Configuration Display**: Check demo template shows 3 config properties (hello_from, log_level, allowed_dirs)
3. **Integration Examples**: Verify connect command shows FastMCP, Claude Desktop, VS Code, HTTP API examples
4. **CLI Help**: Ensure all commands show proper help text

### Known Limitations and Workarounds

**Docker Deployment Testing:**
```bash
# Docker is available but deployment requires network access for image pulling
docker --version  # Should show: Docker version 28.0.4, build b8034c0
docker ps  # Should show running containers

# For testing deployment without network: 
python -m mcp_template deploy demo --no-pull --show-config
# This shows config without attempting image pull
```

**Interactive CLI Mode:**
```bash
# Interactive mode may hang - use carefully
python -m mcp_template interactive
# If it hangs, use Ctrl+C to exit and use individual commands instead
```

**Deprecated Commands:**
- `python -m mcp_template tools` - Shows deprecation warning, use interactive CLI instead
- `python -m mcp_template run-tool` - Shows deprecation warning, use interactive CLI instead

## Common Tasks

### Repository Structure Reference
```
.
├── README.md                    # Main documentation
├── CONTRIBUTING.md              # Development guidelines  
├── PROJECT_ARCHITECTURE_GUIDE.md # Technical architecture
├── pyproject.toml              # Package configuration
├── requirements.txt            # Runtime dependencies (7 packages)
├── requirements-dev.txt        # Development dependencies (40+ packages)
├── Makefile                    # Development commands
├── mcp_template/               # Main Python package
│   ├── __init__.py            # CLI entry point
│   ├── deployer.py            # Template deployment
│   ├── interactive_cli.py     # Interactive CLI mode
│   └── template/              # Template system
│       └── templates/         # Built-in templates
├── tests/                     # Test suite
│   ├── runner.py              # Test runner script
│   └── test_*.py              # Individual test files
├── docs/                      # Documentation
└── .github/workflows/         # CI/CD pipelines
```

### Key Configuration Properties

**Demo Template Configuration:**
- `hello_from` (string): Greeting source, default "MCP Platform"
- `log_level` (string): Logging level, default "info", enum: debug|info|warning|error
- `allowed_dirs` (string): File access directories, default "/tmp"

**Filesystem Template Configuration (Required):**
- `allowed_dirs` (string): **REQUIRED** - Space-separated allowed directories
- `log_level` (string): Logging level, default "INFO"

### Environment Variables

**Key Environment Mappings:**
- `MCP_HELLO_FROM` → hello_from config
- `MCP_LOG_LEVEL` → log_level config  
- `MCP_ALLOWED_DIRS` → allowed_dirs config
- `LOG_LEVEL` → filesystem template log_level
- `ALLOWED_DIRS` → filesystem template allowed_dirs

### Testing Patterns

**Test Categories:**
- `unit` - Fast tests, no Docker required (~23s)
- `integration` - Slower tests, may use Docker (~38s) 
- `docker` - Requires Docker daemon
- `e2e` - End-to-end tests
- `template` - Template-specific tests

**Test Commands:**
```bash
# Run specific test categories
python tests/runner.py --unit
python tests/runner.py --integration
python tests/runner.py --docker
python tests/runner.py --template

# Run specific test file
python tests/runner.py --file tests/test_config_strategy.py
```

## Build and Development Workflow

### Standard Development Commands

**Setup:**
```bash
# Initial setup
make dev-setup
# This runs: make install install-dev

# Quick development test
make dev-test  
# This runs: make test-quick lint
```

**Development Cycle:**
```bash
# 1. Format code (~3 seconds)
make format

# 2. Run quick tests (~25 seconds)
python tests/runner.py --unit

# 3. Lint code (~2 seconds, expect warnings)
make lint

# 4. Validate templates (<1 second)
make validate-templates
```

**Before Committing:**
```bash
# Full validation (~90 seconds total). NEVER CANCEL.
make dev-test      # Quick tests + linting
python tests/runner.py --integration  # Integration tests
# Set timeout to 180+ seconds for complete validation
```

### CI/CD Simulation

**Quick CI check (~30 seconds):**
```bash
make ci-quick
# Runs: test-quick + lint
```

**Full CI simulation (~120+ seconds). NEVER CANCEL:**
```bash
make ci-full
# Runs: install + test-quick + test-unit + lint + type-check + test-integration + build
# Set timeout to 300+ seconds
```

## Exact Commands Reference

### Package Management
- `pip install -r requirements.txt` (60s timeout)
- `pip install -r requirements-dev.txt` (60s timeout)

### Testing  
- `python tests/runner.py --unit` (60s timeout)
- `python tests/runner.py --integration` (90s timeout)
- `python tests/runner.py --all` (180s timeout)

### Code Quality
- `make format` (30s timeout)
- `make lint` (30s timeout)  
- `make type-check` (60s timeout, expect errors)

### Template Operations
- `python -m mcp_template list` (10s timeout)
- `python -m mcp_template config <template>` (10s timeout)
- `python -m mcp_template connect <template>` (10s timeout)
- `make validate-templates` (10s timeout)

### Build Operations
- `make build` (60s timeout)
- `make clean` (10s timeout)

**CRITICAL**: Always use the PYTHONPATH export for any python -m mcp_template commands. The pip install -e . approach may fail due to network timeouts.

## Known Working Scenarios

### Scenario 1: Template Exploration
```bash
export PYTHONPATH=/home/runner/work/mcp-server-templates/mcp-server-templates:$PYTHONPATH
python -m mcp_template list
python -m mcp_template config demo
python -m mcp_template config filesystem
```

### Scenario 2: Development Testing
```bash
make format
python tests/runner.py --unit
make validate-templates
```

### Scenario 3: Integration Examples
```bash
export PYTHONPATH=/home/runner/work/mcp-server-templates/mcp-server-templates:$PYTHONPATH
python -m mcp_template connect demo
python -m mcp_template deploy demo --show-config
```

Always validate these scenarios work correctly after making changes to ensure the system is functioning properly.