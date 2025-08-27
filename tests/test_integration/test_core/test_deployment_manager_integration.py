"""
Integration tests for DeploymentManager.

Tests the deployment manager with real backend interactions
and end-to-end deployment scenarios using mock backends.
"""

import pytest

from mcp_template.core.deployment_manager import DeploymentManager, DeploymentOptions

pytestmark = pytest.mark.integration


class TestDeploymentManagerIntegration:
    """Integration tests for DeploymentManager."""

    def test_deployment_manager_with_real_backend(self):
        """Test deployment manager with mock backend."""
        deployment_manager = DeploymentManager(backend_type="mock")

        # Should be able to find deployments without errors
        deployments = deployment_manager.find_deployments_by_criteria()
        assert isinstance(deployments, list)

    def test_deployment_error_handling(self):
        """Test deployment error handling in integration scenarios."""
        deployment_manager = DeploymentManager(backend_type="mock")

        # Test with invalid configuration
        config_sources = {"config_values": {"invalid": "config"}}
        options = DeploymentOptions()

        result = deployment_manager.deploy_template(
            "nonexistent", config_sources, options
        )
        assert result.success is False
        assert result.error is not None
