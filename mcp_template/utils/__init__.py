"""
MCP Template Utilities
"""

from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
PACKAGE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "template" / "templates"
TESTS_DIR = ROOT_DIR / "tests"
