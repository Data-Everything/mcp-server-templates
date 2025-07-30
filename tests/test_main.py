#!/usr/bin/env python3
"""
Tests for mcp_template.__main__ module.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
class TestMain:
    """Test the __main__ module entry point."""

    @patch("mcp_template.main")
    def test_main_entry_point(self, mock_main):
        """Test that the main function is called when module is executed."""
        # Import and execute the __main__ module
        import importlib.util

        main_module_path = Path(__file__).parent.parent / "mcp_template" / "__main__.py"
        spec = importlib.util.spec_from_file_location("__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)

        # Execute the module
        spec.loader.exec_module(main_module)

        # Verify main was called
        mock_main.assert_called_once()

    def test_main_module_structure(self):
        """Test that __main__ module has correct structure."""
        main_module_path = Path(__file__).parent.parent / "mcp_template" / "__main__.py"

        # Read the file content
        with open(main_module_path, encoding="utf-8") as f:
            content = f.read()

        # Verify expected content structure
        assert "from mcp_template import main" in content
        assert 'if __name__ == "__main__":' in content
        assert "main()" in content

    @patch("mcp_template.main")
    def test_main_not_called_on_import(self, mock_main):
        """Test that main is not called when module is imported (not executed)."""
        # Import the __main__ module (but don't execute it as __main__)
        import mcp_template.__main__  # noqa: F401

        # Verify main was not called during import
        mock_main.assert_not_called()
