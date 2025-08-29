"""
Pytest configuration for Github template tests.
"""

import sys
from pathlib import Path

import pytest

# Add template directory to Python path
template_dir = Path(__file__).parent.parent
sys.path.insert(0, str(template_dir))


@pytest.fixture(scope="session")
def template_config():
    """Load template configuration for tests."""
    import json

    config_file = template_dir / "template.json"
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
