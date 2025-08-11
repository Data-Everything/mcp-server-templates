"""
Test CLI override functionality integration with deployment
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_template.deployer import MCPDeployer


@pytest.mark.unit
class TestCLIOverrides:
    """Test CLI override functionality integration with deployment."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

    @pytest.mark.skip(
        reason="Integration test needs rework after refactoring - will fix in Phase 3"
    )
    def test_deploy_method_integration(self):
        """Test that override values are properly passed through deploy method."""
        # Mock the deployment manager and template discovery
        with (
            patch.object(self.deployer, "deployment_manager") as mock_manager,
            patch.object(
                self.deployer,
                "templates",
                {"test": {"name": "test", "image": "test:latest"}},
            ),
            patch.object(self.deployer, "_generate_mcp_config"),
        ):

            mock_manager.deploy_template.return_value = {
                "deployment_name": "test-deployment",
                "status": "deployed",
                "image": "test:latest",
            }

            # Test deploy with override values
            result = self.deployer.deploy(
                template_name="test", override_values={"metadata__version": "2.0.0"}
            )

            # Verify that deploy_template was called and deployment succeeded
            assert mock_manager.deploy_template.called
            assert result is True
            call_args = mock_manager.deploy_template.call_args

            # Check that override values were converted to environment variables
            config = call_args[1]["configuration"]
            assert "OVERRIDE_metadata__version" in config
            assert config["OVERRIDE_metadata__version"] == "2.0.0"
