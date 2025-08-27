"""
Unit tests for the base backend module (mcp_template.backends.base).

Tests the abstract base class for deployment backends.
"""

import pytest

from mcp_template.backends.base import BaseDeploymentBackend


class ConcreteBackend(BaseDeploymentBackend):
    """Concrete implementation of BaseDeploymentBackend for testing."""

    def deploy_template(
        self,
        template_id,
        config,
        template_data,
        backend_config,
        pull_image=True,
        dry_run=False,
    ):
        """Concrete implementation for testing."""
        return {
            "success": True,
            "deployment_id": f"test-{template_id}",
            "template_id": template_id,
            "status": "running",
        }

    def stop_deployment(self, deployment_id):
        """Concrete implementation for testing."""
        return {"success": True, "deployment_id": deployment_id}

    def get_deployment_status(self, deployment_id):
        """Concrete implementation for testing."""
        return {"deployment_id": deployment_id, "status": "running"}

    def list_deployments(self):
        """Concrete implementation for testing."""
        return [{"deployment_id": "test-1", "status": "running"}]

    def get_deployment_logs(self, deployment_id, lines=None):
        """Concrete implementation for testing."""
        return ["log line 1", "log line 2"]

    def execute_tool(self, deployment_id, tool_name, parameters):
        """Concrete implementation for testing."""
        return {"result": "success", "output": "tool executed"}

    def health_check(self):
        """Concrete implementation for testing."""
        return {"status": "healthy"}


class TestBaseDeploymentBackend:
    """Test the BaseDeploymentBackend abstract base class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = ConcreteBackend()

    def test_init(self):
        """Test BaseDeploymentBackend initialization."""
        assert hasattr(self.backend, "_config")
        assert self.backend._config == {}

    def test_is_available_default(self):
        """Test default is_available property."""
        # Base implementation returns False
        base_backend = BaseDeploymentBackend()
        assert base_backend.is_available is False

    def test_is_available_can_be_overridden(self):
        """Test that is_available can be overridden in subclasses."""

        class AvailableBackend(BaseDeploymentBackend):
            @property
            def is_available(self):
                return True

            def deploy_template(self, *args, **kwargs):
                return {}

        backend = AvailableBackend()
        assert backend.is_available is True

    def test_deploy_template_abstract_method(self):
        """Test that deploy_template is abstract."""
        with pytest.raises(TypeError):
            BaseDeploymentBackend()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation works."""
        result = self.backend.deploy_template(
            template_id="test",
            config={"key": "value"},
            template_data={"name": "Test Template"},
            backend_config={},
        )
        assert result["success"] is True
        assert result["template_id"] == "test"

    def test_deploy_template_with_all_parameters(self):
        """Test deploy_template with all parameters."""
        result = self.backend.deploy_template(
            template_id="full-test",
            config={"param1": "value1"},
            template_data={"description": "Full test"},
            backend_config={"backend_param": "backend_value"},
            pull_image=False,
            dry_run=True,
        )
        assert result is not None
        assert result["template_id"] == "full-test"

    def test_config_property_access(self):
        """Test config property access and modification."""
        # Initial config is empty
        assert self.backend._config == {}

        # Can modify config
        self.backend._config["key"] = "value"
        assert self.backend._config["key"] == "value"

    def test_config_property_isolation(self):
        """Test that config is isolated between instances."""
        backend1 = ConcreteBackend()
        backend2 = ConcreteBackend()

        backend1._config["key1"] = "value1"
        backend2._config["key2"] = "value2"

        assert "key1" not in backend2._config
        assert "key2" not in backend1._config


class TestBaseDeploymentBackendInheritance:
    """Test inheritance behavior and abstract method enforcement."""

    def test_subclass_must_implement_deploy_template(self):
        """Test that subclasses must implement deploy_template."""

        class IncompleteBackend(BaseDeploymentBackend):
            pass

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_subclass_with_implementation_works(self):
        """Test that subclass with proper implementation works."""

        class WorkingBackend(BaseDeploymentBackend):
            def deploy_template(
                self,
                template_id,
                config,
                template_data,
                backend_config,
                pull_image=True,
                dry_run=False,
            ):
                return {"working": True, "template_id": template_id}

        backend = WorkingBackend()
        result = backend.deploy_template("test", {}, {}, {})
        assert result["working"] is True

    def test_optional_methods_have_defaults(self):
        """Test that optional methods have default implementations or can be left unimplemented."""

        class MinimalBackend(BaseDeploymentBackend):
            def deploy_template(
                self,
                template_id,
                config,
                template_data,
                backend_config,
                pull_image=True,
                dry_run=False,
            ):
                return {"minimal": True}

        backend = MinimalBackend()

        # Should be able to create instance with just required method
        assert backend is not None

        # Optional methods might not be implemented
        # This depends on whether they're abstract or have default implementations

    def test_multiple_inheritance_compatibility(self):
        """Test that BaseDeploymentBackend works with multiple inheritance."""

        class Mixin:
            def extra_method(self):
                return "mixin"

        class MultiInheritanceBackend(BaseDeploymentBackend, Mixin):
            def deploy_template(
                self,
                template_id,
                config,
                template_data,
                backend_config,
                pull_image=True,
                dry_run=False,
            ):
                return {"multi": True}

        backend = MultiInheritanceBackend()
        assert backend.deploy_template("test", {}, {}, {})["multi"] is True
        assert backend.extra_method() == "mixin"


class TestBaseDeploymentBackendDocumentation:
    """Test documentation and type hints."""

    def test_class_docstring(self):
        """Test that BaseDeploymentBackend has proper documentation."""
        assert BaseDeploymentBackend.__doc__ is not None
        assert (
            "Abstract base class for deployment backends"
            in BaseDeploymentBackend.__doc__
        )

    def test_deploy_template_docstring(self):
        """Test that deploy_template method has proper documentation."""
        assert BaseDeploymentBackend.deploy_template.__doc__ is not None
        assert (
            "Deploy a template using the backend"
            in BaseDeploymentBackend.deploy_template.__doc__
        )

    def test_module_docstring(self):
        """Test that module has proper documentation."""
        from mcp_template.backends import base

        assert base.__doc__ is not None
        assert "Deployment backend interface" in base.__doc__


class TestBaseDeploymentBackendMethodSignatures:
    """Test method signatures and parameter handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = ConcreteBackend()

    def test_deploy_template_required_parameters(self):
        """Test deploy_template with required parameters only."""
        result = self.backend.deploy_template(
            template_id="test", config={}, template_data={}, backend_config={}
        )
        assert result is not None

    def test_deploy_template_optional_parameters(self):
        """Test deploy_template with optional parameters."""
        result = self.backend.deploy_template(
            template_id="test",
            config={},
            template_data={},
            backend_config={},
            pull_image=False,
            dry_run=True,
        )
        assert result is not None

    def test_deploy_template_parameter_types(self):
        """Test deploy_template parameter type handling."""
        # Test with various parameter types
        result = self.backend.deploy_template(
            template_id="test-123",
            config={"number": 42, "boolean": True, "list": [1, 2, 3]},
            template_data={"nested": {"key": "value"}},
            backend_config={"timeout": 30},
            pull_image=False,
            dry_run=False,
        )
        assert result is not None

    def test_is_available_property_signature(self):
        """Test is_available property signature."""
        # Should be a property, not a method
        assert isinstance(type(self.backend).is_available, property)


class TestBaseDeploymentBackendErrorHandling:
    """Test error handling in BaseDeploymentBackend."""

    def test_error_handling_in_concrete_implementation(self):
        """Test error handling behavior."""

        class ErrorBackend(BaseDeploymentBackend):
            def deploy_template(
                self,
                template_id,
                config,
                template_data,
                backend_config,
                pull_image=True,
                dry_run=False,
            ):
                if template_id == "error":
                    raise Exception("Test error")
                return {"success": True}

        backend = ErrorBackend()

        # Normal case should work
        result = backend.deploy_template("normal", {}, {}, {})
        assert result["success"] is True

        # Error case should raise
        with pytest.raises(Exception, match="Test error"):
            backend.deploy_template("error", {}, {}, {})

    def test_config_modification_safety(self):
        """Test that config modifications are safe."""
        backend = ConcreteBackend()

        # Should not raise when modifying config
        backend._config.update({"key1": "value1", "key2": "value2"})
        assert len(backend._config) == 2

        # Should not raise when clearing config
        backend._config.clear()
        assert len(backend._config) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
