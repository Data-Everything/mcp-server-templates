"""
MCP Template Utilities
"""

from pathlib import Path

# Directory constants
ROOT_DIR = Path(__file__).parent.parent.parent
PACKAGE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "template" / "templates"
TESTS_DIR = ROOT_DIR / "tests"

# Note: Visual formatting utilities have been moved to mcp_template.core.response_formatter
# Import them directly from there to avoid circular dependencies
