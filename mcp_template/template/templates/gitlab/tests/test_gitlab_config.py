"""
Unit tests for GitLab template configuration and validation.

Tests the GitLab template's configuration schema and validation
without requiring complex template management infrastructure.
"""

import json


class TestGitLabTemplateConfiguration:
    """Test GitLab template configuration validation and processing."""

    def test_template_json_structure(self):
        """Test GitLab template.json has required structure."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        # Verify required template fields
        assert template_config["name"] == "GitLab MCP Server"
        assert template_config["description"]
        assert template_config["version"]
        assert template_config["docker_image"] == "dataeverything/mcp-gitlab"
        assert template_config["has_image"] is True
        assert template_config["origin"] == "internal"

        # Verify supported transports
        assert "stdio" in template_config["transport"]["supported"]
        assert "sse" in template_config["transport"]["supported"]
        assert "streamable-http" in template_config["transport"]["supported"]
        assert "http" in template_config["transport"]["supported"]

        # Verify configuration schema
        config_schema = template_config["config_schema"]
        assert "gitlab_personal_access_token" in config_schema["required"]
        assert (
            config_schema["properties"]["gitlab_personal_access_token"]["env_mapping"]
            == "GITLAB_PERSONAL_ACCESS_TOKEN"
        )

    def test_minimal_valid_configuration_schema(self):
        """Test minimal valid GitLab configuration schema."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        config_schema = template_config["config_schema"]
        properties = config_schema["properties"]

        # Required field
        assert "gitlab_personal_access_token" in properties
        assert (
            properties["gitlab_personal_access_token"]["env_mapping"]
            == "GITLAB_PERSONAL_ACCESS_TOKEN"
        )

        # Optional fields with defaults
        assert "gitlab_api_url" in properties
        assert properties["gitlab_api_url"]["default"] == "https://gitlab.com/api/v4"
        assert properties["gitlab_api_url"]["env_mapping"] == "GITLAB_API_URL"

        assert "gitlab_read_only_mode" in properties
        assert properties["gitlab_read_only_mode"]["default"] is False
        assert (
            properties["gitlab_read_only_mode"]["env_mapping"]
            == "GITLAB_READ_ONLY_MODE"
        )

    def test_feature_toggle_configuration_schema(self):
        """Test feature toggle configuration options in schema."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        config_schema = template_config["config_schema"]
        properties = config_schema["properties"]

        # Feature toggles
        feature_toggles = [
            ("use_gitlab_wiki", "USE_GITLAB_WIKI"),
            ("use_milestone", "USE_MILESTONE"),
            ("use_pipeline", "USE_PIPELINE"),
        ]

        for config_key, env_key in feature_toggles:
            assert config_key in properties
            assert properties[config_key]["type"] == "boolean"
            assert properties[config_key]["default"] is False
            assert properties[config_key]["env_mapping"] == env_key

    def test_transport_configuration_schema(self):
        """Test transport protocol configuration options in schema."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        config_schema = template_config["config_schema"]
        properties = config_schema["properties"]

        # Transport options
        transport_options = [("sse", "SSE"), ("streamable_http", "STREAMABLE_HTTP")]

        for config_key, env_key in transport_options:
            assert config_key in properties
            assert properties[config_key]["type"] == "boolean"
            assert properties[config_key]["default"] is False
            assert properties[config_key]["env_mapping"] == env_key

    def test_enterprise_configuration_schema(self):
        """Test enterprise configuration options in schema."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        config_schema = template_config["config_schema"]
        properties = config_schema["properties"]

        # Enterprise options
        enterprise_options = [
            ("gitlab_auth_cookie_path", "GITLAB_AUTH_COOKIE_PATH"),
            ("http_proxy", "HTTP_PROXY"),
            ("https_proxy", "HTTPS_PROXY"),
        ]

        for config_key, env_key in enterprise_options:
            assert config_key in properties
            assert properties[config_key]["type"] == "string"
            assert properties[config_key]["env_mapping"] == env_key

    def test_configuration_completeness(self):
        """Test that all documented configuration options are present."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        config_schema = template_config["config_schema"]
        properties = config_schema["properties"]

        # All expected properties
        expected_properties = [
            "gitlab_personal_access_token",
            "gitlab_api_url",
            "gitlab_project_id",
            "gitlab_read_only_mode",
            "use_gitlab_wiki",
            "use_milestone",
            "use_pipeline",
            "gitlab_auth_cookie_path",
            "sse",
            "streamable_http",
            "http_proxy",
            "https_proxy",
        ]

        for prop in expected_properties:
            assert prop in properties, f"Property {prop} missing from schema"
            assert (
                "env_mapping" in properties[prop]
            ), f"Environment mapping missing for {prop}"

        # Verify required fields
        assert "gitlab_personal_access_token" in config_schema["required"]
        assert len(config_schema["required"]) == 1  # Only token is required

    def test_capability_examples(self):
        """Test that template includes capability examples."""
        import os

        template_path = os.path.join(os.path.dirname(__file__), "..", "template.json")

        with open(template_path, "r") as f:
            template_config = json.load(f)

        capabilities = template_config["capabilities"]
        assert len(capabilities) >= 3  # Should have multiple examples

        # Check first capability has required fields
        first_cap = capabilities[0]
        assert "name" in first_cap
        assert "description" in first_cap
        assert "example" in first_cap
        assert "example_args" in first_cap
        assert "example_response" in first_cap

        # Verify capability names match expected GitLab operations
        cap_names = [cap["name"] for cap in capabilities]
        expected_capabilities = [
            "create_or_update_file",
            "search_repositories",
            "create_issue",
        ]

        for expected in expected_capabilities:
            assert expected in cap_names
