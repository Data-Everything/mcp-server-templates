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
	@echo "  test-template Run tests for a specific template (usage: make test-template TEMPLATE=file-server)"
	@echo "  test-templates Run tests for all templates"
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
	pytest tests/runner.py quick

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/runner.py unit

test-integration:
	@echo "🐳 Running integration tests..."
	pytest tests/runner.py integration

test-all:
	@echo "🚀 Running all tests..."
	pytest tests/runner.py all

test:
	pytest tests

# Template-specific testing
test-template:
	@if [ -z "$(TEMPLATE)" ]; then \
		echo "❌ Please specify a template: make test-template TEMPLATE=file-server"; \
		exit 1; \
	fi; \
	if [ -d "templates/$(TEMPLATE)/tests" ]; then \
		echo "🧪 Running tests for template: $(TEMPLATE)"; \
		cd templates/$(TEMPLATE) && pytest tests/ -v; \
	else \
		echo "❌ No tests found for template: $(TEMPLATE)"; \
		exit 1; \
	fi

test-templates:
	@echo "🧪 Running tests for all templates..."
	@for template in templates/*/; do \
		template_name=$$(basename "$$template"); \
		if [ -d "$$template/tests" ]; then \
			echo "Testing $$template_name..."; \
			cd "$$template" && pytest tests/ -v --tb=short || exit 1; \
			cd - > /dev/null; \
		else \
			echo "⚠️  No tests found for $$template_name"; \
		fi \
	done; \
	echo "✅ All template tests completed!"

# Code quality
lint:
	@echo "🔍 Running code linting..."
	flake8 mcp_template/ tests/ --max-line-length=100 --ignore=E203,W503
	bandit -r mcp_template/ -f json -o bandit-report.json || true

format:
	@echo "🎨 Formatting code..."
	black mcp_template/ tests/
	isort mcp_template/ tests/

type-check:
	@echo "🔬 Running type checking..."
	mypy mcp_template/ --ignore-missing-imports

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
	python -m mcp_template deploy file-server

cleanup-test:
	@echo "🧹 Cleaning up test deployments..."
	python -m mcp_template cleanup --all

list-templates:
	@echo "📋 Available templates:"
	python -m mcp_template list

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
	pytest tests/test_deployment_units.py -m unit --cov=mcp_template --cov-report=html --cov-report=term
	@echo "📋 Coverage report generated in htmlcov/"

# Documentation
docs:
	@echo "📚 Building documentation..."
	python scripts/build_docs.py

docs-serve:
	@echo "🌐 Serving documentation locally..."
	mkdocs serve

docs-clean:
	@echo "🧹 Cleaning documentation build..."
	rm -rf site/
	find docs/templates/ -mindepth 1 -maxdepth 1 -type d ! -name ".pages" -exec rm -rf {} +

# Docker helpers
docker-check:
	@echo "🐳 Checking Docker availability..."
	docker --version
	docker ps

# Template development
validate-templates:
	@echo "✅ Validating all templates..."
	python -c "from mcp_template import TemplateDiscovery; import sys; d = TemplateDiscovery(); t = d.discover_templates(); print(f'Found {len(t)} templates: {list(t.keys())}') if t else sys.exit(1)"

# Release helpers
pre-release: ci-full
	@echo "🚀 Pre-release checks complete!"

version:
	@echo "📊 Package version:"
	python -c "import mcp_template; print(getattr(mcp_template, '__version__', 'unknown'))"
