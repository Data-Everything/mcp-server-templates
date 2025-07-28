# Test all templates in the repository

import json
from pathlib import Path

import pytest

# Add src to Python path for testing
from mcp_template.template.discovery import TemplateDiscovery
from mcp_template.utils import TEMPLATES_DIR
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
            validated = validate_template_structure(template_name)
            assert validated, f"Template {template_name} structure validation failed"

    @pytest.mark.slow
    def test_all_templates_build_successfully(self, template_list):
        """Test that all templates can be built."""
        results = {}

        for template_name in template_list:
            print(f"\nTesting template: {template_name}")
            result = run_template_tests(template_name)
            results[template_name] = result

            # Assert basic requirements - for CompletedProcess, check returncode
            assert (
                result.returncode == 0
            ), f"{template_name}: Template tests failed with return code {result.returncode}. Output: {result.stdout} {result.stderr}"

            # Check if stdout contains success indicators
            output = result.stdout + result.stderr
            if "FAILED" in output:
                print(f"Test failures for {template_name}: Found FAILED in output")

        # Print summary
        print("\n" + "=" * 50)
        print("Template Test Summary:")
        print("=" * 50)

        for template_name, result in results.items():
            status = "✅" if result.returncode == 0 else "❌"
            print(f"{status} {template_name}")
            if result.returncode != 0:
                print(f"   - Return code: {result.returncode}")
                if result.stderr:
                    print(f"   - Error: {result.stderr}")

        print("=" * 50)


class TestProductionTemplates:
    """Specific tests for production-ready templates."""

    def _get_production_templates(self):
        """Discover production templates dynamically."""

        # Use TemplateDiscovery to find all templates
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        production_templates = []
        for template_name, template_data in templates.items():
            # Identify production templates by checking metadata
            if self._is_production_template(template_name, template_data):
                production_templates.append(template_name)

        return production_templates

    def _is_production_template(self, template_name: str, template_data: dict) -> bool:
        """Determine if a template is production-ready."""
        # Production templates should have:
        # 1. Complete metadata
        # 2. Tests directory
        # 3. Docker configuration

        required_fields = ["name", "description", "docker_image", "version"]
        has_required_fields = all(field in template_data for field in required_fields)

        # Check if template has tests
        template_dir = TEMPLATES_DIR / template_name
        has_tests = (template_dir / "tests").exists()

        # For now, consider templates with tests as production-ready
        return has_required_fields and has_tests

    def test_production_templates_discovered(self):
        """Test that we can discover production templates."""

        production_templates = self._get_production_templates()
        assert (
            len(production_templates) > 0
        ), "Should discover at least one production template"
        print(f"Discovered production templates: {production_templates}")

    def test_production_template_comprehensive(self):
        """Run comprehensive tests on all production templates."""
        production_templates = self._get_production_templates()

        for template_name in production_templates:
            print(f"Testing production template: {template_name}")
            result = run_template_tests(template_name)

            # Check that tests pass (return code 0 means success)
            assert (
                result.returncode == 0
            ), f"Template tests failed for {template_name}. Output: {result.stdout} {result.stderr}"


class TestTemplateMetadata:
    """Test template metadata and configuration schemas."""

    def test_all_templates_have_valid_json(self):
        """Test that all template.json files are valid JSON."""

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

        for template_name in get_template_list():
            template_dir = Path(__file__).parent.parent / "templates" / template_name
            template_json_path = template_dir / "template.json"

            if template_json_path.exists():
                with open(template_json_path, encoding="utf-8") as f:
                    template_data = json.load(f)

                assert (
                    "docker_image" in template_data
                ), f"{template_name}: Missing docker_image"
                # Allow any valid docker image format for flexibility
                assert template_data[
                    "docker_image"
                ], f"{template_name}: docker_image cannot be empty"


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])
