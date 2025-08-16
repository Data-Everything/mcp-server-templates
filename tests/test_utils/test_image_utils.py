"""
Unit tests for image utility functions.
"""

import os
import unittest
from unittest.mock import patch

from mcp_template.utils.image_utils import (
    get_default_registry,
    get_image_registry,
    is_local_image,
    normalize_image_name,
)


class TestImageUtils(unittest.TestCase):
    """Test image utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Save original environment
        self.original_registry = os.environ.get("MCP_DEFAULT_REGISTRY")

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment
        if self.original_registry is not None:
            os.environ["MCP_DEFAULT_REGISTRY"] = self.original_registry
        elif "MCP_DEFAULT_REGISTRY" in os.environ:
            del os.environ["MCP_DEFAULT_REGISTRY"]

    def test_get_default_registry_default(self):
        """Test get_default_registry returns docker.io by default."""
        # Remove env var if set
        if "MCP_DEFAULT_REGISTRY" in os.environ:
            del os.environ["MCP_DEFAULT_REGISTRY"]

        result = get_default_registry()
        self.assertEqual(result, "docker.io")

    def test_get_default_registry_from_env(self):
        """Test get_default_registry returns value from environment."""
        test_registry = "myregistry.com"
        os.environ["MCP_DEFAULT_REGISTRY"] = test_registry

        result = get_default_registry()
        self.assertEqual(result, test_registry)

    def test_normalize_image_name_simple(self):
        """Test normalizing simple image names."""
        test_cases = [
            ("nginx", "docker.io/nginx"),
            ("ubuntu", "docker.io/ubuntu"),
            ("python", "docker.io/python"),
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = normalize_image_name(input_image)
                self.assertEqual(result, expected)

    def test_normalize_image_name_with_tag(self):
        """Test normalizing image names with tags."""
        test_cases = [
            ("nginx:latest", "docker.io/nginx:latest"),
            ("ubuntu:20.04", "docker.io/ubuntu:20.04"),
            ("python:3.9", "docker.io/python:3.9"),
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = normalize_image_name(input_image)
                self.assertEqual(result, expected)

    def test_normalize_image_name_already_has_registry(self):
        """Test normalizing image names that already have registry."""
        test_cases = [
            ("docker.io/nginx", "docker.io/nginx"),
            ("gcr.io/project/image", "gcr.io/project/image"),
            ("myregistry.com:5000/image", "myregistry.com:5000/image"),
            (
                "registry.example.com/namespace/image:tag",
                "registry.example.com/namespace/image:tag",
            ),
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = normalize_image_name(input_image)
                self.assertEqual(result, expected)

    def test_normalize_image_name_localhost(self):
        """Test normalizing localhost images (should not add registry)."""
        test_cases = [
            ("localhost/myimage", "localhost/myimage"),
            ("localhost:5000/myimage", "localhost:5000/myimage"),
            ("localhost/myimage:latest", "localhost/myimage:latest"),
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = normalize_image_name(input_image)
                self.assertEqual(result, expected)

    def test_normalize_image_name_custom_registry(self):
        """Test normalizing with custom registry parameter."""
        test_cases = [
            ("nginx", "myregistry.com", "myregistry.com/nginx"),
            ("ubuntu:20.04", "private.registry", "private.registry/ubuntu:20.04"),
        ]

        for input_image, registry, expected in test_cases:
            with self.subTest(input_image=input_image, registry=registry):
                result = normalize_image_name(input_image, registry)
                self.assertEqual(result, expected)

    def test_normalize_image_name_empty(self):
        """Test normalizing empty image name."""
        result = normalize_image_name("")
        self.assertEqual(result, "")

    def test_get_image_registry(self):
        """Test extracting registry from image names."""
        test_cases = [
            ("docker.io/nginx", "docker.io"),
            ("gcr.io/project/image", "gcr.io"),
            ("myregistry.com:5000/image", "myregistry.com:5000"),
            ("nginx", None),
            ("ubuntu:latest", None),
            ("library/nginx", None),  # Docker Hub library namespace
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = get_image_registry(input_image)
                self.assertEqual(result, expected)

    def test_is_local_image(self):
        """Test identifying local images."""
        test_cases = [
            ("nginx", True),  # Simple name
            ("ubuntu:latest", True),  # Simple name with tag
            ("localhost/myimage", True),  # Localhost registry
            ("localhost:5000/myimage", True),  # Localhost with port
            ("library/nginx", True),  # Docker Hub library (no dots)
            ("docker.io/nginx", False),  # Remote registry
            ("gcr.io/project/image", False),  # Remote registry
            ("myregistry.com/image", False),  # Custom remote registry
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = is_local_image(input_image)
                self.assertEqual(result, expected)

    def test_normalize_image_name_with_namespace(self):
        """Test normalizing image names with namespaces."""
        test_cases = [
            ("library/nginx", "docker.io/library/nginx"),
            ("dataeverything/mcp-demo", "docker.io/dataeverything/mcp-demo"),
            ("user/repo:tag", "docker.io/user/repo:tag"),
        ]

        for input_image, expected in test_cases:
            with self.subTest(input_image=input_image):
                result = normalize_image_name(input_image)
                self.assertEqual(result, expected)

    @patch.dict(os.environ, {"MCP_DEFAULT_REGISTRY": "custom.registry.com"})
    def test_normalize_with_custom_default_registry(self):
        """Test normalizing with custom default registry from environment."""
        result = normalize_image_name("nginx")
        self.assertEqual(result, "custom.registry.com/nginx")


if __name__ == "__main__":
    unittest.main()
