# Test all templates in the repository

import sys
from pathlib import Path

import pytest

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils.mcp_test_utils import (
    get_template_list,
    run_template_tests,
    validate_template_structure,
)


class TestAllTemplates:
    """Test all available templates."""

    @pytest.fixture(scope="class")
    def template_list(self):
        """Get list of all templates."""
        return get_template_list()

    def test_all_templates_have_required_structure(self, template_list):
        """Test that all templates have required files and structure."""
        for template_name in template_list:
            try:
                validate_template_structure(template_name)
            except Exception as e:
                pytest.fail(
                    f"Template {template_name} structure validation failed: {e}"
                )

    @pytest.mark.slow
    def test_all_templates_build_successfully(self, template_list):
        """Test that all templates can be built."""
        results = {}

        for template_name in template_list:
            print(f"\nTesting template: {template_name}")
            result = run_template_tests(template_name)
            results[template_name] = result

            # Assert basic requirements
            assert result[
                "structure_valid"
            ], f"{template_name}: Structure validation failed"

            if result["errors"]:
                print(f"Errors for {template_name}: {result['errors']}")

            # Build should succeed for production templates
            if template_name in ["file-server"]:  # Production-ready templates
                assert result["build_successful"], f"{template_name}: Build failed"
                assert result[
                    "container_starts"
                ], f"{template_name}: Container failed to start"
                assert result[
                    "health_check_passes"
                ], f"{template_name}: Health check failed"

        # Print summary
        print("\n" + "=" * 50)
        print("Template Test Summary:")
        print("=" * 50)

        for template_name, result in results.items():
            status = "✅" if not result["errors"] else "❌"
            print(f"{status} {template_name}")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"   - {error}")

        print("=" * 50)


class TestProductionTemplates:
    """Specific tests for production-ready templates."""

    PRODUCTION_TEMPLATES = ["file-server"]

    @pytest.mark.parametrize("template_name", PRODUCTION_TEMPLATES)
    def test_production_template_comprehensive(self, template_name):
        """Run comprehensive tests on production templates."""
        result = run_template_tests(template_name)

        # All checks must pass for production templates
        assert result["structure_valid"], "Structure validation must pass"
        assert result["build_successful"], "Build must succeed"
        assert result["container_starts"], "Container must start"
        assert result["health_check_passes"], "Health check must pass"
        assert not result["errors"], f"No errors allowed: {result['errors']}"


class TestTemplateMetadata:
    """Test template metadata and configuration schemas."""

    def test_all_templates_have_valid_json(self):
        """Test that all template.json files are valid JSON."""
        import json

        for template_name in get_template_list():
            template_dir = Path(__file__).parent.parent / "templates" / template_name
            template_json_path = template_dir / "template.json"

            if template_json_path.exists():
                try:
                    with open(template_json_path, encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {template_name}/template.json: {e}")

    def test_all_templates_have_docker_images(self):
        """Test that all templates specify Docker images."""
        import json

        for template_name in get_template_list():
            template_dir = Path(__file__).parent.parent / "templates" / template_name
            template_json_path = template_dir / "template.json"

            if template_json_path.exists():
                with open(template_json_path, encoding="utf-8") as f:
                    template_data = json.load(f)

                assert (
                    "docker_image" in template_data
                ), f"{template_name}: Missing docker_image"
                assert template_data["docker_image"].startswith(
                    "dataeverything/"
                ), f"{template_name}: Docker image should use dataeverything registry"


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])
