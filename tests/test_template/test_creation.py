#!/usr/bin/env python3
"""
Comprehensive tests for mcp_template.template.creation.TemplateCreator.create_template module.
"""

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from mcp_template.template.creation import TEMPLATES_DIR, TESTS_DIR, TemplateCreator


class TestTemplateCreator(unittest.TestCase):
    """Test the TemplateCreator class."""

    def setup_method(self, method):
        """Set up test fixtures before each test method."""

        self.creator = TemplateCreator()

    def test_init_default_paths(self):
        """Test TemplateCreator initialization with default paths."""

        creator = TemplateCreator()

        # Check that default paths are set
        assert creator.templates_dir.name == "templates"
        assert creator.tests_dir.name == "tests"
        assert creator.template_data == {}
        assert creator.template_dir is None

    def test_init_custom_paths(self):
        """Test TemplateCreator initialization with custom paths."""

        custom_templates = Path("/custom/templates")
        custom_tests = Path("/custom/tests")

        creator = TemplateCreator(
            templates_dir=custom_templates, tests_dir=custom_tests
        )

        assert creator.templates_dir == custom_templates
        assert creator.tests_dir == custom_tests

    def test_create_template_without_data_raises_error(self):
        """Test that create_template raises error when no template_data is set."""
        with pytest.raises(ValueError, match="No template data provided"):
            self.creator.create_template()

    def test_create_template_without_id_raises_error(self):
        """Test that create_template raises error when template_data has no ID."""
        self.creator.template_data = {"name": "Test Template"}

        with pytest.raises(ValueError, match="Template ID is required"):
            self.creator.create_template()

    @patch.object(Path, "mkdir")
    @patch.object(Path, "exists", return_value=False)
    def test_create_template_success(self, mock_exists, mock_mkdir):
        """Test successful template creation."""
        self.creator.template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template",
            "author": "Test Author",
            "version": "1.0.0",
        }

        with patch.object(
            self.creator, "_create_template_structure", return_value=True
        ) as mock_create:
            result = self.creator.create_template()

            assert result is True
            assert self.creator.template_dir.name == "test-template"
            mock_create.assert_called_once()

    @patch("mcp_template.template.creation.console")
    def test_prompt_template_id_valid(self, mock_console):
        """Test prompting for template ID with valid input."""

        with patch("mcp_template.template.creation.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "valid-template-id"

            creator = TemplateCreator()
            result = creator._prompt_template_id()

            assert result == "valid-template-id"

    @patch("mcp_template.template.creation.console")
    def test_prompt_template_id_invalid_then_valid(self, mock_console):
        """Test prompting for template ID with invalid input first, then valid."""

        with patch("mcp_template.template.creation.Prompt") as mock_prompt:
            # First return invalid, then valid
            mock_prompt.ask.side_effect = ["Invalid Template!", "valid-template-id"]

            creator = TemplateCreator()
            result = creator._prompt_template_id()

            assert result == "valid-template-id"
            # Should have been called twice due to invalid input
            assert mock_prompt.ask.call_count == 2

    def test_validate_template_id_valid(self):
        """Test template ID validation with valid inputs."""
        # Valid IDs (lowercase, numbers, hyphens, length >= 2)
        valid_ids = [
            "hello-world",
            "simple-server",
            "server123",
            "my-mcp-server",
            "test123",
            "123numbers-first",  # numbers and letters with hyphens
            "ab",  # minimum length
        ]

        for template_id in valid_ids:
            with self.subTest(template_id=template_id):
                assert self.creator._validate_template_id(template_id) is True

    def test_validate_template_id_invalid(self):
        """Test template ID validation with invalid inputs."""
        # Invalid IDs
        invalid_ids = [
            "CamelCase",  # uppercase not allowed
            "under_scores",  # underscores not allowed
            "with spaces",  # spaces not allowed
            "with.dots",  # dots not allowed
            "a",  # too short (< 2 chars)
            "",  # empty
            "special@chars",  # special chars not allowed
        ]

        for template_id in invalid_ids:
            with self.subTest(template_id=template_id):
                result = self.creator._validate_template_id(template_id)
                # Validate the template ID against the expected rules
                assert result is False

    @patch("mcp_template.template.creation.Prompt.ask")
    def test_gather_template_info(self, mock_ask):
        """Test gathering template information from user input."""
        # Set up template_data with id first
        self.creator.template_data = {"id": "test-template"}

        # Mock user inputs
        mock_ask.side_effect = [
            "Test Template Name",  # name
            "A comprehensive test template",  # description
            "1.0.0",  # version
            "Test Author",  # author
            "dataeverything/mcp-test-template",  # docker_image
        ]

        self.creator._gather_template_info()

        # Verify the structure matches what the method actually creates
        expected_data = {
            "id": "test-template",
            "name": "Test Template Name",
            "description": "A comprehensive test template",
            "version": "1.0.0",
            "author": "Test Author",
            "docker_image": "dataeverything/mcp-test-template",
            "capabilities": [
                {
                    "name": "hello",
                    "description": "A simple hello world tool",
                    "example": "Say hello to the world",
                    "example_args": {},
                    "example_response": "Hello from your new MCP server!",
                }
            ],
            "config_schema": {
                "type": "object",
                "properties": {
                    "log_level": {
                        "type": "string",
                        "description": "Logging level (DEBUG, INFO, WARNING, ERROR)",
                        "default": "INFO",
                        "env_mapping": "LOG_LEVEL",
                    }
                },
                "required": [],
            },
        }

        assert self.creator.template_data == expected_data

    @patch("mcp_template.template.creation.console")
    @patch("mcp_template.template.creation.Confirm")
    def test_confirm_creation_yes(self, mock_confirm, mock_console):
        """Test confirmation dialog when user confirms creation."""
        mock_confirm.ask.return_value = True

        # Set up complete template data with all required fields
        self.creator.template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template",
            "version": "1.0.0",
            "author": "Test Author",
            "docker_image": "test-image",
            "capabilities": [{"name": "test"}],
            "config_schema": {"properties": {"test": True}},
        }

        result = self.creator._confirm_creation()
        assert result is True

    @patch("mcp_template.template.creation.console")
    @patch("mcp_template.template.creation.Confirm")
    def test_confirm_creation_no(self, mock_confirm, mock_console):
        """Test confirmation dialog when user declines creation."""
        mock_confirm.ask.return_value = False

        # Set up complete template data with all required fields
        self.creator.template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template",
            "version": "1.0.0",
            "author": "Test Author",
            "docker_image": "test-image",
            "capabilities": [{"name": "test"}],
            "config_schema": {"properties": {"test": True}},
        }

        result = self.creator._confirm_creation()
        assert result is False

    def test_create_from_config_file_success(self):
        """Test creating template from config file."""
        config_data = {
            "id": "config-template",
            "name": "Config Template",
            "description": "Template from config",
            "author": "Config Author",
            "version": "1.0.0",
        }

        mock_file_content = json.dumps(config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch.object(
                    self.creator, "_create_template_structure", return_value=True
                ):
                    result = self.creator._create_from_config_file("config.json")

                    assert result is True
                    assert self.creator.template_data == config_data

    def test_create_from_config_file_with_template_id_override(self):
        """Test creating template from config file with ID override."""
        config_data = {
            "id": "original-id",
            "name": "Config Template",
            "description": "Template from config",
        }

        mock_file_content = json.dumps(config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch.object(
                    self.creator, "_create_template_structure", return_value=True
                ):
                    result = self.creator._create_from_config_file(
                        "config.json", "override-id"
                    )

                    assert result is True
                    # ID should be overridden
                    assert self.creator.template_data["id"] == "override-id"
                    assert self.creator.template_data["name"] == "Config Template"

    def test_create_from_config_file_invalid_json(self):
        """Test creating template from invalid JSON config file."""
        invalid_json = "{ invalid json }"

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch("mcp_template.template.creation.console") as mock_console:
                result = self.creator._create_from_config_file("config.json")

                assert result is False
                mock_console.print.assert_called()

    def test_create_from_config_file_missing_file(self):
        """Test creating template from missing config file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("mcp_template.template.creation.console") as mock_console:
                result = self.creator._create_from_config_file("missing.json")

                assert result is False
                mock_console.print.assert_called()

    def test_create_dockerfile(self):
        """Test creating Dockerfile."""
        self.creator.template_data = {"id": "test-template", "name": "Test Template"}
        self.creator.template_dir = Path("/tmp/test-template")

        # Create the directory first to avoid FileNotFoundError
        self.creator.template_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.creator._create_dockerfile()

            # Verify the file was created (by checking it exists)
            dockerfile_path = self.creator.template_dir / "Dockerfile"
            assert dockerfile_path.exists()
        finally:
            # Clean up
            if self.creator.template_dir.exists():
                shutil.rmtree(self.creator.template_dir)

    def test_create_requirements_txt(self):
        """Test creating requirements.txt."""
        self.creator.template_dir = Path("/tmp/test-template")

        # Create the directory first to avoid FileNotFoundError
        self.creator.template_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.creator._create_requirements_txt()

            # Verify the file was created
            requirements_path = self.creator.template_dir / "requirements.txt"
            assert requirements_path.exists()
        finally:
            # Clean up
            if self.creator.template_dir.exists():
                shutil.rmtree(self.creator.template_dir)

    def test_create_template_json(self):
        """Test creating template.json."""
        self.creator.template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template",
            "author": "Test Author",
            "version": "1.0.0",
            "docker_image": "test/image",
            "capabilities": [{"name": "test"}],
            "config_schema": {"properties": {}},
        }
        self.creator.template_dir = Path("/tmp/test-template")

        # Create the directory first to avoid FileNotFoundError
        self.creator.template_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.creator._create_template_json()

            # Verify the file was created and contains expected data
            json_path = self.creator.template_dir / "template.json"
            assert json_path.exists()

            with open(json_path, "r") as f:
                template_config = json.load(f)
                assert template_config["name"] == "Test Template"
                assert template_config["description"] == "A test template"
        finally:
            # Clean up
            if self.creator.template_dir.exists():
                shutil.rmtree(self.creator.template_dir)


class TestTemplateCreatorUtilityFunctions:
    """Test utility functions in the create_template module."""

    def test_constants_are_defined(self):
        """Test that module constants are properly defined."""

        assert isinstance(TEMPLATES_DIR, Path)
        assert isinstance(TESTS_DIR, Path)

        assert TEMPLATES_DIR.name == "templates"
        assert TESTS_DIR.name == "tests"
