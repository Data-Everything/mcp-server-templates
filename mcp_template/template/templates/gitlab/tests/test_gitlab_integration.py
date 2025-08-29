"""
Integration tests for GitLab MCP server template.

These tests verify the GitLab template structure and basic functionality
without requiring full deployment infrastructure.
"""

import json
from pathlib import Path

import pytest


class TestGitLabTemplate:
    """Test GitLab MCP server template structure and configuration."""

    @pytest.fixture
    def template_dir(self) -> Path:
        """Get GitLab template directory."""
        return Path(__file__).parent.parent

    def test_template_structure(self, template_dir):
        """Test GitLab template has required files and structure."""
        # Required files
        required_files = ["template.json", "README.md", "USAGE.md", "docs/index.md"]

        for file_path in required_files:
            assert (
                template_dir / file_path
            ).exists(), f"Missing required file: {file_path}"

        # Required directories
        required_dirs = ["docs", "tests"]

        for dir_path in required_dirs:
            assert (
                template_dir / dir_path
            ).is_dir(), f"Missing required directory: {dir_path}"

    def test_template_json_validity(self, template_dir):
        """Test template.json is valid JSON with required fields."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        # Required top-level fields
        required_fields = [
            "name",
            "description",
            "version",
            "author",
            "category",
            "docker_image",
            "docker_tag",
            "transport",
            "capabilities",
            "config_schema",
            "tool_discovery",
            "has_image",
            "origin",
        ]

        for field in required_fields:
            assert field in config, f"Missing required field: {field}"

        # Verify GitLab-specific values
        assert config["name"] == "GitLab MCP Server"
        assert config["docker_image"] == "dataeverything/mcp-gitlab"
        assert config["has_image"] is True
        assert config["origin"] == "internal"
        assert config["tool_discovery"] == "dynamic"

    def test_configuration_schema_structure(self, template_dir):
        """Test configuration schema has proper structure."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        schema = config["config_schema"]

        # Schema structure
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert schema["type"] == "object"

        # Required properties
        assert "gitlab_personal_access_token" in schema["required"]

        # Verify all properties have env_mapping
        for prop_name, prop_config in schema["properties"].items():
            assert "env_mapping" in prop_config, f"Missing env_mapping for {prop_name}"
            assert "type" in prop_config, f"Missing type for {prop_name}"

    def test_transport_configuration(self, template_dir):
        """Test transport configuration is properly defined."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        transport = config["transport"]

        assert "default" in transport
        assert "supported" in transport
        assert transport["default"] == "stdio"

        # GitLab supports multiple transports
        supported = transport["supported"]
        assert "stdio" in supported
        assert "sse" in supported
        assert "streamable-http" in supported

    def test_capabilities_examples(self, template_dir):
        """Test capabilities include proper examples."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        capabilities = config["capabilities"]
        assert len(capabilities) >= 3

        # Each capability should have required fields
        for cap in capabilities:
            assert "name" in cap
            assert "description" in cap
            assert "example" in cap
            assert "example_args" in cap
            assert "example_response" in cap

        # Verify GitLab-specific capabilities
        cap_names = [cap["name"] for cap in capabilities]
        expected_caps = ["create_or_update_file", "search_repositories", "create_issue"]

        for expected in expected_caps:
            assert expected in cap_names

    def test_documentation_completeness(self, template_dir):
        """Test documentation files are complete and well-formed."""
        # README.md
        readme = template_dir / "README.md"
        readme_content = readme.read_text()

        assert "GitLab MCP Server Template" in readme_content
        assert "Configuration" in readme_content
        assert "Quick Start" in readme_content

        # USAGE.md
        usage = template_dir / "USAGE.md"
        usage_content = usage.read_text()

        assert "GitLab MCP Server Usage Guide" in usage_content
        assert "Setup Scenarios" in usage_content
        assert "Common Operations" in usage_content

        # docs/index.md
        docs = template_dir / "docs" / "index.md"
        docs_content = docs.read_text()

        assert "Complete Tool Reference" in docs_content
        assert "66+ Tools" in docs_content or "Tool Catalog" in docs_content

    def test_feature_toggles_documented(self, template_dir):
        """Test feature toggles are properly documented."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        properties = config["config_schema"]["properties"]

        # Feature toggle properties
        feature_toggles = [
            "use_gitlab_wiki",
            "use_milestone",
            "use_pipeline",
            "gitlab_read_only_mode",
        ]

        for toggle in feature_toggles:
            assert toggle in properties
            assert properties[toggle]["type"] == "boolean"
            assert "description" in properties[toggle]

    def test_environment_variable_mapping(self, template_dir):
        """Test environment variable mappings are consistent."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        properties = config["config_schema"]["properties"]

        # Expected mappings
        expected_mappings = {
            "gitlab_personal_access_token": "GITLAB_PERSONAL_ACCESS_TOKEN",
            "gitlab_api_url": "GITLAB_API_URL",
            "gitlab_read_only_mode": "GITLAB_READ_ONLY_MODE",
            "use_gitlab_wiki": "USE_GITLAB_WIKI",
            "use_milestone": "USE_MILESTONE",
            "use_pipeline": "USE_PIPELINE",
            "sse": "SSE",
            "streamable_http": "STREAMABLE_HTTP",
        }

        for config_key, env_var in expected_mappings.items():
            assert config_key in properties
            assert properties[config_key]["env_mapping"] == env_var

    def test_docker_configuration(self, template_dir):
        """Test Docker configuration is properly defined."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        # Docker configuration
        assert config["docker_image"] == "dataeverything/mcp-gitlab"
        assert config["docker_tag"] == "latest"
        assert config["has_image"] is True
        assert isinstance(config["ports"], dict)  # May be empty
        assert isinstance(config["command"], list)  # May be empty

    def test_category_and_tags(self, template_dir):
        """Test template category and tags are appropriate."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        assert config["category"] == "Development"

        tags = config["tags"]
        expected_tags = ["gitlab", "version-control", "development"]
        for tag in expected_tags:
            assert tag in tags

    def test_template_version_format(self, template_dir):
        """Test template version follows semantic versioning."""
        template_json = template_dir / "template.json"

        with open(template_json, "r") as f:
            config = json.load(f)

        version = config["version"]

        # Should be semantic version (x.y.z)
        import re

        semver_pattern = r"^\d+\.\d+\.\d+.*$"
        assert re.match(semver_pattern, version), f"Invalid version format: {version}"

    def test_readme_sections(self, template_dir):
        """Test README includes all required sections."""
        readme = template_dir / "README.md"
        content = readme.read_text()

        required_sections = [
            "# GitLab MCP Server Template",
            "## Overview",
            "## Key Features",
            "## Quick Start",
            "## Configuration Options",
            "## Transport Modes",
            "## Tool Categories",
        ]

        for section in required_sections:
            assert section in content, f"Missing README section: {section}"
