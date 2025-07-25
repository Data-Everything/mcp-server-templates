# Makefile for MCP Server Templates

.PHONY: help install test test-unit test-integration test-all test-quick clean lint format

# Default target
help:
	@echo "MCP Server Templates Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install development dependencies"
	@echo "  install-dev   Install in development mode"
	@echo ""
	@echo "Testing:"
	@echo "  test-quick    Run quick validation tests"
	@echo "  test-unit     Run unit tests (fast, no Docker)"
	@echo "  test-integration  Run integration tests (requires Docker)"
	@echo "  test-all      Run all tests"
	@echo "  test          Alias for test-all"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run code linting"
	@echo "  format        Format code"
	@echo "  type-check    Run type checking"
	@echo ""
	@echo "Deployment:"
	@echo "  build         Build package"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Local Development:"
	@echo "  deploy-test   Deploy a test template locally"
	@echo "  cleanup-test  Cleanup test deployments"

# Installation
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-dev:
	pip install -e .

# Testing
test-quick:
	@echo "🔬 Running quick validation tests..."
	pytest tests/test_runner.py quick

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/test_runner.py unit

test-integration:
	@echo "🐳 Running integration tests..."
	pytest tests/test_runner.py integration

test-all:
	@echo "🚀 Running all tests..."
	pytest tests/test_runner.py all

test:
	pytest tests

# Code quality
lint:
	@echo "🔍 Running code linting..."
	flake8 mcp_deploy/ tests/ --max-line-length=100 --ignore=E203,W503
	bandit -r mcp_deploy/ -f json -o bandit-report.json || true

format:
	@echo "🎨 Formatting code..."
	black mcp_deploy/ tests/
	isort mcp_deploy/ tests/

type-check:
	@echo "🔬 Running type checking..."
	mypy mcp_deploy/ --ignore-missing-imports

# Package building
build:
	@echo "📦 Building package..."
	python -m build

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Local development helpers
deploy-test:
	@echo "🚀 Deploying test template..."
	python -m mcp_deploy deploy file-server

cleanup-test:
	@echo "🧹 Cleaning up test deployments..."
	python -m mcp_deploy cleanup --all

list-templates:
	@echo "📋 Available templates:"
	python -m mcp_deploy list

# CI/CD simulation
ci-quick:
	@echo "⚡ Simulating CI quick tests..."
	make test-quick
	make lint

ci-full:
	@echo "🏗️ Simulating full CI pipeline..."
	make install
	make test-quick
	make test-unit
	make lint
	make type-check
	make test-integration
	make build

# Development workflow
dev-setup: install install-dev
	@echo "✅ Development environment setup complete!"

dev-test: test-quick lint
	@echo "✅ Development tests passed!"

# Coverage reporting
coverage:
	@echo "📊 Generating coverage report..."
	pytest tests/test_deployment_units.py -m unit --cov=mcp_deploy --cov-report=html --cov-report=term
	@echo "📋 Coverage report generated in htmlcov/"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "TODO: Add documentation generation"

# Docker helpers
docker-check:
	@echo "🐳 Checking Docker availability..."
	docker --version
	docker ps

# Template development
validate-templates:
	@echo "✅ Validating all templates..."
	python -c "from mcp_deploy import TemplateDiscovery; import sys; d = TemplateDiscovery(); t = d.discover_templates(); print(f'Found {len(t)} templates: {list(t.keys())}') if t else sys.exit(1)"

# Release helpers
pre-release: ci-full
	@echo "🚀 Pre-release checks complete!"

version:
	@echo "📊 Package version:"
	python -c "import mcp_deploy; print(getattr(mcp_deploy, '__version__', 'unknown'))"
