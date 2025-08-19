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


class SubProcessRunDummyResult:
    """
    Mimics subprocess.run command's dummy response
    """

    def __init__(self, args=None, returncode=0, stdout=None, stderr=None):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def check_returncode(self):
        if self.returncode != 0:
            raise RuntimeError(
                f"Command '{self.args}' returned non-zero exit status {self.returncode}."
            )
