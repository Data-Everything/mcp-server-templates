"""Test configuration and fixtures for demo server tests."""

import os
import sys
from pathlib import Path

import pytest

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def demo_config():
    """Fixture providing demo server configuration."""
    return {"hello_from": "Test Server", "log_level": "INFO"}


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up test environment variables."""
    monkeypatch.setenv("MCP_HELLO_FROM", "Test Server")
    monkeypatch.setenv("MCP_LOG_LEVEL", "INFO")


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to clean environment variables."""
    monkeypatch.delenv("MCP_HELLO_FROM", raising=False)
    monkeypatch.delenv("MCP_LOG_LEVEL", raising=False)
