"""
Integration tests for Filesystem template.
"""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path

from mcp_template.utils import TESTS_DIR

# Import MCP testing utilities
import sys

sys.path.insert(0, str(TESTS_DIR / "utils"))


@pytest.mark.integration
@pytest.mark.asyncio
class TestFilesystemIntegration:
    """Integration tests for Filesystem template."""

    @pytest_asyncio.fixture
    async def mcp_client(self):
        """Create MCP test client."""
        template_dir = Path(
            "/home/samarora/data-everything/mcp-server-templates/mcp_template/template/templates/filesystem"
        )
        client = MCPTestClient(template_dir / "server.py")
        await client.start()
        yield client
        await client.stop()

    async def test_server_connection(self, mcp_client):
        """Test MCP server connection."""
        tools = await mcp_client.list_tools()
        assert len(tools) >= 0  # Server should be accessible

    async def test_example_integration(self, mcp_client):
        """Test example integration."""
        result = await mcp_client.call_tool("example", {})
        assert result is not None
        # TODO: Add specific assertions for example
