# Template Testing and Docker Release Workflow

This document explains the integrated template testing and Docker release workflow.

## How It Works

1. **Change Detection**: Detects which template directories have changes
2. **Template Testing**: Runs comprehensive tests for each changed template
3. **Docker Build Test**: Validates Dockerfile builds successfully
4. **Docker Release**: Only pushes to Docker Hub if all tests pass

## Workflow Triggers

- **Push to main**: When template files change
- **Pull Request**: For validation before merge
- **Manual Dispatch**: Build all templates with Dockerfiles

## Test Steps Per Template

1. **Unit Tests**: Fast tests without external dependencies
2. **Integration Tests**: Tests with MCP client simulation
3. **Coverage Check**: Ensures 80%+ test coverage
4. **Configuration Validation**: Validates template.json and docs
5. **Server Startup Test**: Ensures server can start without errors
6. **Docker Build Test**: Validates Dockerfile builds successfully

## Only Tested Templates Get Released

The workflow ensures that **only templates that pass all tests** get built and pushed to Docker Hub. This prevents broken images from being published.

## Template Requirements

For a template to be built and released, it must have:

- ✅ `Dockerfile` present
- ✅ `template.json` with required fields
- ✅ `docs/index.md` documentation
- ✅ Tests that pass (if `tests/` directory exists)
- ✅ Valid server startup (if `src/server.py` exists)

## Available Images

Templates that pass all requirements are available at:
- `docker pull dataeverything/mcp-file-server:latest`
- `docker pull dataeverything/mcp-demo:latest`

## Local Testing

Test a template locally before pushing:

```bash
# Test specific template
make test-template TEMPLATE=file-server

# Test all templates
make test-templates

# Build Docker image locally
cd templates/file-server
docker build -t test-file-server .
```
