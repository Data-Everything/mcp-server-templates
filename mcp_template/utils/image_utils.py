"""
Image utility functions for handling registry prefixes and image references.
"""

import os
from typing import Optional


def get_default_registry() -> str:
    """Get the default container registry.

    Returns the value of MCP_DEFAULT_REGISTRY environment variable,
    or 'docker.io' if not set.
    """
    registry = os.getenv("MCP_DEFAULT_REGISTRY", "docker.io")
    # Handle empty string case
    return registry if registry else "docker.io"


def normalize_image_name(image_name: str, registry: Optional[str] = None) -> str:
    """Normalize an image name by adding registry prefix if needed.

    Args:
        image_name: The image name to normalize
        registry: Optional registry to use. If None, uses get_default_registry()

    Returns:
        Normalized image name with registry prefix

    Examples:
        normalize_image_name("nginx") -> "docker.io/nginx"
        normalize_image_name("docker.io/nginx") -> "docker.io/nginx" (unchanged)
        normalize_image_name("gcr.io/project/image") -> "gcr.io/project/image" (unchanged)
        normalize_image_name("nginx", "myregistry.com") -> "myregistry.com/nginx"
    """
    if not image_name:
        return image_name

    # If image already has a registry (contains a dot before the first slash)
    if "/" in image_name:
        first_part = image_name.split("/")[0]
        if "." in first_part or ":" in first_part:
            # Already has registry or port
            return image_name

    # If image starts with localhost, don't add registry
    if image_name.startswith("localhost"):
        return image_name

    # Add registry prefix
    if registry is None:
        registry = get_default_registry()

    return f"{registry}/{image_name}"
