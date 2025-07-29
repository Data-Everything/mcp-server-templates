"""
Test mock deployment service functionality.
"""

from unittest.mock import Mock

import pytest

from mcp_template.backends.mock import MockDeploymentService


class TestMockDeploymentService:
    """Test mock deployment service."""

    def test_init(self):
        """Test mock service initialization."""
        service = MockDeploymentService()
        assert service.deployments == {}

    def test_deploy_template(self):
        """Test mock template deployment."""
        service = MockDeploymentService()
        template_data = {"image": "test-image:latest"}
        config = {"param1": "value1"}

        result = service.deploy_template("test", config, template_data)

        assert result["template_id"] == "test"
        assert result["status"] == "deployed"
        assert result["mock"] is True
        assert "deployment_name" in result

    def test_list_deployments(self):
        """Test listing mock deployments."""
        service = MockDeploymentService()

        # Deploy a template first
        service.deploy_template("test", {}, {"image": "test:latest"})

        deployments = service.list_deployments()
        assert len(deployments) == 1
        assert deployments[0]["template"] == "test"
        assert deployments[0]["mock"] is True

    def test_delete_deployment(self):
        """Test deleting mock deployment."""
        service = MockDeploymentService()

        # Deploy first
        result = service.deploy_template("test", {}, {"image": "test:latest"})
        deployment_name = result["deployment_name"]

        # Delete
        success = service.delete_deployment(deployment_name)
        assert success is True
        assert deployment_name not in service.deployments

    def test_delete_deployment_not_found(self):
        """Test deleting non-existent deployment."""
        service = MockDeploymentService()

        success = service.delete_deployment("nonexistent")
        assert success is False

    def test_get_deployment_status(self):
        """Test getting deployment status."""
        service = MockDeploymentService()

        # Deploy first
        result = service.deploy_template("test", {}, {"image": "test:latest"})
        deployment_name = result["deployment_name"]

        # Get status
        status = service.get_deployment_status(deployment_name)
        assert status["name"] == deployment_name
        assert status["status"] == "running"
        assert status["mock"] is True
