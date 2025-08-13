"""
Unit tests for DeploymentManager.

Tests the deployment lifecycle management and coordination
provided by the DeploymentManager common module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from mcp_template.core.deployment_manager import (
    DeploymentManager,
    DeploymentOptions,
    DeploymentResult,
)
from mcp_template.core.config_manager import ValidationResult


@pytest.mark.unit
class TestDeploymentManager:
    """Unit tests for DeploymentManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployment_manager = DeploymentManager(backend_type="mock")

    def test_deploy_template_basic(self):
        """Test basic template deployment."""
        # Mock template validation
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                # Mock config operations
                with patch.object(
                    self.deployment_manager.config_manager, "merge_config_sources"
                ) as mock_merge:
                    mock_merge.return_value = {"greeting": "Hello"}

                    with patch.object(
                        self.deployment_manager.config_manager, "validate_config"
                    ) as mock_validate:
                        mock_validate.return_value = ValidationResult(
                            valid=True, errors=[], warnings=[]
                        )

                        # Mock backend deployment
                        with patch.object(
                            self.deployment_manager.backend, "deploy_template"
                        ) as mock_deploy:
                            mock_deploy.return_value = {
                                "success": True,
                                "deployment_id": "demo-123",
                                "container_id": "container-123",
                            }

                            config_sources = {"config_values": {"greeting": "Hello"}}
                            options = DeploymentOptions(name="test-demo")

                            result = self.deployment_manager.deploy_template(
                                "demo", config_sources, options
                            )

        assert result.success is True
        assert result.deployment_id == "demo-123"

    def test_deploy_template_invalid_template(self):
        """Test deployment with invalid template."""
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=False,
        ):
            config_sources = {}
            options = DeploymentOptions()

            result = self.deployment_manager.deploy_template(
                "invalid", config_sources, options
            )

        assert result.success is False
        assert result.error is not None

    def test_deploy_template_config_validation_failure(self):
        """Test deployment with config validation failure."""
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager.config_manager, "merge_config_sources"
                ) as mock_merge:
                    mock_merge.return_value = {"invalid": "config"}

                    with patch.object(
                        self.deployment_manager.config_manager, "validate_config"
                    ) as mock_validate:
                        mock_validate.return_value = ValidationResult(
                            valid=False, errors=["Invalid config"], warnings=[]
                        )

                        config_sources = {"config_values": {"invalid": "config"}}
                        options = DeploymentOptions()

                        result = self.deployment_manager.deploy_template(
                            "demo", config_sources, options
                        )

        assert result.success is False
        assert result.error is not None

    def test_stop_deployment_success(self):
        """Test successful deployment stop."""
        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            mock_stop.return_value = {"success": True}

            result = self.deployment_manager.stop_deployment("demo-123")

        assert result.success is True
        mock_stop.assert_called_once_with("demo-123", force=False)

    def test_stop_deployment_not_found(self):
        """Test stopping non-existent deployment."""
        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            mock_stop.return_value = {"success": False, "error": "Not found"}

            result = self.deployment_manager.stop_deployment("nonexistent")

        assert result.success is False
        assert result.error == "Not found"

    def test_stop_deployment_with_force(self):
        """Test force stopping deployment."""
        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            mock_stop.return_value = {"success": True}

            result = self.deployment_manager.stop_deployment("demo-123", force=True)

        assert result.success is True
        mock_stop.assert_called_once_with("demo-123", force=True)

    def test_stop_deployments_bulk(self):
        """Test bulk deployment stopping."""
        deployments = ["demo-123", "demo-456", "demo-789"]

        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            mock_stop.return_value = {"success": True}

            results = self.deployment_manager.stop_deployments(deployments)

        assert len(results) == 3
        assert all(result.success for result in results)
        assert mock_stop.call_count == 3

    def test_get_deployment_logs_success(self):
        """Test successful log retrieval."""
        with patch.object(
            self.deployment_manager.backend, "get_deployment_logs"
        ) as mock_logs:
            mock_logs.return_value = {
                "success": True,
                "logs": "Application started\nServer running on port 8080",
            }

            result = self.deployment_manager.get_deployment_logs("demo-123")

        assert result.success is True
        assert "Application started" in result.logs
        mock_logs.assert_called_once_with(
            "demo-123", lines=None, since=None, until=None
        )

    def test_get_deployment_logs_not_found(self):
        """Test log retrieval for non-existent deployment."""
        with patch.object(
            self.deployment_manager.backend, "get_deployment_logs"
        ) as mock_logs:
            mock_logs.return_value = {"success": False, "error": "Deployment not found"}

            result = self.deployment_manager.get_deployment_logs("nonexistent")

        assert result.success is False
        assert result.error == "Deployment not found"

    def test_stream_deployment_logs(self):
        """Test log streaming functionality."""
        with patch.object(
            self.deployment_manager.backend, "stream_deployment_logs"
        ) as mock_stream:
            mock_stream.return_value = iter(["Line 1", "Line 2", "Line 3"])

            logs = list(
                self.deployment_manager.stream_deployment_logs("demo-123", follow=True)
            )

        assert len(logs) == 3
        assert logs[0] == "Line 1"
        assert logs[2] == "Line 3"
        mock_stream.assert_called_once_with("demo-123", follow=True, lines=None)

    def test_find_deployments_by_criteria(self):
        """Test finding deployments by various criteria."""
        mock_deployments = [
            {"deployment_id": "demo-123", "template": "demo", "status": "running"},
            {
                "deployment_id": "file-456",
                "template": "filesystem",
                "status": "stopped",
            },
        ]

        with patch.object(
            self.deployment_manager.backend, "list_deployments"
        ) as mock_list:
            mock_list.return_value = {"deployments": mock_deployments}

            # Test finding by template
            result = self.deployment_manager.find_deployments_by_criteria(
                template="demo"
            )

        assert len(result) == 1
        assert result[0]["deployment_id"] == "demo-123"

    def test_find_deployment_for_logs(self):
        """Test finding deployment for log operations."""
        with patch.object(
            self.deployment_manager, "find_deployments_by_criteria"
        ) as mock_find:
            mock_find.return_value = [
                {"deployment_id": "demo-123", "template": "demo", "status": "running"}
            ]

            deployment = self.deployment_manager.find_deployment_for_logs("demo")

        assert deployment is not None
        assert deployment["deployment_id"] == "demo-123"

    def test_deployment_options(self):
        """Test DeploymentOptions class."""
        options = DeploymentOptions(
            name="test-deployment",
            environment={"ENV_VAR": "value"},
            ports={"8080": 8080},
            volumes={"/host": "/container"},
        )

        assert options.name == "test-deployment"
        assert options.environment["ENV_VAR"] == "value"
        assert options.ports["8080"] == 8080
        assert options.volumes["/host"] == "/container"

    def test_deployment_result(self):
        """Test DeploymentResult class."""
        result = DeploymentResult(
            success=True,
            deployment_id="demo-123",
            template="demo",
            status="running",
            container_id="abc123",
            image="demo:latest",
            ports={"7071": 7071},
            config={"greeting": "Hello"},
            transport="http",
            endpoint="http://localhost:7071",
            duration=5.2,
        )

        assert result.success is True
        assert result.deployment_id == "demo-123"
        assert result.duration == 5.2

        # Test to_dict conversion
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["deployment_id"] == "demo-123"
        assert result_dict["ports"]["7071"] == 7071

    def test_reserved_env_vars_mapping(self):
        """Test that RESERVED_ENV_VARS are properly applied to deployment."""
        template_name = "demo"
        config_sources = {
            "config_values": {
                "transport": "http",
                "port": "8080",
                "host": "0.0.0.0",
                "log_level": "debug",
            }
        }
        options = DeploymentOptions(name="test-reserved-env", port=None)

        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager.config_manager, "merge_config_sources"
                ) as mock_merge:
                    # Mock merged config with RESERVED_ENV_VARS already mapped
                    merged_config = {
                        "MCP_TRANSPORT": "http",
                        "MCP_PORT": "8080",
                        "MCP_HOST": "0.0.0.0",
                        "MCP_LOG_LEVEL": "debug",
                        "hello_from": "Test",
                    }
                    mock_merge.return_value = merged_config

                    with patch.object(
                        self.deployment_manager.config_manager, "validate_config"
                    ) as mock_validate:
                        mock_validate.return_value = ValidationResult(
                            valid=True, errors=[], warnings=[]
                        )

                        with patch.object(
                            self.deployment_manager.backend, "deploy_template"
                        ) as mock_deploy:
                            mock_deploy.return_value = {
                                "success": True,
                                "deployment_id": "test-123",
                                "container_id": "container-123",
                            }

                            # Deploy with RESERVED_ENV_VARS in config
                            result = self.deployment_manager.deploy_template(
                                template_name, config_sources, options
                            )

                            # Verify deployment was successful
                            assert result.success is True

                            # Verify backend.deploy was called
                            mock_deploy.assert_called_once()

                            # Get the call arguments to backend.deploy_template
                            call_args = mock_deploy.call_args

                            # The call should be deploy_template(template_id=..., config=..., template_data=..., pull_image=...)
                            # Let's get the config parameter which contains the environment variables
                            call_kwargs = call_args.kwargs if call_args.kwargs else {}
                            deployment_config = call_kwargs.get("config", {})

                            # Verify RESERVED_ENV_VARS are mapped correctly in config
                            expected_env_mappings = {
                                "MCP_TRANSPORT": "http",
                                "MCP_PORT": "8080",
                                "MCP_HOST": "0.0.0.0",
                                "MCP_LOG_LEVEL": "debug",
                            }

                            # Check that config contains the mapped RESERVED_ENV_VARS
                            for (
                                env_key,
                                expected_value,
                            ) in expected_env_mappings.items():
                                assert (
                                    env_key in deployment_config
                                ), f"Missing {env_key} in config"
                                assert (
                                    str(deployment_config[env_key]) == expected_value
                                ), f"Wrong value for {env_key}: got {deployment_config.get(env_key)}, expected {expected_value}"

                            # hello_from is not a RESERVED_ENV_VAR so it should remain as-is
                            assert "hello_from" in deployment_config
                            assert deployment_config["hello_from"] == "Test"

    def test_reserved_env_vars_partial_mapping(self):
        """Test RESERVED_ENV_VARS mapping with only some variables present."""
        template_name = "demo"
        config_sources = {
            "config_values": {
                "transport": "http",
                "port": "9090",
                # Missing host and log_level - should not cause issues
                "hello_from": "Partial Test",
            }
        }
        options = DeploymentOptions(name="test-partial-env", port=None)

        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager.config_manager, "merge_config_sources"
                ) as mock_merge:
                    merged_config = {
                        "MCP_TRANSPORT": "http",
                        "MCP_PORT": "9090",
                        "hello_from": "Partial Test",
                    }
                    mock_merge.return_value = merged_config

                    with patch.object(
                        self.deployment_manager.config_manager, "validate_config"
                    ) as mock_validate:
                        mock_validate.return_value = ValidationResult(
                            valid=True, errors=[], warnings=[]
                        )

                        with patch.object(
                            self.deployment_manager.backend, "deploy_template"
                        ) as mock_deploy:
                            mock_deploy.return_value = {
                                "success": True,
                                "deployment_id": "test-partial-123",
                                "container_id": "container-partial-123",
                            }

                            # Deploy with partial RESERVED_ENV_VARS
                            result = self.deployment_manager.deploy_template(
                                template_name, config_sources, options
                            )

                            # Verify deployment was successful
                            assert result.success is True

                            # Verify backend.deploy was called
                            mock_deploy.assert_called_once()

                            # Get the call arguments
                            call_args = mock_deploy.call_args

                            # The call should be deploy_template(template_id=..., config=..., template_data=..., pull_image=...)
                            # Let's get the config parameter which contains the environment variables
                            call_kwargs = call_args.kwargs if call_args.kwargs else {}
                            deployment_config = call_kwargs.get("config", {})

                            # Verify that only present RESERVED_ENV_VARS are mapped

                            # Should have these mapped in config directly
                            assert "MCP_TRANSPORT" in deployment_config
                            assert deployment_config["MCP_TRANSPORT"] == "http"
                            assert "MCP_PORT" in deployment_config
                            assert deployment_config["MCP_PORT"] == "9090"

                            # hello_from is not a RESERVED_ENV_VAR so it should remain as-is
                            assert "hello_from" in deployment_config
                            assert deployment_config["hello_from"] == "Partial Test"
                            assert (
                                "MCP_HELLO_FROM" not in deployment_config
                            )  # Should NOT be mapped

                            # Should NOT have these (not in config)
                            assert "MCP_HOST" not in deployment_config
                            assert "MCP_LOG_LEVEL" not in deployment_config


@pytest.mark.integration
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
