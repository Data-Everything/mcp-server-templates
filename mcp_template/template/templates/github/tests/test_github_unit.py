"""
Unit tests for Github template.
"""

import pytest
from unittest.mock import Mock, patch

# Import the server module
import sys

sys.path.insert(
    0,
    str(
        "/home/samarora/data-everything/mcp-server-templates/mcp_template/template/templates/github"
    ),
)

from server import app, load_config


class TestGithubUnit:
    """Unit tests for Github template."""

    def test_config_loading(self):
        """Test configuration loading."""
        config = load_config()
        assert config is not None

    def test_server_initialization(self):
        """Test server initialization."""
        assert app is not None
        assert app.name == "github"

    def test_example(self):
        """Test example functionality."""
        # TODO: Implement unit test for example
        pass
